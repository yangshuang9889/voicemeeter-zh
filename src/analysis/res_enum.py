# -*- coding: utf-8 -*-
"""枚举 PE 资源：RT_BITMAP / RCDATA 等，输出数量与大小。"""
import struct, os, collections
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

def rva2off(rva):
    for name, va, vs, rp, rs in secs:
        if va <= rva < va + max(vs, rs):
            return rp + (rva - va)
    return None

magic = struct.unpack_from('<H', data, pe + 24)[0]
ddoff = pe + 24 + (112 if magic == 0x20b else 96)
rsrc_rva, rsrc_size = struct.unpack_from('<II', data, ddoff + 2 * 8)
print("资源目录 RVA=0x%x size=0x%x" % (rsrc_rva, rsrc_size))
rb = rva2off(rsrc_rva)

def entries(dir_off):
    named, ids = struct.unpack_from('<HH', data, dir_off + 12)
    n = named + ids
    out = []
    for i in range(n):
        nameid, target = struct.unpack_from('<II', data, dir_off + 16 + i * 8)
        out.append((nameid, target))
    return out

def is_dir(nameid):
    return bool(nameid & 0x80000000)

RT = {1:'CURSOR',2:'BITMAP',3:'ICON',4:'MENU',5:'DIALOG',6:'STRING',9:'ACCEL',10:'RCDATA',12:'GROUP_CURSOR',14:'GROUP_ICON',16:'VERSION',23:'HTML',24:'MANIFEST'}
total = 0
for nameid, tgt in entries(rb):
    rtype = nameid & 0x7FFFFFFF
    tname = RT.get(rtype, '#%d' % rtype)
    items = entries(rb + (tgt & 0x7FFFFFFF))
    print("类型 %s: %d 项" % (tname, len(items)))
    for nid, t2 in items:
        if not is_dir(nid):
            continue
        langs = entries(rb + (t2 & 0x7FFFFFFF))
        for lid, t3 in langs:
            if is_dir(t3): continue
            doff = rb + t3
            drva, dsize = struct.unpack_from('<II', data, doff)
            o = rva2off(drva)
            head = data[o:o+8]
            kind = 'PNG' if head[:4] == b'\x89PNG' else ('BMP' if head[:2] == b'BM' else 'other')
            total += 1
            if rtype in (2, 10) or dsize > 200000:
                print("   %s id=%d size=%d (%s) head=%s" % (tname, nid & 0x7FFFFFFF, dsize, kind, head[:4].hex()))
print("资源项总数", total)

