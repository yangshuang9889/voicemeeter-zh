# -*- coding: utf-8 -*-
"""v5 时序实测：记录每个窗口的出现/消失时刻，验证启动界面 5 秒后关闭。"""
import os, subprocess, time, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shot_win

TEMP = os.path.dirname(os.path.abspath(__file__))
EXE = os.path.join(TEMP, "VM8CN_Launcher_v5.exe")

p = subprocess.Popen([EXE], cwd=TEMP)
t0 = time.time()
track = {}   # hwnd -> [class, first, last]
while time.time() - t0 < 11.0:
    now = time.time() - t0
    for h, t, c, w, hh in shot_win.windows_of(p.pid):
        if h not in track:
            track[h] = [c, now, now, "%dx%d" % (w, hh)]
        else:
            track[h][2] = now
    time.sleep(0.1)

for h, v in track.items():
    print("hwnd=%s cls=%s %s 出现 %.2fs 消失 %.2fs 持续 %.2fs" % (h, v[0], v[3], v[1], v[2], v[2] - v[1]))
print("launcher rc:", p.poll())
try:
    p.kill()
    print("已结束测试用启动器进程")
except Exception as e:
    print("kill fail", e)
