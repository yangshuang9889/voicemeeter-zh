# -*- coding: utf-8 -*-
"""精确盘点：列出所有 ANSI / UTF-16 串，标记覆盖状态，导出未覆盖清单。"""
import json, os, re, struct, sys

TEMP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TEMP)
from utf16_zh import U16
from extra_zh import EXTRA
from extra_zh2 import MULTI
EXTRA2 = dict(EXTRA); EXTRA2.update(MULTI)

ORIG = r"C:\Program Files (x86)\VB\Voicemeeter\voicemeeter8x64.exe1"
raw = open(ORIG, 'rb').read()

pt = json.load(open(os.path.join(TEMP, "patch_table.json"), encoding="utf-8"))
PT = {}
for k, v in pt.items():
    off = int(k, 16) if k.lower().startswith("0x") else int(k)
    PT[off] = v

covered = set(PT) | set(U16) | set(EXTRA2)

# ---- ANSI 扫描 ----
ansi = []
for m in re.finditer(rb'[\x20-\x7e]{4,}', raw):
    s, e = m.start(), m.end()
    # 必须前后为 NUL 或边界
    if s > 0 and raw[s-1] != 0:
        continue
    if e < len(raw) and raw[e] != 0:
        continue
    ansi.append((s, m.group().decode('ascii')))

# ---- UTF-16 扫描 ----
u16 = []
i = 0
n = len(raw)
while i + 8 < n:
    if raw[i] == 0 and raw[i+1] == 0:
        j = i + 2
        buf = []
        okc = True
        while j + 1 < n:
            if raw[j] == 0 and raw[j+1] == 0:
                break
            if raw[j+1] != 0 or raw[j] < 0x20 or raw[j] > 0x7e:
                okc = False
                break
            buf.append(chr(raw[j]))
            j += 2
        if okc and len(buf) >= 4:
            u16.append((i+2, ''.join(buf)))
            i = j + 2
            continue
    i += 1

KEY = ['related to this computer', 'Ultimate Virtual Audio Mixer', 'Participation',
       'ERROR_BADRESPONSECODE', 'web-shop', 'hardware', 'Buy', 'level']

out = []
out.append("=== ANSI 总数 %d, UTF16 总数 %d, 已覆盖键 %d ===" % (len(ansi), len(u16), len(covered)))
out.append("")
out.append("### 关键串定位")
for k in KEY:
    out.append("-- %s" % k)
    for off, s in ansi:
        if k.lower() in s.lower():
            out.append("   ANSI 0x%x %s  covered=%s" % (off, repr(s), off in covered))
    for off, s in u16:
        if k.lower() in s.lower():
            out.append("   U16  0x%x %s  covered=%s" % (off, repr(s), off in covered))

def is_ui(s):
    if any(x in s for x in ('%s', '%i', '%0.')):
        return False
    if '/' in s or '\\' in s:
        return False
    if re.search(r'\.(exe|dll|xml|wav|mp3|txt|log|sys|drv|ini|dat|dmp|cab)$', s, re.I):
        return False
    if s.startswith('VB-') or 'WND-CLASS' in s or s.startswith('[VB2CTL]'):
        return False
    if re.match(r'^[a-z]+(?:[A-Z][a-z0-9]*)+$', s):  # 驼峰内部ID
        return False
    if len(s) < 5:
        return False
    return True

miss_ansi = [(o, s) for o, s in ansi if o not in covered and is_ui(s)]
miss_u16 = [(o, s) for o, s in u16 if o not in covered and is_ui(s)]

out.append("")
out.append("### 未覆盖 ANSI %d 条" % len(miss_ansi))
for o, s in miss_ansi:
    out.append("0x%x\t%s" % (o, s))
out.append("")
out.append("### 未覆盖 UTF16 %d 条" % len(miss_u16))
for o, s in miss_u16:
    out.append("0x%x\t%s" % (o, s))

open(os.path.join(TEMP, "gap2.txt"), 'w', encoding='utf-8').write('\n'.join(out))
print("ANSI %d / UTF16 %d；未覆盖 ANSI %d / UTF16 %d" % (len(ansi), len(u16), len(miss_ansi), len(miss_u16)))
