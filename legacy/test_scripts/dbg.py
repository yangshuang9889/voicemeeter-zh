# -*- coding: utf-8 -*-
"""极简调试器：以 DEBUG_ONLY_THIS_PROCESS 启动目标，抓首次异常并回溯栈。"""
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

class DEBUG_EVENT(ctypes.Structure):
    _fields_ = [("dwDebugEventCode", DWORD), ("dwProcessId", DWORD),
                ("dwThreadId", DWORD), ("u", ctypes.c_byte * 176)]

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
    tbl = {}
    for n, va, vs, ra, rs in secs:
        if n == '.pdata':
            for i in range(vs//12):
                beg, end, u = struct.unpack_from('<III', b, ra+i*12)
                if beg:
                    tbl[beg] = end
    return sorted(tbl.items())

def func_of(rvas):
    """返回覆盖该 rva 的函数起点"""
    for beg, end in rvas:
        if beg <= rvas_target[0] < end:
            return beg

def run(exe):
    pi = PROCESS_INFORMATION()
    si = STARTUPINFO(); si.cb = ctypes.sizeof(si)
    cmd = ctypes.create_unicode_buffer('"%s"' % exe)
    k32.SetErrorMode(0x0001 | 0x0002 | 0x8000)
    ok = k32.CreateProcessW(None, cmd, None, None, False,
                            0x00000002, None, os.path.dirname(exe),
                            ctypes.byref(si), ctypes.byref(pi))
    if not ok:
        print("CreateProcess failed", k32.GetLastError()); return
    print("started pid", pi.dwProcessId)
    ev = DEBUG_EVENT()
    pdata = load_pdata(exe)
    base = 0x140000000
    hits = 0
    while True:
        if not k32.WaitForDebugEvent(ctypes.byref(ev), 15000):
            print("timeout"); break
        code = ev.dwDebugEventCode
        if code == 1:  # EXCEPTION
            exc = ctypes.cast(ctypes.byref(ev.u), ctypes.POINTER(DWORD))
            ecode = exc[0]
            eaddr = ctypes.cast(ctypes.byref(ev.u, 16), ctypes.POINTER(ctypes.c_void_p))[0]
            first = ctypes.cast(ctypes.byref(ev.u, 152), ctypes.POINTER(DWORD))[0]
            print("EXCEPTION code=0x%08X addr=%s first=%d tid=%d"
                  % (ecode, hex(eaddr or 0), first, ev.dwThreadId))
            if ecode == 0x80000003 and first:   # 初始断点
                k32.ContinueDebugEvent(ev.dwProcessId, ev.dwThreadId, 0x00010002)
                continue
            # 抓上下文
            h = k32.OpenThread(0x0008 | 0x0010, False, ev.dwThreadId)
            ctx = ctypes.create_string_buffer(0x4D0)
            struct.pack_into('<I', ctx, 0x30, 0x0010000B)
            if k32.GetThreadContext(h, ctx):
                rip = struct.unpack_from('<Q', ctx, 0xF8)[0]
                rsp = struct.unpack_from('<Q', ctx, 0x98)[0]
                rbp = struct.unpack_from('<Q', ctx, 0xA0)[0]
                print("  RIP=%s RSP=%s RBP=%s" % (hex(rip), hex(rsp), hex(rbp)))
                buf = ctypes.create_string_buffer(0x800)
                n = ctypes.c_size_t(0)
                if k32.ReadProcessMemory(pi.hProcess, ctypes.c_void_p(rsp), buf, 0x800, ctypes.byref(n)):
                    seen = []
                    for off in range(0, n.value, 8):
                        v = struct.unpack_from('<Q', buf, off)[0]
                        if base <= v < base+0x200000:
                            rva = v-base
                            for beg, end in pdata:
                                if beg <= rva < end:
                                    if beg not in seen:
                                        seen.append(beg)
                                    break
                    print("  栈内函数起点(RVA):", [hex(x) for x in seen[:20]])
                k32.CloseHandle(h)
            hits += 1
            if hits >= 1:
                k32.ContinueDebugEvent(ev.dwProcessId, ev.dwThreadId, 0x80010001)  # not handled
                break
        k32.ContinueDebugEvent(ev.dwProcessId, ev.dwThreadId, 0x00010002)
    k32.TerminateProcess(pi.hProcess, 0)
    k32.CloseHandle(pi.hProcess); k32.CloseHandle(pi.hThread)

if __name__ == "__main__":
    run(sys.argv[1])
