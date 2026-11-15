# -*- coding: utf-8 -*-
"""v4 正式验收：启动安装目录 exe1 等价副本，长时间存活检查 + 主界面截图。"""
import subprocess, time, os, sys, importlib.util
TEMP = r"C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2Siy4T87X5Sx6qEfhnB8hbI\workspace\conv_7d5c914e13b74cd1a41a32b2f23b1221\temp"
sys.path.insert(0, TEMP)
spec = importlib.util.spec_from_file_location("sw", os.path.join(TEMP, "shot_win.py"))
sw = importlib.util.module_from_spec(spec); spec.loader.exec_module(sw)

subprocess.run(["taskkill", "/F", "/IM", "voicemeeter8x64.exe1"], capture_output=True)
subprocess.run(["taskkill", "/F", "/IM", "voicemeeter8x64.exe"], capture_output=True)
time.sleep(1)

TARGET = r"C:\Program Files (x86)\VB\Voicemeeter\voicemeeter8x64.exe"
p = subprocess.Popen([os.path.join(TEMP, "VM8CN_Launcher_v4.exe"), TARGET])
time.sleep(12)

def alive(pid):
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
        "Get-Process -Id %d -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count" % pid],
        capture_output=True, text=True)
    return r.stdout.strip().startswith('1')

r = subprocess.run(["powershell", "-NoProfile", "-Command",
     "Get-Process | Where-Object { $_.ProcessName -like 'voicemeeter8x64*' } | ForEach-Object { \"$($_.Id)\" }"],
     capture_output=True, text=True)
ids = [x.strip() for x in r.stdout.splitlines() if x.strip().isdigit()]
print("启动后进程:", ids)
if not ids:
    print("FAIL 未启动"); sys.exit(1)
pid = int(ids[0])

wins = sw.windows_of(pid)
for hwnd, title, cls, w, h in wins:
    print("WIN", hwnd, repr(title), cls, w, h)
best = None
for hwnd, title, cls, w, h in wins:
    if 'MainWindow' in cls: best = (hwnd, title, cls, w, h); break
if best:
    bmp = os.path.join(TEMP, "final_main.bmp")
    sw.capture(best[0], bmp)
    from PIL import Image
    im = Image.open(bmp)
    # 若窗口被最小化则还原
    if im.size[0] < 400:
        sw_restore = __import__('ctypes').windll.user32.ShowWindow(best[0], 9)
        time.sleep(1.5)
        sw.capture(best[0], bmp); im = Image.open(bmp)
    im.save(os.path.join(TEMP, "final_main.png"))
    print("主界面截图保存 final_main.png", im.size)

for t in (20, 40):
    time.sleep(t - (0 if t == 20 else 20))
    print("t=%ds 存活=%s" % (t, alive(pid)))

wins2 = sw.windows_of(pid)
print("结束窗口数:", len(wins2), [w[1] for w in wins2])
