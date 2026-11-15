# -*- coding: utf-8 -*-
"""从 MENU 资源原始字节中提取所有 UTF-16 文本串（含偏移/rva）。"""
import struct, re
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

def off2rva(o):
    for va, vs, rp, rs in secs:
        if rp <= o < rp + rs:
            return va + (o - rp)
    return None

MO, SIZE = 0x1c7770, 472
blob = data[MO:MO+SIZE]
print("前 32 字节:", blob[:32].hex())
# 找 utf16 串
i = 0
while i < SIZE - 3:
    # 尝试解码开始
    j = i
    chars = []
    while j + 1 < SIZE:
        ch = blob[j:j+2]
        if ch == b'\x00\x00':
            break
        try:
            c = ch.decode('utf-16-le')
        except Exception:
            break
        if not (c.isprintable() or c == ' '):
            break
        chars.append(c)
        j += 2
    s = ''.join(chars)
    if len(s) >= 2:
        print("off=0x%06x rva=0x%06x len=%2d  %r" % (MO + i, off2rva(MO + i), len(s), s))
        i = j + 2
    else:
        i += 1
