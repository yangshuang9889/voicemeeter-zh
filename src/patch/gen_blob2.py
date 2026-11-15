# -*- coding: utf-8 -*-
"""生成 v3 补丁 blob：ANSI(GBK) + UTF-16LE 双编码，条目格式 rva(4) len(2) enc(1) data(len)。"""
import json, os, struct, base64, sys

TEMP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TEMP)
from utf16_zh import U16
from gen_blob import SHORT  # 复用超短串覆盖表

ORIG = r"C:\Program Files (x86)\VB\Voicemeeter\voicemeeter8x64.exe1"
raw = open(ORIG, 'rb').read()

pe = struct.unpack_from('<I', raw, 0x3c)[0]
nsec = struct.unpack_from('<H', raw, pe + 6)[0]
so = pe + 24 + struct.unpack_from('<H', raw, pe + 20)[0]
secs = []
for i in range(nsec):
    o = so + i * 40
    vs, va, rs, ra = struct.unpack_from('<IIII', raw, o + 8)
    secs.append((ra, rs, va))


def off2rva(off):
    for ra, rs, va in secs:
        if ra <= off < ra + rs:
            return off - ra + va
    return None


def cap_ansi(off):
    p = raw.find(b'\0', off)
    return p - off


def cap_utf16(off):
    j = off
    while j + 1 < len(raw):
        if raw[j] == 0 and raw[j + 1] == 0:
            return j - off
        j += 2
    return -1


blob = bytearray()
ok = skip = 0
report = []

# 1) ANSI 表
items = json.load(open(os.path.join(TEMP, "patch_table.json"), encoding="utf-8"))
for k, txt in items.items():
    off = int(k, 16) if k.lower().startswith("0x") else int(k)
    rva = off2rva(off)
    if rva is None:
        skip += 1; continue
    txt = SHORT.get(off, txt)
    try:
        e = txt.encode('gbk')
    except Exception:
        skip += 1; continue
    cap = cap_ansi(off)
    if cap <= 0 or len(e) > cap:
        report.append(('ANSI', hex(off), txt, len(e), cap)); skip += 1; continue
    blob += struct.pack('<IHB', rva, len(e), 0) + e
    ok += 1

ansi_ok = ok

# 2) UTF-16 表
for off, txt in sorted(U16.items()):
    rva = off2rva(off)
    if rva is None:
        skip += 1; continue
    try:
        e = txt.encode('utf-16le')
    except Exception:
        skip += 1; continue
    cap = cap_utf16(off)
    if cap <= 0 or len(e) > cap:
        report.append(('U16', hex(off), txt, len(e), cap)); skip += 1; continue
    blob += struct.pack('<IHB', rva, len(e), 1) + e
    ok += 1

print("打包成功 %d 条（ANSI %d / UTF16 %d），跳过 %d 条" % (ok, ansi_ok, ok - ansi_ok, skip))
for r in report:
    print("  超长跳过:", r)
b64 = base64.b64encode(bytes(blob)).decode()
open(os.path.join(TEMP, "patch_blob_v3_b64.txt"), "w", encoding="utf-8").write(b64)
print("blob %d 字节, base64 %d 字符" % (len(blob), len(b64)))
