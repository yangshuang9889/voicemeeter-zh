# -*- coding: utf-8 -*-
"""验证：内存补丁（不改磁盘文件）是否触发崩溃。"""
import ctypes, ctypes.wintypes as wt, subprocess, time, sys, struct

k32 = ctypes.WinDLL('kernel32', use_last_error=True)
ntdll = ctypes.WinDLL('ntdll')

CREATE_SUSPENDED = 0x00000004

class STARTUPINFOA(ctypes.Structure):
    _fields_ = [("cb", wt.DWORD), ("lpReserved", wt.LPSTR), ("lpDesktop", wt.LPSTR),
                ("lpTitle", wt.LPSTR), ("dwX", wt.DWORD), ("dwY", wt.DWORD),
                ("dwXSize", wt.DWORD), ("dwYSize", wt.DWORD),
                ("dwXCountChars", wt.DWORD), ("dwYCountChars", wt.DWORD),
                ("dwFillAttribute", wt.DWORD), ("dwFlags", wt.DWORD),
                ("wShowWindow", wt.WORD), ("cbReserved2", wt.WORD),
                ("lpReserved2", ctypes.c_void_p), ("hStdInput", wt.HANDLE),
                ("hStdOutput", wt.HANDLE), ("hStdError", wt.HANDLE)]

class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [("hProcess", wt.HANDLE), ("hThread", wt.HANDLE),
                ("dwProcessId", wt.DWORD), ("dwThreadId", wt.DWORD)]

class PBI(ctypes.Structure):
    _fields_ = [("ExitStatus", ctypes.c_long), ("PebBaseAddress", ctypes.c_void_p),
                ("AffinityMask", ctypes.c_void_p), ("BasePriority", ctypes.c_long),
                ("UniqueProcessId", ctypes.c_void_p), ("InheritedFromUniqueProcessId", ctypes.c_void_p)]

def image_base(hproc):
    pbi = PBI(); ret = ctypes.c_ulong(0)
    ntdll.NtQueryInformationProcess(ctypes.c_void_p(hproc), 0, ctypes.byref(pbi),
                                    ctypes.sizeof(pbi), ctypes.byref(ret))
    v = ctypes.c_ulonglong(0); n = ctypes.c_size_t(0)
    k32.ReadProcessMemory(ctypes.c_void_p(hproc), ctypes.c_void_p(pbi.PebBaseAddress + 0x10),
                          ctypes.byref(v), 8, ctypes.byref(n))
    return v.value

def run(exe, patch_rva=None, newbyte=None, secs=25, label=""):
    si = STARTUPINFOA(); si.cb = ctypes.sizeof(si)
    pi = PROCESS_INFORMATION()
    ok = k32.CreateProcessA(exe.encode(), None, None, None, False,
                            CREATE_SUSPENDED, None, None, ctypes.byref(si), ctypes.byref(pi))
    if not ok:
        print("CreateProcess 失败", ctypes.get_last_error()); return
    base = image_base(pi.hProcess)
    if patch_rva is not None:
        addr = base + patch_rva
        old = ctypes.create_string_buffer(16); n = ctypes.c_size_t(0)
        k32.ReadProcessMemory(ctypes.c_void_p(pi.hProcess), ctypes.c_void_p(addr), old, 1, ctypes.byref(n))
        newb = bytes([newbyte])
        oldp = wt.DWORD(0)
        p = addr & ~0xFFF
        vp = k32.VirtualProtectEx(ctypes.c_void_p(pi.hProcess), ctypes.c_void_p(p),
                                  ctypes.c_size_t(0x1000), 0x04, ctypes.byref(oldp))
        print("  VirtualProtectEx =", bool(vp), "old=0x%x" % oldp.value)
        w = k32.WriteProcessMemory(ctypes.c_void_p(pi.hProcess), ctypes.c_void_p(addr), newb, 1, ctypes.byref(n))
        print("  内存补丁 RVA 0x%x: %02x->%02x 写入=%s err=%d" % (patch_rva, old.raw[0], newbyte, bool(w), ctypes.get_last_error()))
        # 验证写后回读
        chk = ctypes.create_string_buffer(16)
        k32.ReadProcessMemory(ctypes.c_void_p(pi.hProcess), ctypes.c_void_p(addr), chk, 1, ctypes.byref(n))
        print("  回读 = 0x%02x" % chk.raw[0])
    k32.ResumeThread(pi.hThread)
    t0 = time.time(); alive = True; rc = None
    while time.time() - t0 < secs:
        r = k32.WaitForSingleObject(ctypes.c_void_p(pi.hProcess), 200)
        if r == 0:
            code = wt.DWORD(); k32.GetExitCodeProcess(ctypes.c_void_p(pi.hProcess), ctypes.byref(code))
            rc = code.value; alive = False; break
    dt = time.time() - t0
    print("%-22s -> %s  exit=%s  %.1fs" % (label, "OK存活" if alive else "CRASH", rc and hex(rc), dt), flush=True)
    k32.TerminateProcess(ctypes.c_void_p(pi.hProcess), 0)
    k32.CloseHandle(ctypes.c_void_p(pi.hProcess)); k32.CloseHandle(ctypes.c_void_p(pi.hThread))

if __name__ == "__main__":
    exe = r"C:\Program Files (x86)\VB\Voicemeeter\vmtest.exe"
    # 确保磁盘上是原始文件
    subprocess.run(["taskkill", "/F", "/IM", "vmtest.exe"], capture_output=True)
    time.sleep(0.5)
    import shutil
    shutil.copy2(r"C:\Program Files (x86)\VB\Voicemeeter\voicemeeter8x64.exe1", exe)
    run(exe, None, None, 25, "对照-原版磁盘")
    run(exe, 0x159A00, 0x54, 25, "内存补丁 RVA159A00")
    run(exe, 0x1574C0, 0x47, 25, "内存补丁 RVA1574C0")
