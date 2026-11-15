# -*- coding: utf-8 -*-
"""导出 RCDATA 资源并检测类型。"""
import struct, os
EXE = r"C:\Program Files (x86)\VB\Voicemeeter\voicemeeter8x64.exe"
TEMP = os.path.dirname(os.path.abspath(__file__))
data = open(EXE, 'rb').read()
pe = struct.unpack_from('<I', data, 0x3c)[0]
nsec = struct.unpack_from('<H', data, pe + 6)[0]
sizeopt = struct.unpack_from('<H', data, pe + 20)[0]
base = pe + 24 + sizeopt
secs = []
for i in range(nsec):
    off = base + i * 40
    vsize, va, rawsize, rawptr = struct.unpack_from('<IIII', data, off + 8)
    secs.append((va, vsize, rawptr, rawsize))

def rva2off(rva):
    for va, vs, rp, rs in secs:
        if va <= rva < va + max(vs, rs):
            return rp + (rva - va)
    return None

magic = struct.unpack_from('<H', data, pe + 24)[0]
ddoff = pe + 24 + (112 if magic == 0x20b else 96)
rsrc_rva, _ = struct.unpack_from('<II', data, ddoff + 16)
rb = rva2off(rsrc_rva)

def entries(dir_off):
    named, ids = struct.unpack_from('<HH', data, dir_off + 12)
    return [struct.unpack_from('<II', data, dir_off + 16 + i * 8) for i in range(named + ids)]

for nameid, tgt in entries(rb):
    rtype = nameid & 0x7FFFFFFF
    if rtype not in (10, 4):
        continue
    print("== 类型", rtype)
    for nid, t2 in entries(rb + (tgt & 0x7FFFFFFF)):
        for lid, t3 in entries(rb + (t2 & 0x7FFFFFFF)):
            if t3 & 0x80000000:
                continue
            drva, dsize = struct.unpack_from('<II', data, rb + t3)
            o = rva2off(drva)
            head = data[o:o+8]
            print("  id=%s size=%d head=%s ascii=%r" % (nid & 0x7FFFFFFF, dsize, head.hex(), data[o:o+40]))
