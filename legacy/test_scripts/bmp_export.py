# -*- coding: utf-8 -*-
"""导出所有 RT_BITMAP 资源为 bmp 文件，输出尺寸清单。"""
import struct, os
EXE = r"C:\Program Files (x86)\VB\Voicemeeter\voicemeeter8x64.exe"
TEMP = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(TEMP, 'bmp')
os.makedirs(OUT, exist_ok=True)
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
rb = rva2off(rsrc_rva)

def entries(dir_off):
    named, ids = struct.unpack_from('<HH', data, dir_off + 12)
    n = named + ids
    return [struct.unpack_from('<II', data, dir_off + 16 + i * 8) for i in range(n)]

rows = []
for nameid, tgt in entries(rb):
    rtype = nameid & 0x7FFFFFFF
    if rtype != 2:
        continue
    for nid, t2 in entries(rb + (tgt & 0x7FFFFFFF)):
        bid = nid & 0x7FFFFFFF
        for lid, t3 in entries(rb + (t2 & 0x7FFFFFFF)):
            if t3 & 0x80000000: continue
            drva, dsize = struct.unpack_from('<II', data, rb + t3)
            o = rva2off(drva)
            blob = data[o:o+dsize]
            bih_size = struct.unpack_from('<I', blob, 0)[0]
            w, h = struct.unpack_from('<ii', blob, 4)
            bpp = struct.unpack_from('<H', blob, 14)[0]
            clr = struct.unpack_from('<I', blob, 32)[0]
            palfmt = b'' if bpp > 8 else b'\x00' * 1
            bmpfile = b'BM' + struct.pack('<IHHI', 14 + dsize, 0, 0, 14 + bih_size + (clr * 4)) + blob
            fn = os.path.join(OUT, 'r%d_%dx%d_%dbpp.bmp' % (bid, w, h, bpp))
            open(fn, 'wb').write(bmpfile)
            rows.append((bid, w, h, bpp, dsize, os.path.basename(fn)))
rows.sort(key=lambda r: -r[4])
print("导出 %d 张" % len(rows))
for bid, w, h, bpp, sz, fn in rows[:40]:
    print("id=%-4d %dx%d %dbpp %d bytes %s" % (bid, w, h, bpp, sz, fn))
