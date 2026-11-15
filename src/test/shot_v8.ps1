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
    [DllImport("user32.dll")] public static extern bool EnumChildWindows(IntPtr hWnd, EnumProc cb, IntPtr p);
    [DllImport("user32.dll")] public static extern int GetClassName(IntPtr hWnd, System.Text.StringBuilder s, int n);
    [DllImport("user32.dll")] public static extern IntPtr SendMessage(IntPtr hWnd, uint msg, IntPtr wp, IntPtr lp);
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
    public static List<IntPtr> All() {
        List<IntPtr> l = new List<IntPtr>();
        EnumWindows(delegate(IntPtr h, IntPtr p) { if (IsWindowVisible(h)) l.Add(h); return true; }, IntPtr.Zero);
        return l;
    }
    public static string Title(IntPtr h) { System.Text.StringBuilder sb = new System.Text.StringBuilder(512); GetWindowText(h, sb, 512); return sb.ToString(); }
    public static RECT Rect(IntPtr h) { RECT r; GetWindowRect(h, out r); return r; }
    public static List<IntPtr> Kids(IntPtr h) {
        List<IntPtr> l = new List<IntPtr>();
        EnumChildWindows(h, delegate(IntPtr c, IntPtr p) { l.Add(c); return true; }, IntPtr.Zero);
        return l;
    }
}
"@
Add-Type -TypeDefinition $sig -ReferencedAssemblies System.Drawing

$out = "C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2Siy4T87X5Sx6qEfhnB8hbI\workspace\conv_7d5c914e13b74cd1a41a32b2f23b1221\temp"
$exe = "E:\yscl\voicemeeter-zh\src\launcher\VM8CN_v8_test.exe"

function ShotWin($h, $path) {
    $r = [Win]::Rect($h)
    $w = $r.Right - $r.Left; $ht = $r.Bottom - $r.Top
    if ($w -le 0 -or $ht -le 0) { Write-Output "bad rect"; return }
    $bmp = New-Object System.Drawing.Bitmap($w, $ht)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $hdc = $g.GetHdc()
    [void][Win]::PrintWindow($h, $hdc, 2)
    $g.ReleaseHdc($hdc)
    $g.Dispose()
    $bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
    $bmp.Dispose()
    Write-Output ("saved " + $path + " " + $w + "x" + $ht)
}

# splash
$before = @{}
foreach ($h in [Win]::All()) { $before[[int64]$h] = 1 }
$p = Start-Process -FilePath $exe -PassThru
Start-Sleep -Milliseconds 1200
$target = [IntPtr]::Zero
foreach ($h in [Win]::All()) {
    if ($before.ContainsKey([int64]$h)) { continue }
    $r = [Win]::Rect($h)
    $w = $r.Right - $r.Left; $ht = $r.Bottom - $r.Top
    if ($w -gt 300 -and $ht -gt 300) { $target = $h; break }
}
if ($target -ne [IntPtr]::Zero) { ShotWin $target (Join-Path $out "win_splash_v8.png") } else { Write-Output "splash not found" }
Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 600

# license panel
$before2 = @{}
foreach ($h in [Win]::All()) { $before2[[int64]$h] = 1 }
$p2 = Start-Process -FilePath $exe -ArgumentList "--license" -PassThru
Start-Sleep -Milliseconds 1800
$t2 = [IntPtr]::Zero; $best = 0
foreach ($h in [Win]::All()) {
    if ($before2.ContainsKey([int64]$h)) { continue }
    $r = [Win]::Rect($h)
    $w = $r.Right - $r.Left; $ht = $r.Bottom - $r.Top
    if ($w -gt 300 -and $ht -gt 300 -and ($w * $ht) -gt $best) { $best = $w * $ht; $t2 = $h }
}
if ($t2 -ne [IntPtr]::Zero) {
    ShotWin $t2 (Join-Path $out "win_license_v8.png")
    $btns = @()
    foreach ($c in [Win]::Kids($t2)) {
        $sb = New-Object System.Text.StringBuilder 256
        [void][Win]::GetClassName($c, $sb, 256)
        if ($sb.ToString() -like "*BUTTON*") { $btns += $c }
    }
    Write-Output ("buttons: " + $btns.Count)
} else { Write-Output "license not found" }

# click the third button (config) to verify explorer select behavior
if ($t2 -ne [IntPtr]::Zero -and $btns.Count -ge 3) {
    [void][Win]::SendMessage($btns[2], 0x00F5, [IntPtr]::Zero, [IntPtr]::Zero)
    Start-Sleep -Milliseconds 1500
    $expl = Get-Process explorer -ErrorAction SilentlyContinue | Measure-Object
    Write-Output ("explorer procs: " + $expl.Count)
}
Start-Sleep -Milliseconds 300
Stop-Process -Id $p2.Id -Force -ErrorAction SilentlyContinue
Write-Output "done"
