# -*- coding: utf-8 -*-
"""解析 RT_MENU 资源 9040，输出所有项文本及在文件中的偏移/rva。"""
import struct, os
EXE = r"C:\Program Files (x86)\VB\Voicemeeter\voicemeeter8x64.exe"
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

def off2rva(o):
    for va, vs, rp, rs in secs:
        if rp <= o < rp + rs:
            return va + (o - rp)
    return None

magic = struct.unpack_from('<H', data, pe + 24)[0]
ddoff = pe + 24 + (112 if magic == 0x20b else 96)
rsrc_rva, _ = struct.unpack_from('<II', data, ddoff + 16)
rb = rva2off(rsrc_rva)

def entries(dir_off):
    named, ids = struct.unpack_from('<HH', data, dir_off + 12)
    return [struct.unpack_from('<II', data, dir_off + 16 + i * 8) for i in range(named + ids)]

mo = None
for nameid, tgt in entries(rb):
    if (nameid & 0x7FFFFFFF) != 4:
        continue
    for nid, t2 in entries(rb + (tgt & 0x7FFFFFFF)):
        for lid, t3 in entries(rb + (t2 & 0x7FFFFFFF)):
            if t3 & 0x80000000: continue
            drva, dsize = struct.unpack_from('<II', data, rb + t3)
            mo = rva2off(drva)
            msize = dsize
print("MENU off=0x%x size=%d rva=0x%x" % (mo, msize, off2rva(mo)))

pos = mo + 4 + 4  # MENUHEADER: version(2)+headerSize(2)+ 然后第一项从 mo+4 开始？标准：version, headerSize, 然后 items
pos = mo + 4

def read_items(p, depth=0, end=None):
    out = []
    while True:
        if end and p >= end: break
        flags, idv = struct.unpack_from('<HH', data, p)
        p += 4
        if flags == 0 and idv == 0:
            # end of this menu
            out.append((p, None, None, None))
            return out, p
        MF_POPUP = 0x10
        if flags & MF_POPUP:
            # next WORD is offset to submenu, relative to start of menu resource
            sub = struct.unpack_from('<H', data, p)[0]
            p += 2
            out.append((p - 6, depth, idv, '<POPUP>'))
            subitems, _ = read_items(mo + sub, depth + 1)
            out.extend(subitems)
        else:
            # text: null-terminated utf16
            e = p
            while data[e:e+2] != b'\x00\x00':
                e += 2
            txt = data[p:e].decode('utf-16-le', 'replace')
            out.append((p - 4, depth, idv, (p, txt)))
            p = e + 2

items, _ = read_items(mo + 4, 0)
for item in items:
    start, depth, idv, payload = item
    if payload is None: continue
    if payload == '<POPUP>':
        print("  " * depth + "---- 子菜单 (id=%d) ----" % idv)
    else:
        p, txt = payload
        print("  " * depth + "[id=%-5d] off=0x%06x rva=0x%06x  %s" % (idv, p, off2rva(p), txt))
