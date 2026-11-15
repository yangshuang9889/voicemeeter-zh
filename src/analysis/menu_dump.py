# -*- coding: utf-8 -*-
"""导出目标进程窗口的菜单文本与对话框控件文本，验证汉化。"""
import ctypes, sys, os, importlib.util
from ctypes import wintypes
TEMP = os.path.dirname(os.path.abspath(__file__))
pid = int(sys.argv[1]) if len(sys.argv) > 1 else 26496

u32 = ctypes.WinDLL('user32', use_last_error=True)
u32.SendMessageW.restype = ctypes.c_void_p

class MENUITEMINFOW(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.UINT), ("fMask", wintypes.UINT), ("fType", wintypes.UINT),
                ("fState", wintypes.UINT), ("wID", wintypes.UINT), ("hSubMenu", wintypes.HANDLE),
                ("hbmpChecked", wintypes.HANDLE), ("hbmpUnchecked", wintypes.HANDLE),
                ("dwItemData", ctypes.c_void_p), ("dwTypeData", wintypes.LPWSTR),
                ("cch", wintypes.UINT), ("hbmpItem", wintypes.HANDLE)]

MIIM_STRING = 0x40
MIIM_SUBMENU = 0x4

ENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
sql = ctypes.WinDLL('sqlite3') if False else None

def menu_texts(hmenu, depth=0, out=None):
    if out is None: out = []
    n = u32.GetMenuItemCount(hmenu)
    for i in range(n):
        mii = MENUITEMINFOW()
        mii.cbSize = ctypes.sizeof(mii)
        mii.fMask = MIIM_STRING | MIIM_SUBMENU
        buf = ctypes.create_unicode_buffer(512)
        mii.dwTypeData = buf
        mii.cch = 512
        if u32.GetMenuItemInfoW(hmenu, i, True, ctypes.byref(mii)):
            txt = buf.value
            if txt:
                out.append("  " * depth + "[%d] %s" % (i, txt))
            if mii.hSubMenu:
                menu_texts(mii.hSubMenu, depth + 1, out)
    return out

hits = []
@ENUMPROC
def cb(hwnd, lp):
    hits.append(hwnd)
    return True
u32.EnumWindows(cb, 0)

# 找 pid 所属窗口
target = []
gi = ctypes.WinDLL('kernel32')
for hwnd in hits:
    p = wintypes.DWORD()
    u32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
    if p.value != pid: continue
    cls = ctypes.create_unicode_buffer(256)
    u32.GetClassNameW(hwnd, cls, 256)
    t = ctypes.create_unicode_buffer(512)
    u32.GetWindowTextW(hwnd, t, 512)
    target.append((hwnd, cls.value, t.value))

for hwnd, cls, title in target:
    print("=" * 60)
    print("窗口:", hwnd, repr(title), cls)
    hm = u32.GetMenu(hwnd)
    if hm:
        texts = menu_texts(hm)
        print("菜单项 %d 个:" % len(texts))
        for tx in texts[:80]: print(tx)
    else:
        print("(无菜单条)")
    # 子控件文字
    ctrls = []
    @ENUMPROC
    def cbc(h, lp):
        buf = ctypes.create_unicode_buffer(512)
        u32.GetWindowTextW(h, buf, 512)
        c2 = ctypes.create_unicode_buffer(128)
        u32.GetClassNameW(h, c2, 128)
        if buf.value:
            ctrls.append("%s | %s" % (c2.value, buf.value))
        return True
    u32.EnumChildWindows(hwnd, cbc, 0)
    if ctrls:
        print("子控件文字:")
        for c in ctrls[:40]: print("   ", c)
