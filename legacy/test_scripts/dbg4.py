# -*- coding: utf-8 -*-
"""调试器 v4：打印全部 GPR，栈扫描范围扩大。"""
import ctypes, struct, sys, os
from ctypes import wintypes as wt

k32 = ctypes.windll.kernel32
DWORD = ctypes.c_uint32
U_OFF = 16

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

DE_SIZE = U_OFF + 160
class DEBUG_EVENT(ctypes.Structure):
    _fields_ = [("raw", ctypes.c_byte * DE_SIZE)]

GPR = [("Rax",0x78),("Rcx",0x80),("Rdx",0x88),("Rbx",0x90),("Rsp",0x98),("Rbp",0xA0),
       ("Rsi",0xA8),("Rdi",0xB0),("R8",0xB8),("R9",0xC0),("R10",0xC8),("R11",0xD0),
       ("R12",0xD8),("R13",0xE0),("R14",0xE8),("R15",0xF0),("Rip",0xF8)]

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
    for n, va, vs, ra, rs in secs:
        if n == '.pdata':
            for i in range(vs//12):
                beg, end, u = struct.unpack_from('<III', b, ra+i*12)
                if beg:
                    tbl.append((beg, end))
    tbl.sort()
    return tbl

def run(exe, fault_rva):
    pi = PROCESS_INFORMATION()
    si = STARTUPINFO(); si.cb = ctypes.sizeof(si)
    cmd = ctypes.create_unicode_buffer('"%s"' % exe)
    k32.SetErrorMode(0x0001 | 0x0002 | 0x8000)
    if not k32.CreateProcessW(None, cmd, None, None, False, 0x00000002, None,
                              os.path.dirname(exe), ctypes.byref(si), ctypes.byref(pi)):
        print("CreateProcess failed", k32.GetLastError()); return
    print("started pid", pi.dwProcessId)
    pdata = load_pdata(exe)
    base = None
    ev = DEBUG_EVENT()
    while True:
        if not k32.WaitForDebugEvent(ctypes.byref(ev), 20000):
            print("timeout"); break
        raw = bytes(ev.raw)
        code, pid, tid = struct.unpack_from('<III', raw, 0)
        if code == 1:
            ecode = struct.unpack_from('<I', raw, U_OFF)[0]
            eaddr = struct.unpack_from('<Q', raw, U_OFF+16)[0]
            first = struct.unpack_from('<I', raw, U_OFF+152)[0]
            if ecode == 0x80000003 and first:
                k32.ContinueDebugEvent(pid, tid, 0x00010002); continue
            if base is None:
                base = eaddr - fault_rva
            print("EXC 0x%08X @ %s  base=%s" % (ecode, hex(eaddr), hex(base)))
            h = k32.OpenThread(0x0008 | 0x0040, False, tid)
            ctx = ctypes.create_string_buffer(0x4D0 + 16)
            struct.pack_into('<I', ctx, 0x30, 0x0010000B)
            okc = k32.GetThreadContext(h, ctx)
            if okc:
                regs = {nm: struct.unpack_from('<Q', ctx, off)[0] for nm, off in GPR}
                for nm, _ in GPR:
                    print("   %-4s = %s" % (nm, hex(regs[nm])))
                rsp = regs['Rsp']
                SZ = 0x10000
                buf = ctypes.create_string_buffer(SZ)
                n = ctypes.c_size_t(0)
                if k32.ReadProcessMemory(pi.hProcess, ctypes.c_void_p(rsp), buf, SZ, ctypes.byref(n)):
                    print("   --- 栈扫描 (RSP+0..0x%x) ---" % n.value)
                    for off in range(0, n.value-8, 8):
                        v = struct.unpack_from('<Q', buf, off)[0]
                        if base <= v < base+0x200000:
                            rva = v-base
                            for beg, end in pdata:
                                if beg <= rva < end:
                                    print("   +0x%05x: %s  (func 0x%x)" % (off, hex(rva), beg))
                                    break
            k32.CloseHandle(h)
            k32.ContinueDebugEvent(pid, tid, 0x80010001)
            break
        k32.ContinueDebugEvent(pid, tid, 0x00010002)
    k32.TerminateProcess(pi.hProcess, 0)
    k32.CloseHandle(pi.hProcess); k32.CloseHandle(pi.hThread)

if __name__ == "__main__":
    run(sys.argv[1], int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x1445f0)
