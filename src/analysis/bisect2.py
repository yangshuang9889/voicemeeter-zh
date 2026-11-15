# -*- coding: utf-8 -*-
"""二分定位：应用 patch_table 指定区间，实测 20 秒存活。"""
import sys, os, time, struct, shutil, subprocess, importlib.util

TEMP = os.path.dirname(os.path.abspath(__file__))
ORIG = r"C:\Program Files (x86)\VB\Voicemeeter\voicemeeter8x64.exe1"
TEST = r"C:\Program Files (x86)\VB\Voicemeeter\vmtest.exe"

SHORT = {
    0x15a9a0: '复制门限', 0x15aa40: '保存门限', 0x15a820: '单', 0x15a830: '单',
    0x1599d8: 'A1声道#%i', 0x1599f8: 'A2声道#%i', 0x159a18: 'A3声道#%i',
    0x159a38: 'A4声道#%i', 0x159a58: 'A5声道#%i', 0x159a78: 'B1声道#%i',
    0x159a98: 'B2声道#%i', 0x159ab8: 'B3声道#%i',
}

def checksum(b):
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

def items():
    spec = importlib.util.spec_from_file_location("bs", os.path.join(TEMP, "bisect1.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m.items

def build(sel):
    raw = open(ORIG, 'rb').read()
    b = bytearray(raw)
    for off, txt in sel:
        txt = SHORT.get(off, txt)
        e = txt.encode('gbk')
        end = off
        while raw[end] != 0:
            end += 1
        cap = end - off
        if len(e) > cap:
            print("  超长跳过", hex(off)); continue
        b[off:off+cap+1] = e + b'\0'*(cap-len(e)+1)
    assert len(b) == len(raw)
    checksum(b)
    return bytes(b)

def test(data, secs=20):
    subprocess.run(["taskkill", "/F", "/IM", "vmtest.exe"], capture_output=True)
    time.sleep(0.5)
    open(TEST, 'wb').write(data)
    p = subprocess.Popen([TEST]); t0 = time.time()
    while time.time()-t0 < secs:
        if p.poll() is not None:
            rc = p.returncode & 0xffffffff
            subprocess.run(["taskkill", "/F", "/IM", "vmtest.exe"], capture_output=True)
            return False, rc, time.time()-t0
        time.sleep(0.3)
    subprocess.run(["taskkill", "/F", "/IM", "vmtest.exe"], capture_output=True)
    return True, None, time.time()-t0

def main():
    a, b_ = int(sys.argv[1]), int(sys.argv[2])
    its = items()
    sel = its[a:b_]
    print("区间 [%d,%d) 共 %d 条" % (a, b_, len(sel)))
    d = build(sel)
    ok, rc, dt = test(d)
    print("结果: %s  exit=%s  %.1fs" % ("OK存活" if ok else "CRASH", rc, dt))

if __name__ == "__main__":
    main()
