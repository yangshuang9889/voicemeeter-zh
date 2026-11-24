# -*- coding: utf-8 -*-
"""生成多版本补丁 blob（v9）：以「英文原文 -> 中文译文」为桥梁，跨 exe 自动迁移。

思路：
  1. 从 Potato x64 原版副本 + 既有 patch_table / U16 / EXTRA 反查得到 原文->译文 字典；
  2. 对每个目标 exe 独立解析 PE 节表，扫描 zstring 常量池，命中原文即生成补丁条目；
  3. blob 条目格式与原版一致：[rva(4)+len(2)+enc(1)+bytes]，enc=0 ANSI(GBK) / 1 UTF-16LE；
  4. 每套 blob 单独 gzip 压缩后再 base64，供 C# 启动器内嵌，减少体积。
"""
import base64
import gzip
import io
import json
import os
import re
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from utf16_zh import U16
from gen_blob import SHORT
from extra_zh import EXTRA
from extra_zh2 import MULTI

EXTRA.update(MULTI)

VBDIR = r"C:\Program Files (x86)\VB\Voicemeeter"
ORIG = os.path.join(VBDIR, "voicemeeter8x64.exe1")

TARGETS = [
    ("potato_x64", "voicemeeter8x64.exe"),
    ("potato_x86", "voicemeeter8.exe"),
    ("banana_x64", "voicemeeterpro_x64.exe"),
    ("banana_x86", "voicemeeterpro.exe"),
    ("vm_x64", "voicemeeter_x64.exe"),
    ("vm_x86", "voicemeeter.exe"),
]


class PE(object):
    def __init__(self, path):
        self.path = path
        self.raw = open(path, "rb").read()
        pe = struct.unpack_from("<I", self.raw, 0x3C)[0]
        self.pe = pe
        nsec = struct.unpack_from("<H", self.raw, pe + 6)[0]
        optsz = struct.unpack_from("<H", self.raw, pe + 20)[0]
        self.magic = struct.unpack_from("<H", self.raw, pe + 24)[0]
        so = pe + 24 + optsz
        self.secs = []
        for i in range(nsec):
            o = so + i * 40
            name = self.raw[o:o + 8].rstrip(b"\x00").decode("ascii", "replace")
            vs, va, rs, ra = struct.unpack_from("<IIII", self.raw, o + 8)
            self.secs.append((name, ra, rs, va))

    def off2rva(self, off):
        for name, ra, rs, va in self.secs:
            if ra <= off < ra + rs:
                return off - ra + va
        return None

    def in_code(self, off):
        for name, ra, rs, va in self.secs:
            if ra <= off < ra + rs:
                return name
        return None

    def cap_ansi(self, off):
        p = self.raw.find(b"\x00", off)
        return p - off

    def cap_utf16(self, off):
        j = off
        while j + 1 < len(self.raw):
            if self.raw[j] == 0 and self.raw[j + 1] == 0:
                return j - off
            j += 2
        return -1


def read_ansi(pe, off):
    p = pe.raw.find(b"\x00", off)
    if p <= off:
        return None
    try:
        return pe.raw[off:p].decode("ascii")
    except Exception:
        return None


def read_utf16(pe, off):
    j = off
    buf = bytearray()
    while j + 1 < len(pe.raw):
        if pe.raw[j] == 0 and pe.raw[j + 1] == 0:
            break
        buf += pe.raw[j:j + 2]
        j += 2
    if len(buf) < 4:
        return None
    try:
        return buf.decode("utf-16le")
    except Exception:
        return None


