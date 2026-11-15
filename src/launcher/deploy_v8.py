# -*- coding: utf-8 -*-
"""部署 V1.2（启动器 v8）：编译带 UAC manifest 的启动器，部署到 dist，刷新启动界面预览图。

相比 deploy_v7.py：
  - 源码/产物切到 v8，新增「打开配置目录」文案校验
  - 旧交付 exe 与旧预览图按版本号备份进 _archive

用法：python src\launcher\deploy_v8.py
"""
import os
import shutil
import subprocess
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DIST = os.path.join(ROOT, "dist")
ARCHIVE = os.path.join(HERE, "_archive")
CSC = r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"

SRC_CS = os.path.join(HERE, "Launcher_v8.cs")
OUT_EXE = os.path.join(HERE, "VM8CN_Launcher_v8.exe")
DIST_EXE = os.path.join(DIST, "Voicemeeter8中文启动器.exe")
PREVIEW = os.path.join(DIST, "启动界面预览.png")
PREVIEW_SRC = (r"C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User"
               r"\oAN1i2Siy4T87X5Sx6qEfhnB8hbI\workspace\conv_7d5c914e13b74cd1a41a32b2f23b1221"
               r"\temp\win_splash_v8.png")

if not os.path.isdir(ARCHIVE):
    os.makedirs(ARCHIVE)


def backup(src, name):
    """把 src 备份到 _archive/name（已存在则不覆盖）。"""
    bak = os.path.join(ARCHIVE, name)
    if os.path.isfile(src) and not os.path.isfile(bak):
        shutil.copy2(src, bak)
        print("[backup]", bak, os.path.getsize(bak))


# 1) 备份旧交付物
backup(DIST_EXE, "Voicemeeter8中文启动器_V1.1.exe")
backup(PREVIEW, "启动界面预览_V1.1.png")

# 2) 编译（带 app.manifest，requireAdministrator）
cmd = [CSC, "/nologo", "/target:winexe", "/platform:x64", "/optimize+",
       "/win32manifest:app.manifest",
       "/r:System.dll", "/r:System.Drawing.dll", "/r:System.Windows.Forms.dll",
       "/out:" + OUT_EXE, SRC_CS]
r = subprocess.run(cmd, cwd=HERE, capture_output=True)
print("[csc] rc=", r.returncode)
if r.stdout:
    print(r.stdout.decode("gbk", "ignore")[:2000])
if r.returncode != 0:
    raise SystemExit("compile failed")
print("[exe]", OUT_EXE, os.path.getsize(OUT_EXE))

# 3) 交付前校验：提权清单 + V1.2 两处文案 + 体积下限
raw = open(OUT_EXE, "rb").read()
checks = [
    ("requireAdministrator", b"requireAdministrator" in raw),
    ("help panel text", "授权与激活帮助".encode("utf-16-le") in raw),
    ("config button text", "打开配置目录".encode("utf-16-le") in raw),
    ("version V1.2", "V1.2".encode("utf-16-le") in raw),
    ("size > 80KB", len(raw) > 80000),
]
for name, ok in checks:
    print("[check]", name, "=", ok)
assert all(ok for _, ok in checks)

# 4) 部署
shutil.copy2(OUT_EXE, DIST_EXE)
print("[deploy]", DIST_EXE, os.path.getsize(DIST_EXE))

# 5) 刷新预览图
if os.path.isfile(PREVIEW_SRC):
    shutil.copy2(PREVIEW_SRC, PREVIEW)
    print("[preview]", PREVIEW, os.path.getsize(PREVIEW))
else:
    print("[preview] skip, not found:", PREVIEW_SRC)

print("[done]", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
