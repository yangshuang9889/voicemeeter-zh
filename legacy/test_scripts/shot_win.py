# -*- coding: utf-8 -*-
"""按 PID 截取窗口（PrintWindow）。"""
import ctypes, ctypes.wintypes as wt, os

user32 = ctypes.WinDLL('user32', use_last_error=True)
gdi32 = ctypes.WinDLL('gdi32', use_last_error=True)

class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

ENUMPROC = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)

def windows_of(pid):
    out = []
    def cb(hwnd, lp):
        p = wt.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
        if p.value == pid and user32.IsWindowVisible(hwnd):
            buf = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(hwnd, buf, 256)
            cls = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, cls, 256)
            r = RECT(); user32.GetWindowRect(hwnd, ctypes.byref(r))
            out.append((hwnd, buf.value, cls.value,
                        r.right-r.left, r.bottom-r.top))
        return True
    user32.EnumWindows(ENUMPROC(cb), 0)
    return out

def capture(hwnd, path):
    r = RECT(); user32.GetWindowRect(hwnd, ctypes.byref(r))
    w = max(r.right-r.left, 1); h = max(r.bottom-r.top, 1)
    hdc = user32.GetWindowDC(hwnd)
    mdc = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
    gdi32.SelectObject(mdc, bmp)
    ok = user32.PrintWindow(hwnd, mdc, 2)
    # 保存
    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [("biSize", wt.DWORD), ("biWidth", ctypes.c_long), ("biHeight", ctypes.c_long),
                    ("biPlanes", wt.WORD), ("biBitCount", wt.WORD), ("biCompression", wt.DWORD),
                    ("biSizeImage", wt.DWORD), ("biXPelsPerMeter", ctypes.c_long),
                    ("biYPelsPerMeter", ctypes.c_long), ("biClrUsed", wt.DWORD), ("biClrImportant", wt.DWORD)]
    bi = BITMAPINFOHEADER(); bi.biSize = ctypes.sizeof(bi)
    bi.biWidth = w; bi.biHeight = -h; bi.biPlanes = 1; bi.biBitCount = 32; bi.biCompression = 0
    buf = ctypes.create_string_buffer(w*h*4)
    got = gdi32.GetDIBits(mdc, bmp, 0, h, buf, ctypes.byref(bi), 0)
    gdi32.DeleteObject(bmp); gdi32.DeleteDC(mdc); user32.ReleaseDC(hwnd, hdc)
    # 写 BMP
    import struct
    data = buf.raw
    hdr = b'BM' + struct.pack('<IHHI', 14+40+len(data), 0, 0, 14+40)
    ih = struct.pack('<IiiHHIIiiII', 40, w, -h, 1, 32, 0, len(data), 0, 0, 0, 0)
    open(path, 'wb').write(hdr+ih+data)
    return ok, got, w, h
