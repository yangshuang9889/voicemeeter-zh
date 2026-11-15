# -*- coding: utf-8 -*-
"""硬件断点监视：谁读取了某个字符串常量。"""
import ctypes, struct, sys, os
from ctypes import wintypes as wt

k32 = ctypes.windll.kernel32
psapi = ctypes.windll.psapi
DWORD = ctypes.c_uint32
U_OFF = 16
SINGLE_STEP = 0x80000004
BREAKPOINT = 0x80000003

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

def mainmod_base(pid, hproc):
    ntdll = ctypes.windll.ntdll
    class PBI(ctypes.Structure):
        _fields_ = [("ExitStatus", ctypes.c_long), ("PebBaseAddress", ctypes.c_void_p),
                    ("AffinityMask", ctypes.c_void_p), ("BasePriority", ctypes.c_long),
                    ("UniqueProcessId", ctypes.c_void_p), ("InheritedFromUniqueProcessId", ctypes.c_void_p)]
    pbi = PBI()
    ret = ctypes.c_ulong(0)
    ntdll.NtQueryInformationProcess(ctypes.c_void_p(hproc), 0, ctypes.byref(pbi),
                                    ctypes.sizeof(pbi), ctypes.byref(ret))
    if not pbi.PebBaseAddress:
        return None
    buf = ctypes.c_ulonglong(0)
    n = ctypes.c_size_t(0)
    ok = k32.ReadProcessMemory(ctypes.c_void_p(hproc),
                               ctypes.c_void_p(pbi.PebBaseAddress + 0x10),
                               ctypes.byref(buf), 8, ctypes.byref(n))
    return buf.value if ok else None

def set_hwbp(tid, addr):
    h = k32.OpenThread(0x0008 | 0x0010 | 0x0040, False, tid)
    if not h: return False
    ctx = ctypes.create_string_buffer(0x4D0 + 16)
    struct.pack_into('<I', ctx, 0x30, 0x0010001B)  # FULL | DEBUG_REGISTERS
    if not k32.GetThreadContext(h, ctx):
        k32.CloseHandle(h); return False
    struct.pack_into('<Q', ctx, 0x48, addr)       # Dr0
    struct.pack_into('<Q', ctx, 0x70, 0x000F0001) # L0 + R/W0=11(rdwr) len=1
    ok = k32.SetThreadContext(h, ctx)
    k32.CloseHandle(h)
    return bool(ok)

def clear_hwbp(tid):
    h = k32.OpenThread(0x0008 | 0x0010 | 0x0040, False, tid)
    if not h: return
    ctx = ctypes.create_string_buffer(0x4D0 + 16)
    struct.pack_into('<I', ctx, 0x30, 0x0010001B)
    if k32.GetThreadContext(h, ctx):
        struct.pack_into('<Q', ctx, 0x70, 0)
        struct.pack_into('<Q', ctx, 0x48, 0)
        k32.SetThreadContext(h, ctx)
    k32.CloseHandle(h)

def run(exe, str_rva, maxhit=12):
    pi = PROCESS_INFORMATION()
    si = STARTUPINFO(); si.cb = ctypes.sizeof(si)
    cmd = ctypes.create_unicode_buffer('"%s"' % exe)
    k32.SetErrorMode(0x0001 | 0x0002 | 0x8000)
    if not k32.CreateProcessW(None, cmd, None, None, False, 0x00000002, None,
                              os.path.dirname(exe), ctypes.byref(si), ctypes.byref(pi)):
        print("CreateProcess failed", k32.GetLastError()); return
    print("pid", pi.dwProcessId)
    base = None
    armed = False
    hits = 0
    ev = DEBUG_EVENT()
    while True:
        if not k32.WaitForDebugEvent(ctypes.byref(ev), int(os.environ.get("DBGWAIT", "20000"))):
            print("timeout"); break
        raw = bytes(ev.raw)
        code, pid, tid = struct.unpack_from('<III', raw, 0)
        cont = 0x00010002
        if code == 3:  # CREATE_PROCESS
            if base is None:
                base = mainmod_base(pid, pi.hProcess)
                print("主模块基址 =", hex(base or 0))
                if base:
                    armed = set_hwbp(tid, base + str_rva)
                    print("设断点 @", hex(base+str_rva), "->", armed)
                    buf = ctypes.create_string_buffer(64); n = ctypes.c_size_t(0)
                    if k32.ReadProcessMemory(ctypes.c_void_p(pi.hProcess),
                                             ctypes.c_void_p(base+str_rva), buf, 48, ctypes.byref(n)):
                        print("   内存内容:", bytes(buf.raw[:48]))
                    else:
                        print("   读取失败", k32.GetLastError())
        if code == 1:
            ecode = struct.unpack_from('<I', raw, U_OFF)[0]
            first = struct.unpack_from('<I', raw, U_OFF+152)[0]
            if ecode == BREAKPOINT and first:
                if not armed and base:
                    armed = set_hwbp(tid, base + str_rva)
                    print("设断点 @", hex(base+str_rva), "->", armed)
                cont = 0x00010002
            elif ecode == SINGLE_STEP:
                h = k32.OpenThread(0x0008 | 0x0040, False, tid)
                ctx = ctypes.create_string_buffer(0x4D0 + 16)
                struct.pack_into('<I', ctx, 0x30, 0x0010000B)
                if k32.GetThreadContext(h, ctx):
                    regs = {nm: struct.unpack_from('<Q', ctx, off)[0] for nm, off in GPR}
                    rva = regs['Rip'] - base if base else 0
                    print("HIT#%d tid=%d RIP=%s (rva=%s) Rcx=%s Rdx=%s Rsi=%s Rdi=%s"
                          % (hits, tid, hex(regs['Rip']), hex(rva), hex(regs['Rcx']),
                             hex(regs['Rdx']), hex(regs['Rsi']), hex(regs['Rdi'])))
                k32.CloseHandle(h)
                hits += 1
                if hits >= maxhit:
                    clear_hwbp(tid); armed = False
                cont = 0x00010002
            else:
                print("EXC 0x%08X @ %s base=%s" % (ecode,
                      hex(struct.unpack_from('<Q', raw, U_OFF+16)[0]), hex(base or 0)))
                cont = 0x80010001
                k32.ContinueDebugEvent(pid, tid, cont)
                break
        if code == 6:  # EXIT_PROCESS
            k32.ContinueDebugEvent(pid, tid, cont); break
        k32.ContinueDebugEvent(pid, tid, cont)
    k32.TerminateProcess(pi.hProcess, 0)
    k32.CloseHandle(pi.hProcess); k32.CloseHandle(pi.hThread)

if __name__ == "__main__":
    run(sys.argv[1], int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x159A00)
