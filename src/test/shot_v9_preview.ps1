Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms

$sig = @"
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
public class Win {
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc lpEnumFunc, IntPtr lParam);
    public delegate bool EnumProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
    [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr hWnd, System.Text.StringBuilder s, int n);
    [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr hWnd, IntPtr hdc, uint flags);
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
    public static List<IntPtr> All() {
        List<IntPtr> l = new List<IntPtr>();
        EnumWindows(delegate(IntPtr h, IntPtr p) { if (IsWindowVisible(h)) l.Add(h); return true; }, IntPtr.Zero);
        return l;
    }
    public static string Title(IntPtr h) { System.Text.StringBuilder sb = new System.Text.StringBuilder(512); GetWindowText(h, sb, 512); return sb.ToString(); }
    public static RECT Rect(IntPtr h) { RECT r; GetWindowRect(h, out r); return r; }
}
"@
Add-Type -TypeDefinition $sig -ReferencedAssemblies System.Drawing

$out  = "C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2Siy4T87X5Sx6qEfhnB8hbI\workspace\conv_7d5c914e13b74cd1a41a32b2f23b1221\temp"
$exe  = "E:\yscl\voicemeeter-zh\src\launcher\VM8CN_Launcher_v9.exe"
$iniDir = Join-Path $env:APPDATA "VoicemeeterZH"
$ini  = Join-Path $iniDir "settings.ini"

New-Item -ItemType Directory -Force -Path $iniDir | Out-Null
$content = "# 设置文件`r`nTarget=potato_x64`r`nSplashSeconds=5`r`nAutoStart=0`r`n"
[System.IO.File]::WriteAllText($ini, $content, (New-Object System.Text.UTF8Encoding($false)))
Write-Output ("[ini] " + $ini)

$before = @{}
foreach ($h in [Win]::All()) { $before[[int64]$h] = 1 }

$p = Start-Process -FilePath $exe -PassThru
Write-Output ("[pid] " + $p.Id)
Start-Sleep -Milliseconds 1100

$target = [IntPtr]::Zero
foreach ($h in [Win]::All()) {
    if ($before.ContainsKey([int64]$h)) { continue }
    $r = [Win]::Rect($h)
    $w = $r.Right - $r.Left; $ht = $r.Bottom - $r.Top
    if ($w -ge 560 -and $w -le 700 -and $ht -ge 480 -and $ht -le 600) {
        $target = $h
        Write-Output ("[splash] " + [Win]::Title($h) + " " + $w + "x" + $ht)
        break
    }
}

if ($target -eq [IntPtr]::Zero) {
    Write-Output "splash not found"
} else {
    $r = [Win]::Rect($target)
    $w = $r.Right - $r.Left; $ht = $r.Bottom - $r.Top
    $bmp = New-Object System.Drawing.Bitmap($w, $ht)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $hdc = $g.GetHdc()
    [void][Win]::PrintWindow($target, $hdc, 2)
    $g.ReleaseHdc($hdc); $g.Dispose()
    $path = Join-Path $out "splash_v9_preview.png"
    $bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
    $bmp.Dispose()
    Write-Output ("saved " + $path + " " + $w + "x" + $ht)
}

Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 400
Get-Process voicemeeter8x64 -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Write-Output "done"
