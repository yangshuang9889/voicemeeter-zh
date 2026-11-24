# -*- coding: utf-8 -*-
r"""打包 V1.3 分享包（exe + 使用说明 + 分享介绍 + 预览图），并做交付前校验。

用法：python src\launcher\pack_v9.py
前置：deploy_v9.py 已执行、dist 内四份文件均为 V1.3 内容
"""
import io
import os
import zipfile
import hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIST = os.path.join(ROOT, "dist")

EXE_NAME = "Voicemeeter中文启动器.exe"
EXE = os.path.join(DIST, EXE_NAME)
TXT = os.path.join(DIST, "使用说明.txt")
MD = os.path.join(DIST, "分享介绍.md")
PNG = os.path.join(DIST, "启动界面预览.png")
ZIP = os.path.join(DIST, "Voicemeeter中文启动器_V1.3_分享包.zip")

# 1) 统一换行 CRLF，避免手改文档混入裸 LF
for p, enc in ((TXT, "utf-8-sig"), (MD, "utf-8")):
    s = open(p, "rb").read().decode(enc)
    s = s.replace("\r\n", "\n").replace("\n", "\r\n")
    io.open(p, "w", encoding=enc, newline="").write(s)
    print("[crlf]", os.path.basename(p), os.path.getsize(p))

# 2) 校验
raw = open(EXE, "rb").read()
txt = open(TXT, "rb").read().decode("utf-8-sig")
md = open(MD, "rb").read().decode("utf-8")
u16 = lambda s: s.encode("utf-16-le")

checks = [
    ("exe > 150KB", len(raw) > 150000),
    ("UAC manifest", b"requireAdministrator" in raw),
    ("设置窗口标题", u16("设置 - Voicemeeter 中文界面启动器") in raw),
    ("设置项-秒数", u16("启动画面等待秒数") in raw),
    ("设置项-自启", u16("开机自动启动") in raw),
    ("自启命令参数", u16("--autostart") in raw),
    ("六版本-Banana", u16("voicemeeterpro_x64.exe") in raw),
    ("六版本-VM", u16("voicemeeter_x64.exe") in raw),
    ("启动画面设置按钮", u16("打开配置目录") in raw),
    ("exe 版本 V1.3", u16("V1.3") in raw),
    ("说明标题 V1.3", "中文界面启动器 V1.3" in txt),
    ("说明设置章节", "三、设置窗口（V1.3 新增）" in txt),
    ("说明六版本表", "六个版本与汉化条目数" in txt),
    ("说明自启注册表", "VoicemeeterZHLauncher" in txt),
    ("说明命令行段", "十、命令行参数" in txt),
    ("分享介绍 V1.3 标题", "启动器 V1.3" in md),
    ("分享介绍自启行", "开机自启开关" in md),
    ("分享介绍六版本", "Potato、Banana、Voicemeeter" in md),
    ("预览图存在", os.path.exists(PNG) and os.path.getsize(PNG) > 20000),
]
for name, ok in checks:
    print("[check]", "%-18s" % name, "=", ok)
bad = [n for n, ok in checks if not ok]
assert not bad, bad

# 3) 打包（旧版本包保留，不删）
if os.path.exists(ZIP):
    os.remove(ZIP)
with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(EXE, EXE_NAME)
    z.write(TXT, "使用说明.txt")
    z.write(MD, "分享介绍.md")
    z.write(PNG, "启动界面预览.png")

with zipfile.ZipFile(ZIP) as z:
    print("[zip] 条目:")
    for i in z.infolist():
        print("   %-34s %9d" % (i.filename, i.file_size))
    assert z.testzip() is None
print("[zip]", ZIP, os.path.getsize(ZIP))
print("[sha256] exe", hashlib.sha256(raw).hexdigest())
print("[sha256] zip", hashlib.sha256(open(ZIP, "rb").read()).hexdigest())

print("\n[dist]")
for f in sorted(os.listdir(DIST)):
    print("   %-46s %9d" % (f, os.path.getsize(os.path.join(DIST, f))))
print("\nOK: %d/%d checks passed" % (len(checks), len(checks)))