def build_dicts():
    src = PE(ORIG)
    ansi_map = {}
    utf_map = {}

    tbl = json.load(open(os.path.join(HERE, "patch_table.json"), encoding="utf-8"))
    for k, zh in tbl.items():
        off = int(k, 16) if k.lower().startswith("0x") else int(k)
        en = read_ansi(src, off)
        if not en:
            continue
        zh = SHORT.get(off, zh)
        key = en.strip()
        if key and key not in ansi_map:
            ansi_map[key] = zh

    for off, zh in sorted(U16.items()):
        en = read_utf16(src, off)
        if not en:
            continue
        key = en.strip()
        if key and key not in utf_map:
            utf_map[key] = zh

    for off, pair in sorted(EXTRA.items()):
        try:
            en, zh = pair
        except Exception:
            continue
        key = (en or "").strip()
        if key and key not in ansi_map:
            ansi_map[key] = zh

    return ansi_map, utf_map


SAMP = re.compile(r"^(\d+) samples(?: \(([^)]*)\))?$")


def samples_zh(m):
    n = m.group(1)
    inner = m.group(2)
    if inner:
        body = inner.replace("@48000Hz", "@48k").replace("@44100Hz", "@44.1k")
        return "%s 采样(%s)" % (n, body)
    return "%s 采样" % n


def gen(pe, ansi_map, utf_map):
    blob = bytearray()
    ok = skip_len = 0
    seen = set()
    stats = {}

    def add(off, zh, enc):
        nonlocal ok, skip_len, blob
        if off in seen:
            return
        seen.add(off)
        rva = pe.off2rva(off)
        if rva is None:
            return
        try:
            data = zh.encode("gbk") if enc == 0 else zh.encode("utf-16le")
        except Exception:
            return
        cap = pe.cap_ansi(off) if enc == 0 else pe.cap_utf16(off)
        if cap <= 0 or len(data) > cap:
            skip_len += 1
            return
        blob += struct.pack("<IHB", rva, len(data), enc) + data
        ok += 1
        sec = pe.in_code(off) or "?"
        stats[sec] = stats.get(sec, 0) + 1

    # ANSI 常量池
    for m in re.finditer(rb"(?<=\x00)[\x20-\x7e]{2,}(?=\x00)", pe.raw):
        off = m.start()
        try:
            text = m.group().decode("ascii")
        except Exception:
            continue
        key = text.strip()
        if key in ansi_map:
            add(off, ansi_map[key], 0)
            continue
        sm = SAMP.match(key)
        if sm:
            add(off, samples_zh(sm), 0)

    # UTF-16LE 常量池
    for m in re.finditer(rb"(?<=\x00\x00)(?:[\x20-\x7e]\x00){2,}(?=\x00\x00)", pe.raw):
        off = m.start()
        try:
            text = m.group().decode("utf-16le")
        except Exception:
            continue
        key = text.strip()
        if key in utf_map:
            add(off, utf_map[key], 1)

    return bytes(blob), ok, skip_len, stats


def gz_b64(data):
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=9, mtime=0) as f:
        f.write(data)
    return base64.b64encode(buf.getvalue()).decode()


def main():
    ansi_map, utf_map = build_dicts()
    print("字典: ANSI %d 条, UTF16 %d 条" % (len(ansi_map), len(utf_map)))

    out = {}
    summary = []
    for key, fname in TARGETS:
        path = os.path.join(VBDIR, fname)
        if not os.path.exists(path):
            print("[MISS] %s -> %s" % (key, fname))
            continue
        pe = PE(path)
        blob, ok, skip, stats = gen(pe, ansi_map, utf_map)
        b64 = gz_b64(blob)
        out[key] = {"file": fname, "b64": b64, "count": ok, "raw": len(blob)}
        summary.append((key, fname, len(pe.raw), ok, skip, len(blob), len(b64), stats))
        print("[OK] %-11s %-24s exe=%9d 条目=%4d 超长跳过=%3d blob=%6d gz_b64=%6d %s"
              % (key, fname, len(pe.raw), ok, skip, len(blob), len(b64), stats))

    with open(os.path.join(HERE, "patch_blobs_multi.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("\n已写出 patch_blobs_multi.json, 版本数=%d" % len(out))


if __name__ == "__main__":
    main()
