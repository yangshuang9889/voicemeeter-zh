# -*- coding: utf-8 -*-
"""部署 V1.3（启动器 v9）：编译带 UAC manifest 的启动器并部署到 dist。

相比 deploy_v8.py：
  - 源码/产物切到 v9，新增设置窗口、多版本汉化的产物校验
  - 校验点：requireAdministrator、设置窗口文案、六版本 exe 名、开机自启值名、版本串 V1.3
  - 旧交付 exe 与旧预览图按版本号备份进 _archive

用法：python src\launcher\deploy_v9.py [--no-deploy]
"""
import datetime
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DIST = os.path.join(ROOT, "dist")
ARCHIVE = os.path.join(HERE, "_archive")
CSC = r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"

SRC_CS = os.path.join(HERE, "Launcher_v9.cs")
OUT_EXE = os.path.join(HERE, "VM8CN_Launcher_v9.exe")
DIST_EXE = os.path.join(DIST, "Voicemeeter中文启动器.exe")
OLD_DIST_EXE = os.path.join(DIST, "Voicemeeter8中文启动器.exe")

NO_DEPLOY = "--no-deploy" in sys.argv

if not os.path.isdir(ARCHIVE):
    os.makedirs(ARCHIVE)


def backup(src, name):
    bak = os.path.join(ARCHIVE, name)
    if os.path.isfile(src) and not os.path.isfile(bak):
        shutil.copy2(src, bak)
        print("[backup]", bak, os.path.getsize(bak))


backup(OLD_DIST_EXE, "Voicemeeter8中文启动器_V1.2.exe")

cmd = [CSC, "/nologo", "/target:winexe", "/platform:x64", "/optimize+",
       "/win32manifest:app.manifest",
       "/r:System.dll", "/r:System.Drawing.dll", "/r:System.Windows.Forms.dll",
       "/out:" + OUT_EXE, SRC_CS]
r = subprocess.run(cmd, cwd=HERE, capture_output=True)
print("[csc] rc=", r.returncode)
out = r.stdout.decode("gbk", "ignore")
err = r.stderr.decode("gbk", "ignore")
if out.strip():
    print(out[:3000])
if err.strip():
    print("[stderr]", err[:3000])
if r.returncode != 0:
    raise SystemExit("compile failed")
print("[exe]", OUT_EXE, os.path.getsize(OUT_EXE))

raw = open(OUT_EXE, "rb").read()


def u16(s):
    return s.encode("utf-16-le") in raw


checks = [
    ("requireAdministrator", b"requireAdministrator" in raw),
    ("版本串 V1.3", u16("V1.3")),
    ("设置窗口标题", u16("启动器设置")),
    ("启动秒数项", u16("启动画面等待秒数")),
    ("开机自启项", u16("开机自动启动")),
    ("Run 注册表值名", u16("VoicemeeterZHLauncher")),
    ("配置文件 settings.ini", u16("settings.ini")),
    ("banana_x64 exe", u16("voicemeeterpro_x64.exe")),
    ("banana_x86 exe", u16("voicemeeterpro.exe")),
    ("vm_x64 exe", u16("voicemeeter_x64.exe")),
    ("vm_x86 exe", u16("voicemeeter.exe")),
    ("potato_x86 exe", u16("voicemeeter8.exe")),
    ("设置按钮", u16("设置")),
    ("体积 > 110KB", len(raw) > 110000),
]
for name, ok in checks:
    print("[check]", name, "=", ok)
assert all(ok for _, ok in checks), "check failed"

if NO_DEPLOY:
    print("[skip deploy]")
else:
    shutil.copy2(OUT_EXE, DIST_EXE)
    print("[deploy]", DIST_EXE, os.path.getsize(DIST_EXE))
    if os.path.isfile(OLD_DIST_EXE):
        os.remove(OLD_DIST_EXE)
        print("[clean] 旧名产物已移除 Voicemeeter8中文启动器.exe")

print("[done]", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
