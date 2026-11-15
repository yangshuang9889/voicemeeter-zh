# -*- coding: utf-8 -*-
"""列出目标 pid 全部窗口（含 prompt 对话框）并逐窗截图。"""
import ctypes, sys, os, importlib.util
from ctypes import wintypes
TEMP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TEMP)
spec = importlib.util.spec_from_file_location("sw", os.path.join(TEMP, "shot_win.py"))
sw = importlib.util.module_from_spec(spec); spec.loader.exec_module(sw)

pid = int(sys.argv[1]) if len(sys.argv) > 1 else 26496
u32 = ctypes.WinDLL('user32')
EP = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
hits = []
@EP
def cb(h, l):
    hits.append(h); return True
u32.EnumWindows(cb, 0)
from PIL import Image
for h in hits:
    p = wintypes.DWORD()
    u32.GetWindowThreadProcessId(h, ctypes.byref(p))
    if p.value != pid: continue
    cls = ctypes.create_unicode_buffer(256); u32.GetClassNameW(h, cls, 256)
    t = ctypes.create_unicode_buffer(512); u32.GetWindowTextW(h, t, 512)
    vis = u32.IsWindowVisible(h)
    r = wintypes.RECT(); u32.GetWindowRect(h, ctypes.byref(r))
    print(h, repr(t.value), cls.value, "visible=%s" % vis, "%dx%d" % (r.right-r.left, r.bottom-r.top))
    if t.value and vis and (r.right - r.left) > 300:
        bmp = os.path.join(TEMP, "win_%d.bmp" % h)
        ok = sw.capture(h, bmp)
        if ok:
            Image.open(bmp).save(os.path.join(TEMP, "win_%d.png" % h))
            print("  截图 -> win_%d.png" % h)
