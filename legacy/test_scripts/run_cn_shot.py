# -*- coding: utf-8 -*-
"""启动原版 + 全量内存汉化，等待界面出现后按 PID 截图。"""
import ctypes, ctypes.wintypes as wt, subprocess, time, os, shutil, importlib.util, sys

TEMP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TEMP)
spec = importlib.util.spec_from_file_location("mpf", os.path.join(TEMP, "mem_patch_full.py"))
mpf = importlib.util.module_from_spec(spec); spec.loader.exec_module(mpf)
spec2 = importlib.util.spec_from_file_location("sw", os.path.join(TEMP, "shot_win.py"))
sw = importlib.util.module_from_spec(spec2); spec2.loader.exec_module(sw)

k32 = mpf.k32
ORIG = mpf.ORIG; TEST = mpf.TEST

subprocess.run(["taskkill", "/F", "/IM", "vmtest.exe"], capture_output=True)
time.sleep(0.6)
shutil.copy2(ORIG, TEST)
si = mpf.STARTUPINFOA(); si.cb = ctypes.sizeof(si); pi = mpf.PI()
k32.CreateProcessA(TEST.encode(), None, None, None, False, mpf.CREATE_SUSPENDED, None, None,
                   ctypes.byref(si), ctypes.byref(pi))
base = mpf.image_base(pi.hProcess)
print("ImageBase = %#x pid=%d" % (base, pi.dwProcessId))
mpf.apply_patches(pi.hProcess, base)
k32.ResumeThread(pi.hThread)
print("已恢复运行，等待界面...")
time.sleep(8)
wins = sw.windows_of(pi.dwProcessId)
print("该进程窗口:", wins)
best = None
for hwnd, title, cls, w, h in wins:
    if 'MainWindow' in cls or 'Voicemeeter' in cls:
        best = (hwnd, title, cls, w, h); break
if best is None:
    for hwnd, title, cls, w, h in wins:
        if w > 300 and h > 200:
            best = (hwnd, title, cls, w, h); break
if best:
    p = os.path.join(TEMP, "vm_cn_win.bmp")
    print("截图:", best, sw.capture(best[0], p), p)
else:
    print("未找到合适窗口")
time.sleep(1)
k32.TerminateProcess(ctypes.c_void_p(pi.hProcess), 0)
