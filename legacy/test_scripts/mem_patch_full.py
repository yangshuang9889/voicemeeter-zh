# -*- coding: utf-8 -*-
"""全量内存汉化补丁验证。"""
import ctypes, ctypes.wintypes as wt, subprocess, time, os, json, shutil

TEMP = os.path.dirname(os.path.abspath(__file__))
ORIG = r"C:\Program Files (x86)\VB\Voicemeeter\voicemeeter8x64.exe1"
TEST = r"C:\Program Files (x86)\VB\Voicemeeter\vmtest.exe"

SHORT = {
    0x15a9a0: '复制门限', 0x15aa40: '保存门限', 0x15a820: '单', 0x15a830: '单',
    0x1599d8: 'A1声道#%i', 0x1599f8: 'A2声道#%i', 0x159a18: 'A3声道#%i',
    0x159a38: 'A4声道#%i', 0x159a58: 'A5声道#%i', 0x159a78: 'B1声道#%i',
    0x159a98: 'B2声道#%i', 0x159ab8: 'B3声道#%i',
}

k32 = ctypes.WinDLL('kernel32', use_last_error=True)
ntdll = ctypes.WinDLL('ntdll')
CREATE_SUSPENDED = 4

class STARTUPINFOA(ctypes.Structure):
    _fields_ = [("cb", wt.DWORD), ("lpReserved", wt.LPSTR), ("lpDesktop", wt.LPSTR),
                ("lpTitle", wt.LPSTR), ("dwX", wt.DWORD), ("dwY", wt.DWORD),
                ("dwXSize", wt.DWORD), ("dwYSize", wt.DWORD),
                ("dwXCountChars", wt.DWORD), ("dwYCountChars", wt.DWORD),
                ("dwFillAttribute", wt.DWORD), ("dwFlags", wt.DWORD),
                ("wShowWindow", wt.WORD), ("cbReserved2", wt.WORD),
                ("lpReserved2", ctypes.c_void_p), ("hStdInput", wt.HANDLE),
                ("hStdOutput", wt.HANDLE), ("hStdError", wt.HANDLE)]

class PI(ctypes.Structure):
    _fields_ = [("hProcess", wt.HANDLE), ("hThread", wt.HANDLE),
                ("dwProcessId", wt.DWORD), ("dwThreadId", wt.DWORD)]

class PBI(ctypes.Structure):
    _fields_ = [("ExitStatus", ctypes.c_long), ("PebBaseAddress", ctypes.c_void_p),
                ("AffinityMask", ctypes.c_void_p), ("BasePriority", ctypes.c_long),
                ("UniqueProcessId", ctypes.c_void_p), ("InheritedFromUniqueProcessId", ctypes.c_void_p)]

def image_base(h):
    pbi = PBI(); ret = ctypes.c_ulong(0)
    ntdll.NtQueryInformationProcess(ctypes.c_void_p(h), 0, ctypes.byref(pbi), ctypes.sizeof(pbi), ctypes.byref(ret))
    v = ctypes.c_ulonglong(0); n = ctypes.c_size_t(0)
    k32.ReadProcessMemory(ctypes.c_void_p(h), ctypes.c_void_p(pbi.PebBaseAddress + 0x10), ctypes.byref(v), 8, ctypes.byref(n))
    return v.value

def off2rva_map():
    import struct
    raw = open(ORIG, 'rb').read()
    pe = struct.unpack_from('<I', raw, 0x3c)[0]
    nsec = struct.unpack_from('<H', raw, pe+6)[0]
    so = pe + 24 + struct.unpack_from('<H', raw, pe+20)[0]
    secs = []
    for i in range(nsec):
        o = so + i*40
        vs, va, rs, ra = struct.unpack_from('<IIII', raw, o+8)
        secs.append((ra, rs, va))
    def conv(off):
        for ra, rs, va in secs:
            if ra <= off < ra + rs:
                return off - ra + va
        return None
    return conv

