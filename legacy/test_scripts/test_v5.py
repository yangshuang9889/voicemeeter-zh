# -*- coding: utf-8 -*-
"""v5 启动画面实测：验证启动界面出现、5 秒后消失、随后正常拉起 Voicemeeter。"""
import os, subprocess, time, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shot_win

TEMP = os.path.dirname(os.path.abspath(__file__))
EXE = os.path.join(TEMP, "VM8CN_Launcher_v5.exe")

p = subprocess.Popen([EXE], cwd=TEMP)
print("launcher pid", p.pid, "t0", time.strftime("%H:%M:%S"))

t0 = time.time()
shots = [(1.2, "v5_splash_1"), (2.6, "v5_splash_2"), (4.3, "v5_splash_3")]
pending = list(shots)
first_seen = None
last_seen = None
seen_titles = set()
vm_main = None

while time.time() - t0 < 12.0:
    now = time.time() - t0
    wins = shot_win.windows_of(p.pid)
    if wins:
        if first_seen is None:
            first_seen = now
        last_seen = now
        for h, t, c, w, hh in wins:
            seen_titles.add("%s|%s|%dx%d" % (t, c, w, hh))
    if pending and now >= pending[0][0]:
        _, name = pending.pop(0)
        ws = [x for x in win for x in [x]] if False else win
        pass
    # 抓图
    if pending is None:
        pass
    if not pending:
        pass
    if pending == []:
        pending = None
    time.sleep(0.2)
    if vm_main is None:
        r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq voicemeeter8x64.exe", "/NH"],
                           capture_output=True, text=True, encoding="gbk", errors="ignore")
        if "voicemeeter8x64" in (r.stdout or "").lower():
            vm_main = now
    if last_seen is not None and vm_main is not None and now - last_seen > 3:
        break

print("splash 首次出现 t=%.2fs  最后可见 t=%.2fs  持续=%.2fs" %
      (first_seen if first_seen else -1, last_seen if last_seen else -1,
       (last_seen - first_seen) if (first_seen and last_seen) else -1))
print("voicemeeter8x64 出现 t=%s" % ("%.2fs" % vm_main if vm_main else "未检测到"))
for s in sorted(seen_titles):
    print("  win:", s)
print("launcher rc:", p.poll())
