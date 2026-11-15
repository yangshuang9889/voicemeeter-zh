# -*- coding: utf-8 -*-
"""v5 启动画面实测：验证启动界面出现、5 秒后消失、随后正常拉起 Voicemeeter。"""
import os, subprocess, time, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shot_win

TEMP = os.path.dirname(os.path.abspath(__file__))
EXE = os.path.join(TEMP, "VM8CN_Launcher_v5.exe")

p = subprocess.Popen([EXE], cwd=TEMP)
print("launcher pid", p.pid)

t0 = time.time()
want = [(1.2, "v5_splash_1.bmp"), (2.6, "v5_splash_2.bmp"), (4.3, "v5_splash_3.bmp")]
first_seen = last_seen = None
titles = set()
vm_seen = None

while time.time() - t0 < 20.0:
    now = time.time() - t0
    wins = shot_win.windows_of(p.pid)
    if wins:
        if first_seen is None:
            first_seen = now
        last_seen = now
        for h, t, c, w, hh in wins:
            titles.add("%s | %s | %dx%d" % (t, c, w, hh))
            if want and now >= want[0][0]:
                _, name = want.pop(0)
                try:
                    shot_win.capture(h, os.path.join(TEMP, name))
                    print("shot %s @ t=%.2f hwnd=%s %dx%d" % (name, now, h, w, hh))
                except Exception as ex:
                    print("shot fail", ex)
    if vm_seen is None:
        r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq voicemeeter8x64.exe", "/NH"],
                           capture_output=True, text=True, encoding="gbk", errors="ignore")
        if "voicemeeter8x64" in (r.stdout or "").lower():
            vm_seen = now
    if last_seen and vm_seen and now - last_seen > 2.5:
        break
    time.sleep(0.15)

dur = (last_seen - first_seen) if (first_seen and last_seen) else -1
print("splash 首次出现 t=%.2fs，最后可见 t=%.2fs，持续 %.2fs" %
      (first_seen or -1, last_seen or -1, dur))
print("voicemeeter8x64 出现于 t=%s" % (("%.2fs" % vm_seen) if vm_seen else "未检测到"))
for t in sorted(titles):
    print("  win:", t)
print("launcher 退出码:", p.poll())
