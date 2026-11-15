# -*- coding: utf-8 -*-
"""二分定位导致崩溃的汉化词条。用法: python bisect1.py start end"""
import json, os, sys, struct, hashlib, subprocess, time, ctypes

T = r"C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2Siy4T87X5Sx6qEfhnB8hbI\workspace\conv_7d5c914e13b74cd1a41a32b2f23b1221\temp"
ORIG = r"C:\Program Files (x86)\VB\Voicemeeter\voicemeeter8x64.exe1"
TEST = r"C:\Program Files (x86)\VB\Voicemeeter\vmtest.exe"

orig = open(ORIG, 'rb').read()
cand = json.load(open(os.path.join(T, "ui_candidates.json"), encoding='utf-8'))
lm = {c["off"]: c["t"] for c in cand}
ptab = json.load(open(os.path.join(T, "patch_table.json"), encoding='utf-8'))
items = [(int(k), v) for k, v in ptab.items()]


def pe_checksum(data):
    b = bytearray(data)
    pe = struct.unpack_from('<I', b, 0x3c)[0]
    opt = pe + 24
    b[opt+64:opt+68] = b'\0\0\0\0'
    s = 0
    for i in range(0, len(b)-1, 2):
        s += struct.unpack_from('<H', b, i)[0]
        s = (s & 0xFFFF) + (s >> 16)
    if len(b) % 2:
        s += b[-1]
        s = (s & 0xFFFF) + (s >> 16)
    s = (s & 0xFFFF) + (s >> 16)
    return s + len(b)


def build(sub):
    b = bytearray(orig)
    for fo, cn in sub:
        tt = lm.get(fo)
        if tt is None:
            e = orig.index(b'\0', fo)
            tt = e - fo + 1
        g = cn.encode('gbk')
        if len(g) > tt:
            continue
        b[fo:fo+tt] = g + b'\0' * (tt - len(g))
    ck = pe_checksum(b)
    pe = struct.unpack_from('<I', b, 0x3c)[0]
    struct.pack_into('<I', b, pe+24+64, ck)
    return bytes(b)


def test(data, wait=4.0):
    with open(TEST, 'wb') as f:
        f.write(data)
    k32 = ctypes.windll.kernel32
    old = k32.SetErrorMode(0x0001 | 0x0002 | 0x8000)
    try:
        p = subprocess.Popen([TEST], cwd=os.path.dirname(TEST))
    finally:
        k32.SetErrorMode(old)
    t0 = time.time()
    rc = None
    while time.time() - t0 < wait:
        rc = p.poll()
        if rc is not None:
            break
        time.sleep(0.2)
    if rc is None:
        subprocess.run(["taskkill", "/F", "/PID", str(p.pid)], capture_output=True)
        return "OK", 0, time.time()-t0
    return "CRASH", rc & 0xFFFFFFFF, time.time()-t0


if __name__ == "__main__":
    s, e = int(sys.argv[1]), int(sys.argv[2])
    sub = items[s:e]
    st, rc, el = test(build(sub))
    print("[%d:%d] n=%d -> %s rc=0x%08X t=%.2fs" % (s, e, len(sub), st, rc, el))
    for i in range(s, min(e, s+3)):
        print("   ", i, hex(items[i][0]), repr(items[i][1]))
    try:
        os.remove(TEST)
    except Exception:
        pass