def apply_patches(h, base):
    items = json.load(open(os.path.join(TEMP, "patch_table.json"), encoding="utf-8"))
    conv = off2rva_map()
    print("补丁条目:", len(items))
    ok = fail = 0
    sample = []
    for k, txt in items.items():
        off = int(k, 16) if k.lower().startswith("0x") else int(k)
        rva = conv(off)
        if rva is None:
            fail += 1; continue
        txt = SHORT.get(off, txt)
        try:
            e = txt.encode('gbk')
        except Exception:
            fail += 1; continue
        addr = base + rva
        # 读原串可用长度
        buf = ctypes.create_string_buffer(256); n = ctypes.c_size_t(0)
        if not k32.ReadProcessMemory(ctypes.c_void_p(h), ctypes.c_void_p(addr), buf, 200, ctypes.byref(n)):
            fail += 1; continue
        raw = buf.raw[:n.value]
        cap = raw.find(b'\0')
        if cap < 0:
            fail += 1; continue
        if len(e) > cap:
            fail += 1; continue
        payload = e + b'\0' * (cap - len(e) + 1)
        oldp = wt.DWORD(0)
        k32.VirtualProtectEx(ctypes.c_void_p(h), ctypes.c_void_p(addr & ~0xFFF),
                             ctypes.c_size_t((len(payload) + 0x1000) & ~0xFFF), 0x04, ctypes.byref(oldp))
        if k32.WriteProcessMemory(ctypes.c_void_p(h), ctypes.c_void_p(addr), payload, len(payload), ctypes.byref(n)):
            ok += 1
        else:
            fail += 1
    print("内存写入成功 %d 条，失败 %d 条" % (ok, fail))
    return ok, fail

def main(secs=30):
    subprocess.run(["taskkill", "/F", "/IM", "vmtest.exe"], capture_output=True); time.sleep(0.5)
    shutil.copy2(ORIG, TEST)
    si = STARTUPINFOA(); si.cb = ctypes.sizeof(si); pi = PI()
    if not k32.CreateProcessA(TEST.encode(), None, None, None, False, CREATE_SUSPENDED, None, None,
                              ctypes.byref(si), ctypes.byref(pi)):
        print("CreateProcess 失败", ctypes.get_last_error()); return
    base = image_base(pi.hProcess)
    print("ImageBase = %#x" % base)
    apply_patches(pi.hProcess, base)
    k32.ResumeThread(pi.hThread)
    t0 = time.time(); alive = True; rc = None
    while time.time() - t0 < secs:
        if k32.WaitForSingleObject(ctypes.c_void_p(pi.hProcess), 200) == 0:
            c = wt.DWORD(); k32.GetExitCodeProcess(ctypes.c_void_p(pi.hProcess), ctypes.byref(c))
            rc = c.value; alive = False; break
    print("结果: %s exit=%s 存活 %.1fs" % ("OK存活" if alive else "CRASH", hex(rc) if rc else rc, time.time()-t0))
    # 截图
    try:
        import subprocess as sp
        shot = os.path.join(TEMP, "vm_cn_shot.png")
        sp.run(["powershell", "-NoProfile", "-Command",
                "Add-Type -AssemblyName System.Windows.Forms,System.Drawing;"
                "$b=[System.Windows.Forms.SystemInformation]::VirtualScreen;"
                "$bmp=New-Object System.Drawing.Bitmap $b.Width,$b.Height;"
                "$g=[System.Drawing.Graphics]::FromImage($bmp);"
                "$g.CopyFromScreen($b.Left,$b.Top,0,0,$bmp.Size);"
                "$bmp.Save('%s',[System.Drawing.Imaging.ImageFormat]::Png)" % shot], capture_output=True)
        print("截图:", shot, os.path.exists(shot))
    except Exception as e:
        print("截图失败", e)
    k32.TerminateProcess(ctypes.c_void_p(pi.hProcess), 0)

if __name__ == "__main__":
    main()
