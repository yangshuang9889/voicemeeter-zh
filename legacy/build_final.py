# -*- coding: utf-8 -*-
"""生成最终汉化版 voicemeeter8x64.exe（等长原地替换，超长条目改用更短译文）。"""
import struct, os, json, importlib.util

ORIG = r"C:\Program Files (x86)\VB\Voicemeeter\voicemeeter8x64.exe1"
TEMP = r"C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2Siy4T87X5Sx6qEfhnB8hbI\workspace\conv_7d5c914e13b74cd1a41a32b2f23b1221\temp"
OUT = r"C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2Siy4T87X5Sx6qEfhnB8hbI\workspace\conv_7d5c914e13b74cd1a41a32b2f23b1221\output\voicemeeter_cn"

SHORT = {
    0x15a9a0: '复制门限',
    0x15aa40: '保存门限',
    0x15a820: '单',
    0x15a830: '单',
    0x1599d8: 'A1声道#%i', 0x1599f8: 'A2声道#%i', 0x159a18: 'A3声道#%i',
    0x159a38: 'A4声道#%i', 0x159a58: 'A5声道#%i', 0x159a78: 'B1声道#%i',
    0x159a98: 'B2声道#%i', 0x159ab8: 'B3声道#%i',
}

def pe_checksum(b):
    pe = struct.unpack_from('<I', b, 0x3c)[0]
    ck = pe + 24 + 64
    struct.pack_into('<I', b, ck, 0)
    s = 0
    for i in range(0, len(b), 2):
        w = b[i] | ((b[i+1] << 8) if i+1 < len(b) else 0)
        s += w
        s = (s & 0xffff) + (s >> 16)
    s = (s & 0xffff) + (s >> 16)
    struct.pack_into('<I', b, ck, (s + len(b)) & 0xffffffff)
    return ck, struct.unpack_from('<I', b, ck)[0]

def main():
    spec = importlib.util.spec_from_file_location("bs", TEMP + r"\bisect1.py")
    bs = importlib.util.module_from_spec(spec); spec.loader.exec_module(bs)
    raw = open(ORIG, 'rb').read()
    b = bytearray(raw)
    ok = 0; fail = []
    table = []
    for off, txt in bs.items:
        if off in SHORT:
            txt = SHORT[off]
        e = txt.encode('gbk')
        end = off
        while raw[end] != 0:
            end += 1
        cap = end - off
        if len(e) > cap:
            fail.append((hex(off), raw[off:end].decode('latin1'), txt, cap, len(e)))
            continue
        old = raw[off:end].decode('latin1')
        b[off:off+cap+1] = e + b'\0'*(cap-len(e)+1)
        table.append((hex(off), old, txt, cap))
        ok += 1
    if len(b) != len(raw):
        raise SystemExit("文件长度变化，终止：%d -> %d" % (len(raw), len(b)))
    ckoff, ckval = pe_checksum(b)
    os.makedirs(OUT, exist_ok=True)
    dst = os.path.join(OUT, "voicemeeter8x64.exe")
    open(dst, 'wb').write(bytes(b))
    print("写入:", dst)
    print("大小: %d (原 %d)" % (len(b), len(raw)))
    print("成功替换: %d 条，失败: %d 条" % (ok, len(fail)))
    for f in fail: print("  失败:", f)
    print("PE 校验和: 0x%08x" % ckval)
    with open(os.path.join(OUT, "汉化对照表.csv"), 'w', encoding='utf-8-sig', newline='') as f:
        f.write("偏移,原文,译文,可用字节\n")
        for row in table:
            f.write('"%s","%s","%s",%d\n' % (row[0], row[1].replace('"', '""'), row[2], row[3]))
    print("对照表已更新")

if __name__ == "__main__":
    main()
