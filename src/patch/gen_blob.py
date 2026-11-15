# -*- coding: utf-8 -*-
"""生成启动器所需的补丁数据 blob（base64）。"""
import json, os, struct, base64

TEMP = os.path.dirname(os.path.abspath(__file__))
ORIG = r"C:\Program Files (x86)\VB\Voicemeeter\voicemeeter8x64.exe1"

SHORT = {
    0x15a9a0: '复制门限', 0x15aa40: '保存门限', 0x15a820: '单', 0x15a830: '单',
    0x1599d8: 'A1声道#%i', 0x1599f8: 'A2声道#%i', 0x159a18: 'A3声道#%i',
    0x159a38: 'A4声道#%i', 0x159a58: 'A5声道#%i', 0x159a78: 'B1声道#%i',
    0x159a98: 'B2声道#%i', 0x159ab8: 'B3声道#%i',
}

raw = open(ORIG, 'rb').read()
pe = struct.unpack_from('<I', raw, 0x3c)[0]
nsec = struct.unpack_from('<H', raw, pe+6)[0]
so = pe + 24 + struct.unpack_from('<H', raw, pe+20)[0]
secs = []
for i in range(nsec):
    o = so + i*40
    vs, va, rs, ra = struct.unpack_from('<IIII', raw, o+8)
    secs.append((ra, rs, va))

def off2rva(off):
    for ra, rs, va in secs:
        if ra <= off < ra + rs:
            return off - ra + va
    return None

items = json.load(open(os.path.join(TEMP, "patch_table.json"), encoding="utf-8"))
blob = bytearray()
ok = skip = 0
report = []
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
    cap = raw.find(b'\0', off) - off
    if cap <= 0 or len(e) > cap:
        report.append((hex(off), txt, len(e), cap)); skip += 1; continue
    blob += struct.pack('<IH', rva, len(e)) + e
    ok += 1

print("打包成功 %d 条，跳过 %d 条" % (ok, skip))
for r in report:
    print("  超长跳过:", r)
b64 = base64.b64encode(bytes(blob)).decode()
open(os.path.join(TEMP, "patch_blob_b64.txt"), "w", encoding="utf-8").write(b64)
print("blob 长度 %d 字节, base64 %d 字符" % (len(blob), len(b64)))
