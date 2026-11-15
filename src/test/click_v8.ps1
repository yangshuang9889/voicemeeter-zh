Add-Type -AssemblyName System.Drawing
$sig = @"
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
public class W2 {
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb, IntPtr p);
    public delegate bool EnumProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT r);
    [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr hWnd, System.Text.StringBuilder s, int n);
    [DllImport("user32.dll")] public static extern bool EnumChildWindows(IntPtr hWnd, EnumProc cb, IntPtr p);
    [DllImport("user32.dll")] public static extern int GetClassName(IntPtr hWnd, System.Text.StringBuilder s, int n);
    [DllImport("user32.dll")] public static extern IntPtr SendMessage(IntPtr hWnd, uint msg, IntPtr wp, IntPtr lp);
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
    public static List<IntPtr> All() { List<IntPtr> l = new List<IntPtr>(); EnumWindows(delegate(IntPtr h, IntPtr p) { if (IsWindowVisible(h)) l.Add(h); return true; }, IntPtr.Zero); return l; }
    public static string Title(IntPtr h) { System.Text.StringBuilder sb = new System.Text.StringBuilder(512); GetWindowText(h, sb, 512); return sb.ToString(); }
    public static RECT Rect(IntPtr h) { RECT r; GetWindowRect(h, out r); return r; }
    public static List<IntPtr> Kids(IntPtr h) { List<IntPtr> l = new List<IntPtr>(); EnumChildWindows(h, delegate(IntPtr c, IntPtr p) { l.Add(c); return true; }, IntPtr.Zero); return l; }
    public static string Cls(IntPtr h) { System.Text.StringBuilder sb = new System.Text.StringBuilder(256); GetClassName(h, sb, 256); return sb.ToString(); }
}
"@
Add-Type -TypeDefinition $sig -ReferencedAssemblies System.Drawing

$exe = "E:\yscl\voicemeeter-zh\src\launcher\VM8CN_v8_test.exe"
$before = @{}
foreach ($h in [W2]::All()) { $before[[int64]$h] = 1 }

$p = Start-Process -FilePath $exe -ArgumentList "--license" -PassThru
Start-Sleep -Milliseconds 1800
$form = [IntPtr]::Zero; $best = 0
foreach ($h in [W2]::All()) {
    if ($before.ContainsKey([int64]$h)) { continue }
    $r = [W2]::Rect($h); $w = $r.Right - $r.Left; $ht = $r.Bottom - $r.Top
    if ($w -gt 300 -and $ht -gt 300 -and ($w * $ht) -gt $best) { $best = $w * $ht; $form = $h }
}
$list = New-Object System.Collections.ArrayList
foreach ($c in [W2]::Kids($form)) {
    if ([W2]::Cls($c) -like "*BUTTON*") {
        $r = [W2]::Rect($c)
        [void]$list.Add([pscustomobject]@{ H = $c; X = $r.Left; Y = $r.Top; W = ($r.Right - $r.Left) })
    }
}
$sorted = $list | Sort-Object Y, X
$i = 0
foreach ($b in $sorted) { Write-Output ("btn#" + $i + " x=" + $b.X + " y=" + $b.Y + " w=" + $b.W); $i++ }

$cfg = $sorted[2]
Write-Output ("clicking btn#2 x=" + $cfg.X)
$set = @{}
foreach ($h in [W2]::All()) { $set[[int64]$h] = 1 }
[void][W2]::SendMessage($cfg.H, 0x00F5, [IntPtr]::Zero, [IntPtr]::Zero)
Start-Sleep -Milliseconds 2000
$new = @()
foreach ($h in [W2]::All()) {
    if ($set.ContainsKey([int64]$h)) { continue }
    $t = [W2]::Title($h)
    if ($t -ne "") { $new += ([W2]::Cls($h) + " | " + $t) }
}
Write-Output ("NEW WINDOWS: " + $new.Count)
$new | ForEach-Object { Write-Output $_ }
Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
