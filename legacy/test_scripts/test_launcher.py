# -*- coding: utf-8 -*-
"""测试启动器：清理进程 -> 运行启动器 -> 截图验证中文。"""
import ctypes, ctypes.wintypes as wt, subprocess, time, os, sys, importlib.util

TEMP = r"C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2Siy4T87X5Sx6qEfhnB8hbI\workspace\conv_7d5c914e13b74cd1a41a32b2f23b1221\temp"
LAUNCHER = os.path.join(TEMP, "VM8CN_Launcher.exe")
sys.path.insert(0, TEMP)
spec = importlib.util.spec_from_file_location("sw", os.path.join(TEMP, "shot_win.py"))
sw = importlib.util.module_from_spec(spec); spec.loader.exec_module(sw)

subprocess.run(["taskkill", "/F", "/IM", "voicemeeter8x64.exe"], capture_output=True)
subprocess.run(["taskkill", "/F", "/IM", "vmtest.exe"], capture_output=True)
time.sleep(1.0)

p = subprocess.Popen([LAUNCHER])
print("启动器 pid", p.pid)
time.sleep(9)
p.poll()
print("启动器是否已退出:", p.returncode)

out = subprocess.run(["powershell", "-NoProfile", "-Command",
                      "(Get-Process voicemeeter8x64 -ErrorAction SilentlyContinue | Select-Object -First 1).Id"],
                     capture_output=True, text=True)
pid_txt = out.stdout.strip()
print("voicemeeter pid:", repr(pid_txt))
if not pid_txt:
    print("未启动成功"); sys.exit(1)
pid = int(pid_txt)
wins = sw.windows_of(pid)
print("窗口:", wins)
best = None
for hwnd, title, cls, w, h in wins:
    if 'MainWindow' in cls:
        best = (hwnd, title, cls, w, h); break
if best is None and wins:
    best = max(wins, key=lambda x: x[3]*x[4])
if best:
    bmp = os.path.join(TEMP, "launcher_test.bmp")
    print("截图:", best, sw.capture(best[0], bmp))
    from PIL import Image
    Image.open(bmp).save(os.path.join(TEMP, "launcher_test.png"))
    print("png ok")
else:
    print("未找到窗口")
