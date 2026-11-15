# -*- coding: utf-8 -*-
"""v6 启动画面实测：抓图 + 消失时间 + 是否正常拉起 Voicemeeter"""
import os, subprocess, time, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shot_win

TEMP = os.path.dirname(os.path.abspath(__file__))
EXE = os.path.join(TEMP, "VM8CN_Launcher_v6.exe")

p = subprocess.Popen([EXE], cwd=TEMP)
print("launcher pid", p.pid, time.strftime("%H:%M:%S"))

t0 = time.time()
shots = [(1.4, "v6_splash_1"), (2.9, "v6_splash_2"), (4.5, "v6_splash_3")]
first = last = None
seen = []
vm = None

while time.time() - t0 < 13.0:
    now = time.time() - t0
    wins = shot_win.windows_of(p.pid)
    if wins:
        if first is None:
            first = now
        last = now
        for h, t, c, w, hh in wins:
            key = "%s|%s|%dx%d" % (t, c, w, hh)
            if key not in seen:
                seen.append(key)
                print("  win t=%.2fs %s" % (now, key))
        if shots and now >= shots[0][0]:
            _, name = shots.pop(0)
            bmp = os.path.join(TEMP, name + ".bmp")
            shot_win.capture(wins[0][0], bmp)
            print("  shot", name, "->", bmp)
    if vm is None:
        r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq voicemeeter8x64.exe", "/NH"],
                           capture_output=True, text=True, encoding="gbk", errors="ignore")
        if "voicemeeter8x64" in (r.stdout or "").lower():
            vm = now
    if first and last and vm and now - last > 3:
        break
    time.sleep(0.2)

print("splash 首现 t=%.2fs  末现 t=%.2fs  持续=%.2fs" % (first or -1, last or -1, (last - first) if (first and last) else -1))
print("voicemeeter8x64 出现 t=%s" % ("%.2fs" % vm if vm else "未检测到"))
print("launcher rc:", p.poll())

try:
    from PIL import Image
    for f in os.listdir(TEMP):
        if f.startswith("v6_splash") and f.endswith(".bmp"):
            im = Image.open(os.path.join(TEMP, f))
            out = os.path.join(TEMP, f[:-4] + ".png")
            im.save(out)
            print("png:", out, im.size)
except Exception as e:
    print("PIL skip:", e)
