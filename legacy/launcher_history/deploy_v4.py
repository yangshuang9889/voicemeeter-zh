# -*- coding: utf-8 -*-
import re, os, sys
TEMP = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(TEMP, "Launcher.cs"), encoding="utf-8").read()
b64 = open(os.path.join(TEMP, "patch_blob_v4_b64.txt"), encoding="utf-8").read().strip()
# 分段，每行 4000 字符
chunks = [b64[i:i+4000] for i in range(0, len(b64), 4000)]
lit = '\n            + '.join('"%s"' % c for c in chunks)
new = "static readonly string BLOB =\n            " + lit + ";"
pat = re.compile(r"static readonly string BLOB\s*=.*?;", re.S)
assert pat.search(src), "BLOB 声明未找到"
out = pat.sub(lambda m: new, src, count=1)
dst = os.path.join(TEMP, "Launcher_v4.cs")
open(dst, "w", encoding="utf-8").write(out)
print("写入", dst, "b64 长度", len(b64), "分", len(chunks), "段")
