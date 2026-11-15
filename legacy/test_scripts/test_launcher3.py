# -*- coding: utf-8 -*-
"""用启动器拉起 exe1（原版）并验证中文界面。"""
import subprocess, time, os, sys, importlib.util
TEMP = r"C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2Siy4T87X5Sx6qEfhnB8hbI\workspace\conv_7d5c914e13b74cd1a41a32b2f23b1221\temp"
sys.path.insert(0, TEMP)
spec = importlib.util.spec_from_file_location("sw", os.path.join(TEMP, "shot_win.py"))
sw = importlib.util.module_from_spec(spec); spec.loader.exec_module(sw)

subprocess.run(["taskkill", "/F", "/IM", "voicemeeter8x64.exe1"], capture_output=True)
subprocess.run(["taskkill", "/F", "/IM", "voicemeeter8x64.exe"], capture_output=True)
time.sleep(1)

TARGET = r"C:\Program Files (x86)\VB\Voicemeeter\voicemeeter8x64.exe1"
p = subprocess.Popen([os.path.join(TEMP, "VM8CN_Launcher_v2.exe"), TARGET])
time.sleep(10)
print("launcher rc:", p.poll())

r = subprocess.run(["powershell", "-NoProfile", "-Command",
     "Get-Process | Where-Object { $_.ProcessName -like 'voicemeeter*' } | ForEach-Object { \"$($_.Id)|$($_.ProcessName)\" }"],
     capture_output=True, text=True)
lines = [l for l in r.stdout.splitlines() if '|' in l]
print("进程:", lines)
if not lines:
    print("未启动"); sys.exit(1)
pid = int(lines[0].split('|')[0])
wins = sw.windows_of(pid)
print("窗口:", wins)
best = None
for hwnd, title, cls, w, h in wins:
    if 'MainWindow' in cls: best = (hwnd, title, cls, w, h); break
if best is None and wins: best = max(wins, key=lambda x: x[3]*x[4])
if best:
    bmp = os.path.join(TEMP, "launcher_test3.bmp")
    print("截图:", best, sw.capture(best[0], bmp))
    from PIL import Image
    Image.open(bmp).save(os.path.join(TEMP, "launcher_test3.png"))
    print("已保存 launcher_test3.png")
else:
    print("无窗口")
