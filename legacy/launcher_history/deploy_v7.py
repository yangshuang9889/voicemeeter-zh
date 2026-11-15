# -*- coding: utf-8 -*-
"""部署 v7：编译带 UAC manifest 的启动器，部署到 dist，刷新启动界面预览图。

用法：python src\launcher\deploy_v7.py
"""
import io, os, shutil, subprocess, datetime

TEMP = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(TEMP))
DIST = os.path.join(ROOT, "dist")
ARCHIVE = os.path.join(TEMP, "_archive")
CSC = r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"

SRC_CS = os.path.join(TEMP, "Launcher_v7.cs")
OUT_EXE = os.path.join(TEMP, "VM8CN_Launcher_v7.exe")
DIST_EXE = os.path.join(DIST, "Voicemeeter8中文启动器.exe")
PREVIEW = os.path.join(DIST, "启动界面预览.png")
PREVIEW_SRC = (r"C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User"
               r"\oAN1i2Siy4T87X5Sx6qEfhnB8hbI\workspace\conv_7d5c914e13b74cd1a41a32b2f23b1221"
               r"\temp\win_splash_v7.png")

if not os.path.isdir(ARCHIVE):
    os.makedirs(ARCHIVE)

# 1) 备份旧交付 exe
if os.path.isfile(DIST_EXE):
    bak = os.path.join(ARCHIVE, "Voicemeeter8中文启动器_V1.0.exe")
    if not os.path.isfile(bak):
        shutil.copy2(DIST_EXE, bak)
        print("[backup]", bak, os.path.getsize(bak))

# 2) 编译（带 app.manifest，requireAdministrator）
cmd = [CSC, "/nologo", "/target:winexe", "/platform:x64", "/optimize+",
       "/win32manifest:app.manifest",
       "/r:System.dll", "/r:System.Drawing.dll", "/r:System.Windows.Forms.dll",
       "/out:" + OUT_EXE, SRC_CS]
r = subprocess.run(cmd, cwd=TEMP, capture_output=True)
print("[csc] rc=", r.returncode)
if r.stdout:
    print(r.stdout.decode("gbk", "ignore")[:2000])
if r.returncode != 0:
    raise SystemExit("compile failed")
print("[exe]", OUT_EXE, os.path.getsize(OUT_EXE))

# 3) 基础校验：UAC manifest + 帮助面板字符串存在
raw = open(OUT_EXE, "rb").read()
has_admin = b"requireAdministrator" in raw
probe = "授权与激活帮助"
has_panel = probe.encode("utf-16-le") in raw
has_blob = len(raw) > 80000
print("[check] requireAdministrator=", has_admin, "panel_text=", has_panel, "size_ok=", has_blob)
assert has_admin and has_panel

# 4) 部署
shutil.copy2(OUT_EXE, DIST_EXE)
print("[deploy]", DIST_EXE, os.path.getsize(DIST_EXE))

# 5) 刷新预览图
if os.path.isfile(PREVIEW_SRC):
    if os.path.isfile(PREVIEW):
        shutil.copy2(PREVIEW, os.path.join(ARCHIVE, "启动界面预览_V1.0.png"))
    shutil.copy2(PREVIEW_SRC, PREVIEW)
    print("[preview]", PREVIEW, os.path.getsize(PREVIEW))
else:
    print("[preview] skip, not found:", PREVIEW_SRC)

print("[done]", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
