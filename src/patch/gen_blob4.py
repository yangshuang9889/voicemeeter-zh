# -*- coding: utf-8 -*-
"""生成 v4 补丁 blob：v3 全量 + 第二轮补齐(EXTRA) + samples 系列自动翻译。"""
import json, os, struct, base64, sys, re

TEMP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TEMP)
from utf16_zh import U16
from gen_blob import SHORT
from extra_zh import EXTRA
from extra_zh2 import MULTI
EXTRA.update(MULTI)

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


def zstr(off):
    p = raw.find(b'\0', off)
    try:
        return raw[off:p].decode('ascii')
    except Exception:
        return None


blob = bytearray()
ok = skip = 0
report = []
seen = set()

def add(off, txt, enc):
    global ok, skip, blob
    if off in seen:
        return
    seen.add(off)
    rva = off2rva(off)
    if rva is None:
        skip += 1; return
    try:
        e = txt.encode('gbk') if enc == 0 else txt.encode('utf-16le')
    except Exception:
        skip += 1; return
    cap = cap_ansi(off) if enc == 0 else cap_utf16(off)
    if cap <= 0 or len(e) > cap:
        report.append((hex(off), txt, len(e), cap)); skip += 1; return
    blob += struct.pack('<IHB', rva, len(e), enc) + e
    ok += 1

# 1) 既有 ANSI 表
for k, txt in json.load(open(os.path.join(TEMP, "patch_table.json"), encoding="utf-8")).items():
    off = int(k, 16) if k.lower().startswith("0x") else int(k)
    add(off, SHORT.get(off, txt), 0)

# 2) 既有 UTF-16 表
for off, txt in sorted(U16.items()):
    add(off, txt, 1)

# 3) 第二轮补齐（带原文校验）
bad = []
for off, (orig, zh) in sorted(EXTRA.items()):
    act = zstr(off)
    if act is None or act.strip() != orig.strip():
        bad.append((hex(off), orig, act))
        continue
    add(off, zh, 0)

# 4) samples 系列自动翻译
SAMP = re.compile(rb'^(\d+) samples(?: \(([^)]*)\))?$')
for m in re.finditer(rb'(?<=\x00)[\x20-\x7e]{4,}(?=\x00)', raw):
    s = m.group()
    mm = SAMP.match(s)
    if not mm:
        continue
    n = mm.group(1).decode()
    inner = mm.group(2)
    if inner:
        body = inner.decode().replace('@48000Hz', '@48k').replace('@44100Hz', '@44.1k')
        zh = "%s 采样(%s)" % (n, body)
    else:
        zh = "%s 采样" % n
    add(m.start(), zh, 0)

print("打包成功 %d 条，跳过 %d 条" % (ok, skip))
if bad:
    print("原文不匹配 %d 条:" % len(bad))
    for b in bad[:40]:
        print("  ", b)
if report:
    print("超长跳过 %d 条:" % len(report))
    for r in report[:80]:
        print("  ", r)
b64 = base64.b64encode(bytes(blob)).decode()
open(os.path.join(TEMP, "patch_blob_v4_b64.txt"), "w", encoding="utf-8").write(b64)
print("blob %d 字节, base64 %d 字符" % (len(blob), len(b64)))
