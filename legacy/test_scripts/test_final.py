# -*- coding: utf-8 -*-
"""实测最终汉化版：启动、存活判定、截图。"""
import subprocess, time, os, shutil, ctypes

SRC = r"C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2Siy4T87X5Sx6qEfhnB8hbI\workspace\conv_7d5c914e13b74cd1a41a32b2f23b1221\output\voicemeeter_cn\voicemeeter8x64.exe"
TEST = r"C:\Program Files (x86)\VB\Voicemeeter\vmtest.exe"
SHOT = r"C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2Siy4T87X5Sx6qEfhnB8hbI\workspace\conv_7d5c914e13b74cd1a41a32b2f23b1221\temp\vm_shot.png"

def kill():
    subprocess.run(["taskkill", "/F", "/IM", "vmtest.exe"], capture_output=True)

def shot(path):
    ps = '''
Add-Type -AssemblyName System.Windows.Forms,System.Drawing
$b = [System.Windows.Forms.SystemInformation]::VirtualScreen
$bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($b.Left, $b.Top, 0, 0, $bmp.Size)
$bmp.Save("%s", [System.Drawing.Imaging.ImageFormat]::Png)
''' % path
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True)

kill(); time.sleep(0.5)
shutil.copy2(SRC, TEST)
print("已复制汉化版 ->", TEST)
p = subprocess.Popen([TEST])
t0 = time.time()
while time.time()-t0 < 12:
    if p.poll() is not None:
        print("进程提前退出，exit=%s，用时 %.2fs" % (hex(p.returncode & 0xffffffff), time.time()-t0))
        break
    time.sleep(0.5)
else:
    print("进程存活 %.1fs —— 启动成功" % (time.time()-t0))
    shot(SHOT)
    print("截图:", SHOT, os.path.exists(SHOT))
time.sleep(1)
kill()
