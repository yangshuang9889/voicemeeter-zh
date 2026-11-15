# -*- coding: utf-8 -*-
"""在运行进程内存里搜索主界面英文串，判定是字符串还是位图。"""
import ctypes, sys
from ctypes import wintypes

pid = int(sys.argv[1]) if len(sys.argv) > 1 else 26496
k32 = ctypes.WinDLL('kernel32', use_last_error=True)
PROCESS_VM_READ = 0x10
PROCESS_QUERY_INFORMATION = 0x400

class MBI(ctypes.Structure):
    _fields_ = [("BaseAddress", ctypes.c_ulonglong), ("AllocationBase", ctypes.c_ulonglong),
                ("AllocationProtect", wintypes.DWORD), ("__a", wintypes.DWORD),
                ("RegionSize", ctypes.c_ulonglong), ("State", wintypes.DWORD),
                ("Protect", wintypes.DWORD), ("Type", wintypes.DWORD), ("__b", wintypes.DWORD)]

h = k32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid)
if not h:
    print("OpenProcess 失败", ctypes.get_last_error()); sys.exit(1)

targets = ["IntelliPan", "MODULATION", "HARDWARE OUT", "MASTER SECTION", "RECORDER", "PHYSICAL", "VIRTUAL"]
needles = []
for t in targets:
    needles.append((t + " [ascii]", t.encode('ascii')))
    needles.append((t + " [utf16]", t.encode('utf-16-le')))

found = {}
addr = 0
MB = 1 << 20
mbi = MBI()
MEM_COMMIT = 0x1000
while addr < 0x7FFFFFFF0000:
    if not k32.VirtualQueryEx(h, ctypes.c_ulonglong(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
        break
    base, size = mbi.BaseAddress, mbi.RegionSize
    if mbi.State == MEM_COMMIT and size < 256 * MB and (mbi.Protect & 0xFF) not in (0x01, 0x00):
        buf = ctypes.create_string_buffer(size)
        got = ctypes.c_size_t(0)
        if k32.ReadProcessMemory(h, ctypes.c_ulonglong(base), buf, ctypes.c_size_t(size), ctypes.byref(got)):
            data = buf.raw[:got.value]
            for name, nd in needles:
                if name in found: continue
                i = data.find(nd)
                if i >= 0:
                    found[name] = base + i
    addr = base + size

k32.CloseHandle(h)
for name, _ in needles:
    print(("命中 " if name in found else "未找到 ") + name + ((" @0x%x" % found[name]) if name in found else ""))
