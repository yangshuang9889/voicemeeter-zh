# -*- coding: utf-8 -*-
"""通用单字节修改存活测试：判断完整性校验覆盖哪些区段。"""
import os, sys, time, struct, subprocess, ctypes

ORIG = r"C:\Program Files (x86)\VB\Voicemeeter\voicemeeter8x64.exe1"
TEST = r"C:\Program Files (x86)\VB\Voicemeeter\vmtest.exe"

def kill():
    subprocess.run(["taskkill", "/F", "/IM", "vmtest.exe"], capture_output=True)

def build(edits):
    b = bytearray(open(ORIG, 'rb').read())
    for off, val in edits:
        b[off] = val
    # 重算 PE 校验和
    pe = struct.unpack_from('<I', b, 0x3c)[0]
    ck = pe + 24 + 64
    struct.pack_into('<I', b, ck, 0)
    s = 0
    for i in range(0, len(b), 2):
        w = b[i] | (b[i+1] << 8 if i+1 < len(b) else 0)
        s += w
        s = (s & 0xffff) + (s >> 16)
    s = (s & 0xffff) + (s >> 16)
    struct.pack_into('<I', b, ck, ((s + len(b)) & 0xffffffff))
    return bytes(b)

def test(data, wait=6):
    kill(); time.sleep(0.5)
    open(TEST, 'wb').write(data)
    k32 = ctypes.windll.kernel32
    si = subprocess.STARTUPINFO()
    p = subprocess.Popen([TEST], startupinfo=si)
    t0 = time.time()
    alive = None
    while time.time() - t0 < wait:
        if p.poll() is not None:
            alive = False
            break
        time.sleep(0.3)
    else:
        alive = True
    rc = p.poll()
    if alive:
        p.kill(); p.wait()
    kill()
    return alive, rc, round(time.time()-t0, 2)

if __name__ == "__main__":
    cases = [
        ("baseline-空补丁", []),
        ("A .text CC填充 0x6b8", [(0x6b8, 0x90)]),
        ("B .text CC填充 0x1494bc", [(1348796, 0x90)]),
        ("C .rsrc 1900000^1", [(1900000, open(ORIG,'rb').read()[1900000] ^ 1)]),
        ("D .data 1515000^1", [(1515000, open(ORIG,'rb').read()[1515000] ^ 1)]),
        ("E .rdata 1400000^1", [(1400000, open(ORIG,'rb').read()[1400000] ^ 1)]),
    ]
    raw = open(ORIG, 'rb').read()
    for name, edits in cases:
        d = build(edits)
        a, rc, dt = test(d)
        print("%-28s -> %s  exit=%s  用时%.2fs" % (name, "OK存活" if a else "CRASH", rc, dt), flush=True)
