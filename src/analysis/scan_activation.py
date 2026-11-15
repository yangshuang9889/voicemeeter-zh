# -*- coding: utf-8 -*-
"""解析 v4 blob，列出已覆盖 rva；并扫描激活对话框区间未覆盖的 ASCII 串。"""
import base64, struct, os, re
TEMP = os.path.dirname(os.path.abspath(__file__))
EXE = r"C:\Program Files (x86)\VB\Voicemeeter\voicemeeter8x64.exe"

b = base64.b64decode(open(os.path.join(TEMP, "patch_blob_v4_b64.txt")).read().strip())
pos = 0
covered = {}
while pos + 7 <= len(b):
    rva, ln, enc = struct.unpack('<IHB', b[pos:pos+7]); pos += 7
    data = b[pos:pos+ln]; pos += ln
    covered[rva] = enc
print("v4 覆盖条目:", len(covered), "rva 范围 0x%x - 0x%x" % (min(covered), max(covered)))

data = open(EXE, 'rb').read()

# PE 节 -> 偏移映射函数（这里直接用之前结论：.rdata raw 0x149800 VA 0x14b000 等，用一段通用实现）

# 解析节表
pe = struct.unpack_from('<I', data, 0x3c)[0]
nsec = struct.unpack_from('<H', data, pe + 6)[0]
opt = pe + 24
sizeopt = struct.unpack_from('<H', data, pe + 20)[0]
secs = []
base = opt + sizeopt
for i in range(nsec):
    off = base + i * 40
    name = data[off:off+8].rstrip(b'\x00').decode('latin1')
    vsize, va, rawsize, rawptr = struct.unpack_from('<IIII', data, off + 8)
    secs.append((name, va, vsize, rawptr, rawsize))

def rva2off(rva):
    for name, va, vs, rp, rs in secs:
        if va <= rva < va + max(vs, rs):
            return rp + (rva - va)
    return None

def off2rva(o):
    for name, va, vs, rp, rs in secs:
        if rp <= o < rp + rs:
            return va + (o - rp)
    return None

# 扫描区间内的 ASCII zstring
LO, HI = 0x14e000, 0x14f700
lo = rva2off(LO); hi = rva2off(HI)
print("扫描 off 0x%x-0x%x" % (lo, hi))
i = lo
out = []
while i < hi:
    m = re.compile(rb'[ -~]{4,}').match(data, i)
    if m:
        s = m.group().decode('ascii')
        rva = off2rva(i)
        out.append((rva, i, s))
        i = m.end() + 1
    else:
        i += 1
print("区间内 zstring:", len(out))
for rva, off, s in out:
    mark = "已覆盖" if rva in covered else "缺"
    print("0x%06x\t%s\t%s" % (rva, mark, s[:100]))

