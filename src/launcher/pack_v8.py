# -*- coding: utf-8 -*-
r"""打包 V1.2 分享包（exe + 使用说明 + 分享介绍 + 预览图），并做交付前校验。

用法：python src\launcher\pack_v8.py
前置：deploy_v8.py + update_docs_v8.py 已执行（dist 内容均为 V1.2）
"""
import io
import os
import zipfile
import hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIST = os.path.join(ROOT, "dist")

EXE = os.path.join(DIST, "Voicemeeter8中文启动器.exe")
TXT = os.path.join(DIST, "使用说明.txt")
MD = os.path.join(DIST, "分享介绍.md")
PNG = os.path.join(DIST, "启动界面预览.png")
ZIP = os.path.join(DIST, "Voicemeeter中文启动器_V1.2_分享包.zip")

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
checks = [
    ("exe > 80KB", len(raw) > 80000),
    ("UAC manifest", b"requireAdministrator" in raw),
    ("帮助面板文案", "授权与激活帮助".encode("utf-16-le") in raw),
    ("配置目录文案", "打开配置目录".encode("utf-16-le") in raw),
    ("exe 版本 V1.2", "V1.2".encode("utf-16-le") in raw),
    ("说明标题 V1.2", "中文界面启动器 V1.2" in txt),
    ("说明含 V1.2 章节", "【V1.2 新增】一键打开配置目录" in txt),
    ("说明四按钮", "底部四个按钮" in txt),
    ("分享介绍 V1.2 标题", "启动器 V1.2" in md),
    ("分享介绍配置行", "| 配置定位 |" in md),
]
for name, ok in checks:
    print("[check]", name, "=", ok)
assert all(ok for _, ok in checks)

# 3) 打包（旧版本包保留，不删）
if os.path.exists(ZIP):
    os.remove(ZIP)
with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(EXE, "Voicemeeter8中文启动器.exe")
    z.write(TXT, "使用说明.txt")
    z.write(MD, "分享介绍.md")
    z.write(PNG, "启动界面预览.png")

with zipfile.ZipFile(ZIP) as z:
    print("[zip] 条目:")
    for i in z.infolist():
        print("   %-32s %8d" % (i.filename, i.file_size))
print("[zip]", ZIP, os.path.getsize(ZIP))
print("[sha256] exe", hashlib.sha256(raw).hexdigest()[:32])

print("\n[dist]")
for f in sorted(os.listdir(DIST)):
    print("   %-44s %8d" % (f, os.path.getsize(os.path.join(DIST, f))))
