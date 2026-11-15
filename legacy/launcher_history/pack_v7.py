# -*- coding: utf-8 -*-
"""打包 V1.1 分享包（exe + 使用说明 + 分享介绍 + 预览图），并做交付前校验。

用法：python src\launcher\pack_v7.py
前置：已执行 deploy_v7.py（dist 下 exe 与预览图已是 v7）
"""
import io, os, zipfile, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIST = os.path.join(ROOT, "dist")

EXE = os.path.join(DIST, "Voicemeeter8中文启动器.exe")
TXT = os.path.join(DIST, "使用说明.txt")
MD = os.path.join(DIST, "分享介绍.md")
PNG = os.path.join(DIST, "启动界面预览.png")
ZIP = os.path.join(DIST, "Voicemeeter中文启动器_V1.1_分享包.zip")

# 1) 统一换行 CRLF，避免手改文档混入裸 LF
for p, enc in ((TXT, "utf-8-sig"), (MD, "utf-8")):
    s = open(p, "rb").read().decode(enc)
    s = s.replace("\r\n", "\n").replace("\n", "\r\n")
    io.open(p, "w", encoding=enc, newline="").write(s)
    print("[crlf]", os.path.basename(p), os.path.getsize(p))

# 2) 校验
raw = open(EXE, "rb").read()
checks = [
    ("exe 存在且 >80KB", len(raw) > 80000),
    ("UAC manifest", b"requireAdministrator" in raw),
    ("帮助面板文案", "授权与激活帮助".encode("utf-16-le") in raw),
    ("说明含 V1.1 章节", "【V1.1 新增】授权与激活帮助面板" in open(TXT, "rb").read().decode("utf-8-sig")),
    ("分享介绍含新行", "| 授权帮助 |" in open(MD, "rb").read().decode("utf-8")),
]
for name, ok in checks:
    print("[check]", name, "=", ok)
assert all(ok for _, ok in checks)

# 3) 打包（旧 V1.0 包保留，不删）
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
