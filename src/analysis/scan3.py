# -*- coding: utf-8 -*-
"""正确版本：按文件偏移扫描激活对话框区间，标注 blob 覆盖情况。"""
import base64, struct, os, re
TEMP = os.path.dirname(os.path.abspath(__file__))
EXE = r"C:\Program Files (x86)\VB\Voicemeeter\voicemeeter8x64.exe"
data = open(EXE, 'rb').read()

pe = struct.unpack_from('<I', data, 0x3c)[0]
nsec = struct.unpack_from('<H', data, pe + 6)[0]
sizeopt = struct.unpack_from('<H', data, pe + 20)[0]
base = pe + 24 + sizeopt
secs = []
for i in range(nsec):
    off = base + i * 40
    name = data[off:off+8].rstrip(b'\x00').decode('latin1')
    vsize, va, rawsize, rawptr = struct.unpack_from('<IIII', data, off + 8)
    secs.append((name, va, vsize, rawptr, rawsize))

def off2rva(o):
    for name, va, vs, rp, rs in secs:
        if rp <= o < rp + rs:
            return va + (o - rp)
    return None

b = base64.b64decode(open(os.path.join(TEMP, "patch_blob_v4_b64.txt")).read().strip())
pos = 0; covered = {}
while pos + 7 <= len(b):
    rva, ln, enc = struct.unpack('<IHB', b[pos:pos+7]); pos += 7
    covered[rva] = b[pos:pos+ln]; pos += ln

LO, HI = 0x14b000, 0x150500
i = LO
pat = re.compile(rb'[ -~]{4,}')
rows = []
while i < HI:
    m = pat.match(data, i)
    if m:
        rows.append((i, m.group().decode('ascii')))
        i = m.end() + 1
    else:
        i += 1
print("区间 zstring:", len(rows))
for off, s in rows:
    rva = off2rva(off)
    if rva in covered:
        try: zh = covered[rva].decode('gbk', 'replace')
        except: zh = '?'
        print("0x%06x COVERED -> %s" % (off, zh))
    else:
        print("0x%06x MISSING  %s" % (off, s))
