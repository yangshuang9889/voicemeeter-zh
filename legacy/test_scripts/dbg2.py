# -*- coding: utf-8 -*-
"""极简调试器 v2：DEBUG_EVENT 用原始字节解析，抓首次真实异常并回溯栈。"""
import ctypes, struct, sys, os
from ctypes import wintypes as wt

k32 = ctypes.windll.kernel32
DWORD = ctypes.c_uint32

class STARTUPINFO(ctypes.Structure):
    _fields_ = [("cb", DWORD), ("lpReserved", wt.LPWSTR), ("lpDesktop", wt.LPWSTR),
                ("lpTitle", wt.LPWSTR), ("dwX", DWORD), ("dwY", DWORD), ("dwXSize", DWORD),
                ("dwYSize", DWORD), ("dwXCountChars", DWORD), ("dwYCountChars", DWORD),
                ("dwFillAttribute", DWORD), ("dwFlags", DWORD), ("wShowWindow", wt.WORD),
                ("cbReserved2", wt.WORD), ("lpReserved2", ctypes.POINTER(ctypes.c_byte)),
                ("hStdInput", wt.HANDLE), ("hStdOutput", wt.HANDLE), ("hStdError", wt.HANDLE)]

class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [("hProcess", wt.HANDLE), ("hThread", wt.HANDLE),
                ("dwProcessId", DWORD), ("dwThreadId", DWORD)]

DE_SIZE = 12 + 160
class DEBUG_EVENT(ctypes.Structure):
    _fields_ = [("raw", ctypes.c_byte * DE_SIZE)]

def load_pdata(exe):
    b = open(exe, 'rb').read()
    pe = struct.unpack_from('<I', b, 0x3c)[0]
    nsec = struct.unpack_from('<H', b, pe+6)[0]
    optsz = struct.unpack_from('<H', b, pe+20)[0]
    opt = pe+24
    so = opt+optsz
    secs = []
    for i in range(nsec):
        o = so+i*40
        name = b[o:o+8].rstrip(b'\0').decode('latin1')
        vs, va, rs, ra = struct.unpack_from('<IIII', b, o+8)
        secs.append((name, va, vs, ra, rs))
    tbl = []
    txt = None
    for n, va, vs, ra, rs in secs:
        if n == '.pdata':
            for i in range(vs//12):
                beg, end, u = struct.unpack_from('<III', b, ra+i*12)
                if beg:
                    tbl.append((beg, end))
        if n == '.text':
            txt = (va, vs)
    tbl.sort()
    return tbl, txt

def run(exe, maxsec=10):
    pi = PROCESS_INFORMATION()
    si = STARTUPINFO(); si.cb = ctypes.sizeof(si)
    cmd = ctypes.create_unicode_buffer('"%s"' % exe)
    k32.SetErrorMode(0x0001 | 0x0002 | 0x8000)
    if not k32.CreateProcessW(None, cmd, None, None, False, 0x00000002, None,
                              os.path.dirname(exe), ctypes.byref(si), ctypes.byref(pi)):
        print("CreateProcess failed", k32.GetLastError()); return
    print("started pid", pi.dwProcessId)
    pdata, txt = load_pdata(exe)
    base = 0x140000000
    ev = DEBUG_EVENT()
    while True:
        if not k32.WaitForDebugEvent(ctypes.byref(ev), 15000):
            print("timeout waiting debug event"); break
        raw = bytes(ev.raw)
        code, pid, tid = struct.unpack_from('<III', raw, 0)
        if code == 1:
            ecode, eflags = struct.unpack_from('<II', raw, 12)
            eaddr = struct.unpack_from('<Q', raw, 12+16)[0]
            first = struct.unpack_from('<I', raw, 12+152)[0]
            print("EXC code=0x%08X addr=%s first=%d tid=%d" % (ecode, hex(eaddr), first, tid))
            if ecode == 0x80000003 and first:
                k32.ContinueDebugEvent(pid, tid, 0x00010002); continue
            h = k32.OpenThread(0x0008 | 0x0040, False, tid)
            ctx = ctypes.create_string_buffer(0x4D0 + 16)
            struct.pack_into('<I', ctx, 0x30, 0x0010000B)
            okc = k32.GetThreadContext(h, ctx)
            print("  GetThreadContext ok=%d lasterr=%d" % (okc, k32.GetLastError()))
            if okc:
                rip = struct.unpack_from('<Q', ctx, 0xF8)[0]
                rsp = struct.unpack_from('<Q', ctx, 0x98)[0]
                rbp = struct.unpack_from('<Q', ctx, 0xA0)[0]
                print("  RIP=%s RSP=%s RBP=%s" % (hex(rip), hex(rsp), hex(rbp)))
                buf = ctypes.create_string_buffer(0x1000)
                n = ctypes.c_size_t(0)
                if k32.ReadProcessMemory(pi.hProcess, ctypes.c_void_p(rsp), buf,
                                         0x1000, ctypes.byref(n)):
                    seen = []
                    for off in range(0, n.value-8, 8):
                        v = struct.unpack_from('<Q', buf, off)[0]
                        if base <= v < base+0x200000:
                            rva = v-base
                            for beg, end in pdata:
                                if beg <= rva < end:
                                    if beg not in seen:
                                        seen.append(beg)
                                    break
                    print("  栈内函数起点RVA:", [hex(x) for x in seen[:20]])
                else:
                    print("  ReadProcessMemory fail", k32.GetLastError())
            k32.CloseHandle(h)
            k32.ContinueDebugEvent(pid, tid, 0x80010001)
            break
        k32.ContinueDebugEvent(pid, tid, 0x00010002)
    k32.TerminateProcess(pi.hProcess, 0)
    k32.CloseHandle(pi.hProcess); k32.CloseHandle(pi.hThread)

if __name__ == "__main__":
    run(sys.argv[1])
