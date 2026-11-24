# -*- coding: utf-8 -*-
"""生成 Launcher_v9.cs：在 Launcher_v8.cs 基础上新增「设置窗口」与多版本汉化支持。

V1.3 新增（相比 v8）：
  1. 新增设置窗口 SettingsForm：① 汉化目标程序（6 个版本）② 启动画面等待秒数（0-15）③ 开机自动启动
  2. 新增静态类 AppSettings：settings.ini 读写（%APPDATA%\\VoicemeeterZH）、开机自启注册表同步
  3. 补丁数据改为多套：Potato x64/x86、Banana x64/x86、Voicemeeter x64/x86，全部 gzip+base64 内嵌
  4. 启动画面：新增「设置」按钮，秒数可配置，0 秒即跳过启动画面；文案按目标版本动态显示
  5. 「打开配置目录」按目标版本自动定位 VoiceMeeter*Default.xml
  6. 新增命令参数：--settings（直接打开设置）、--autostart（开机自启，不显示启动画面）

用法：python src\\launcher\\gen_v9.py
前置：src\\launcher\\Launcher_v8.cs、src\\patch\\patch_blobs_multi.json
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
SRC = os.path.join(HERE, "Launcher_v8.cs")
DST = os.path.join(HERE, "Launcher_v9.cs")
BLOBS = os.path.join(HERE, "..", "patch", "patch_blobs_multi.json")


# ---------------------------------------------------------------- 工具
def rep(s, old, new, cnt=1):
    n = s.count(old)
    assert n == cnt, "match %d != %d for: %r" % (n, cnt, old[:80])
    return s.replace(old, new, cnt)


def cut_replace(s, start_mark, end_mark, new):
    i = s.find(start_mark)
    assert i >= 0, "start not found: %r" % start_mark[:60]
    j = s.find(end_mark, i)
    assert j > i, "end not found: %r" % end_mark[:60]
    return s[:i] + new + s[j:]


def gz_b64(raw):
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=9, mtime=0) as f:
        f.write(raw)
    return base64.b64encode(buf.getvalue()).decode()


def count_blob(blob):
    pos = 0
    n = 0
    while pos + 7 <= len(blob):
        _rva, ln = struct.unpack_from("<IH", blob, pos)
        enc = blob[pos + 6]
        pos += 7 + ln
        n += 1
    return n


def cs_const(name, b64, width=100):
    parts = [b64[i:i + width] for i in range(0, len(b64), width)]
    body = "\n            + ".join('"%s"' % p for p in parts)
    return "        internal static readonly string %s =\n            %s;\n" % (name, body)


# ---------------------------------------------------------------- C# 片段
MAIN_NEW = r'''        [STAThread]
        static int Main(string[] args)
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);

            InitTargets();

            bool autoStart = false;
            string exeArg = null;
            foreach (string raw in args)
            {
                string a = (raw == null) ? "" : raw.Trim();
                string al = a.ToLowerInvariant();
                if (al == "--autostart" || al == "/autostart" || al == "autostart") { autoStart = true; continue; }
                if (al == "--settings" || al == "/settings" || al == "settings") { SettingsForm.ShowSettings(); return 0; }
                if (al == "--license" || al == "-license" || al == "/license" || al == "license") { LicenseForm.ShowLicense(); return 0; }
                if (a.Length > 0) exeArg = a;
            }

            AppSettings.Load();
            AppSettings.SyncAutoStart();

            string key = AppSettings.Target;
            if (exeArg != null)
            {
                string g = AppSettings.KeyOfFile(exeArg);
                if (g != null) key = g;
            }
            if (key == null || !Targets.ContainsKey(key)) key = "potato_x64";
            TargetInfo ti = Targets[key];

            // 启动画面（开机自启时跳过）
            int sec = autoStart ? 0 : AppSettings.SplashSeconds;
            if (sec > 0)
            {
                if (SplashForm.ShowSplash(sec * 1000, ti))
                {
                    LicenseForm.ShowLicense();
                    return 0;
                }
                AppSettings.Load();
                key = AppSettings.Target;
                if (key == null || !Targets.ContainsKey(key)) key = "potato_x64";
                ti = Targets[key];
            }

            string exePath = (exeArg != null && File.Exists(exeArg)) ? exeArg : FindTarget(key);
            if (exePath == null || !File.Exists(exePath))
            {
                string def = Path.Combine(@"C:\Program Files (x86)\VB\Voicemeeter", ti.FileName);
                MessageBox.Show("未找到 " + ti.FileName + "。\n\n默认路径：\n" + def +
                    "\n\n请安装对应版本的 Voicemeeter，或在「设置」中改选本机已安装的版本。",
                    "Voicemeeter 中文启动器", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return 2;
            }

            // 已在运行则询问
            var running = Process.GetProcessesByName(Path.GetFileNameWithoutExtension(exePath));
            if (running.Length > 0)
            {
                var r = MessageBox.Show("Voicemeeter 正在运行。\n\n需要先关闭它，才能以中文界面重新启动。\n是否立即关闭并重启？",
                    "Voicemeeter 中文启动器", MessageBoxButtons.YesNo, MessageBoxIcon.Question);
                if (r != DialogResult.Yes) return 0;
                foreach (var p in running) { try { p.Kill(); p.WaitForExit(3000); } catch { } }
                System.Threading.Thread.Sleep(800);
            }

            STARTUPINFO si = new STARTUPINFO();
            si.cb = Marshal.SizeOf(typeof(STARTUPINFO));
            PROCESS_INFORMATION pi;
            string wd = Path.GetDirectoryName(exePath);
            if (!CreateProcess(exePath, null, IntPtr.Zero, IntPtr.Zero, false, CREATE_SUSPENDED,
                    IntPtr.Zero, wd, ref si, out pi))
            {
                MessageBox.Show("启动失败，错误码：" + Marshal.GetLastWin32Error(), "Voicemeeter 中文启动器",
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
                return 3;
            }

            byte[] blob = BlobOf(key);
            bool patched = false;
            try { patched = (blob != null) && ApplyPatches(pi.hProcess, blob); }
            catch { patched = false; }

            ResumeThread(pi.hThread);
            CloseHandle(pi.hThread);
            CloseHandle(pi.hProcess);

            if (!patched)
                MessageBox.Show("界面汉化补丁未能应用，程序已按原版（英文）启动。\n\n目标程序：" + ti.FileName,
                    "Voicemeeter 中文启动器", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return 0;
        }

'''

FIND_NEW = r'''        internal static string FindTarget(string key)
        {
            TargetInfo ti;
            if (!Targets.TryGetValue(key, out ti)) return null;
            string[] cands = {
                Path.Combine(@"C:\Program Files (x86)\VB\Voicemeeter", ti.FileName),
                Path.Combine(@"C:\Program Files\VB\Voicemeeter", ti.FileName),
                Path.Combine(Path.GetDirectoryName(Application.ExecutablePath), ti.FileName)
            };
            foreach (string c in cands) if (File.Exists(c)) return c;
            return null;
        }

'''

TARGETS_NEW = r'''        internal static readonly System.Collections.Generic.Dictionary<string, TargetInfo> Targets =
            new System.Collections.Generic.Dictionary<string, TargetInfo>();

        internal static readonly string[] TargetOrder = {
            "potato_x64", "potato_x86", "banana_x64", "banana_x86", "vm_x64", "vm_x86"
        };

        internal static void InitTargets()
        {
            if (Targets.Count > 0) return;
            Targets["potato_x64"] = new TargetInfo("potato_x64", "voicemeeter8x64.exe",
                "Voicemeeter Potato（64 位）", POTATO_X64_COUNT, GZ_POTATO_X64);
            Targets["potato_x86"] = new TargetInfo("potato_x86", "voicemeeter8.exe",
                "Voicemeeter Potato（32 位）", POTATO_X86_COUNT, GZ_POTATO_X86);
            Targets["banana_x64"] = new TargetInfo("banana_x64", "voicemeeterpro_x64.exe",
                "Voicemeeter Banana（64 位）", BANANA_X64_COUNT, GZ_BANANA_X64);
            Targets["banana_x86"] = new TargetInfo("banana_x86", "voicemeeterpro.exe",
                "Voicemeeter Banana（32 位）", BANANA_X86_COUNT, GZ_BANANA_X86);
            Targets["vm_x64"] = new TargetInfo("vm_x64", "voicemeeter_x64.exe",
                "Voicemeeter（64 位）", VM_X64_COUNT, GZ_VM_X64);
            Targets["vm_x86"] = new TargetInfo("vm_x86", "voicemeeter.exe",
                "Voicemeeter（32 位）", VM_X86_COUNT, GZ_VM_X86);
        }

        internal static byte[] BlobOf(string key)
        {
            TargetInfo ti;
            if (key == null || !Targets.TryGetValue(key, out ti)) return null;
            try { return UnGz(ti.Blob); }
            catch { return null; }
        }

        static byte[] UnGz(string b64)
        {
            byte[] gz = Convert.FromBase64String(b64.Replace("\n", "").Replace("\r", ""));
            using (MemoryStream src = new MemoryStream(gz))
            using (GZipStream zs = new GZipStream(src, CompressionMode.Decompress))
            using (MemoryStream dst = new MemoryStream())
            {
                byte[] buf = new byte[8192];
                int n;
                while ((n = zs.Read(buf, 0, buf.Length)) > 0) dst.Write(buf, 0, n);
                return dst.ToArray();
            }
        }
    }

    class TargetInfo
    {
        internal string Key, FileName, Display;
        internal int Count;
        internal string Blob;

        internal TargetInfo(string key, string file, string display, int count, string blob)
        {
            Key = key; FileName = file; Display = display; Count = count; Blob = blob;
        }

        public override string ToString()
        {
            return Display + "   ·   " + FileName;
        }
    }

    static class AppSettings
    {
        internal static string Target = "potato_x64";
        internal static int SplashSeconds = 5;
        internal static bool AutoStart = false;

        const string RunValueName = "VoicemeeterZHLauncher";
        const string RunKeyPath = @"Software\Microsoft\Windows\CurrentVersion\Run";

        internal static string DirPath()
        {
            return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                "VoicemeeterZH");
        }

        internal static string FilePath()
        {
            return Path.Combine(DirPath(), "settings.ini");
        }

        internal static void Load()
        {
            Target = "potato_x64"; SplashSeconds = 5; AutoStart = false;
            try
            {
                string f = FilePath();
                if (File.Exists(f))
                {
                    foreach (string line in File.ReadAllLines(f, Encoding.UTF8))
                    {
                        int p = line.IndexOf('=');
                        if (p <= 0) continue;
                        string k = line.Substring(0, p).Trim();
                        string v = line.Substring(p + 1).Trim();
                        if (k.Equals("Target", StringComparison.OrdinalIgnoreCase) && v.Length > 0) Target = v;
                        else if (k.Equals("SplashSeconds", StringComparison.OrdinalIgnoreCase))
                        {
                            int n;
                            if (int.TryParse(v, out n)) SplashSeconds = n;
                        }
                        else if (k.Equals("AutoStart", StringComparison.OrdinalIgnoreCase)) AutoStart = (v == "1");
                    }
                }
            }
            catch { }
            if (SplashSeconds < 0) SplashSeconds = 0;
            if (SplashSeconds > 15) SplashSeconds = 15;
            if (Program.Targets.Count > 0 && !Program.Targets.ContainsKey(Target)) Target = "potato_x64";
        }

        internal static void Save()
        {
            try
            {
                string d = DirPath();
                if (!Directory.Exists(d)) Directory.CreateDirectory(d);
                StringBuilder sb = new StringBuilder();
                sb.AppendLine("# Voicemeeter 中文界面启动器 设置文件");
                sb.AppendLine("Target=" + Target);
                sb.AppendLine("SplashSeconds=" + SplashSeconds);
                sb.AppendLine("AutoStart=" + (AutoStart ? "1" : "0"));
                File.WriteAllText(FilePath(), sb.ToString(), Encoding.UTF8);
            }
            catch { }
        }

        internal static void SyncAutoStart()
        {
            try
            {
                using (RegistryKey rk = Registry.CurrentUser.OpenSubKey(RunKeyPath, true))
                {
                    if (rk == null) return;
                    if (AutoStart)
                        rk.SetValue(RunValueName, "\"" + Application.ExecutablePath + "\" --autostart");
                    else if (rk.GetValue(RunValueName) != null)
                        rk.DeleteValue(RunValueName, false);
                }
            }
            catch { }
        }

        internal static string KeyOfFile(string path)
        {
            if (path == null || path.Length == 0) return null;
            string n;
            try { n = Path.GetFileName(path).ToLowerInvariant(); }
            catch { return null; }
            foreach (System.Collections.Generic.KeyValuePair<string, TargetInfo> kv in Program.Targets)
                if (kv.Value.FileName.ToLowerInvariant() == n) return kv.Key;
            return null;
        }
    }

'''

SETTINGS_FORM = r'''    class SettingsForm : Form
    {
        static readonly Color SBg = Color.FromArgb(18, 24, 34);
        static readonly Color SEdit = Color.FromArgb(36, 48, 64);
        static readonly Color SFg = Color.FromArgb(232, 239, 247);
        static readonly Color SDim = Color.FromArgb(142, 166, 190);
        static readonly Color SAcc = Color.FromArgb(47, 129, 247);
        static readonly Color SAcc2 = Color.FromArgb(56, 217, 192);
        static readonly Color Gold = Color.FromArgb(255, 185, 90);

        ComboBox cbTarget;
        NumericUpDown nuSec;
        CheckBox ckAuto;
        Label lbState, lbCount;
        internal bool dirty = false;

        public static void ShowSettings()
        {
            try
            {
                using (SettingsForm f = new SettingsForm())
                {
                    f.ShowDialog();
                    if (f.dirty) AppSettings.Load();
                }
            }
            catch { }
        }

        static Font SF(float sz, FontStyle st)
        {
            try { return new Font("Microsoft YaHei UI", sz, st); }
            catch
            {
                try { return new Font("微软雅黑", sz, st); }
                catch { return new Font(FontFamily.GenericSansSerif, sz, st); }
            }
        }

        Label MkLabel(string text, int x, int y, float sz, Color c, bool bold)
        {
            Label l = new Label();
            l.Text = text;
            l.AutoSize = true;
            l.Left = x;
            l.Top = y;
            l.ForeColor = c;
            l.BackColor = SBg;
            l.Font = SF(sz, bold ? FontStyle.Bold : FontStyle.Regular);
            return l;
        }

        Button MkBtn(string text, int x, int y, int w, bool primary)
        {
            Button b = new Button();
            b.Text = text;
            b.FlatStyle = FlatStyle.Flat;
            b.FlatAppearance.BorderSize = 1;
            b.FlatAppearance.BorderColor = primary ? SAcc : Color.FromArgb(58, 86, 116);
            b.BackColor = primary ? Color.FromArgb(40, SAcc) : SEdit;
            b.ForeColor = SFg;
            b.Font = SF(9.5f, FontStyle.Regular);
            b.Cursor = Cursors.Hand;
            b.SetBounds(x, y, w, 32);
            return b;
        }

        public SettingsForm()
        {
            Text = "设置 - Voicemeeter 中文界面启动器";
            ClientSize = new Size(620, 476);
            FormBorderStyle = FormBorderStyle.FixedSingle;
            MaximizeBox = false;
            MinimizeBox = false;
            StartPosition = FormStartPosition.CenterScreen;
            BackColor = SBg;
            ForeColor = SFg;
            Font = SF(10f, FontStyle.Regular);
            AutoScaleMode = AutoScaleMode.None;

            Controls.Add(MkLabel("启动器设置", 22, 16, 15f, SFg, true));
            Controls.Add(MkLabel("设置保存在本机，下次启动自动生效", 24, 48, 9f, SDim, false));

            Controls.Add(MkLabel("① 汉化目标程序", 24, 82, 10f, SAcc2, true));

            cbTarget = new ComboBox();
            cbTarget.DropDownStyle = ComboBoxStyle.DropDownList;
            cbTarget.FlatStyle = FlatStyle.Flat;
            cbTarget.BackColor = SEdit;
            cbTarget.ForeColor = SFg;
            cbTarget.Font = SF(9.5f, FontStyle.Regular);
            cbTarget.SetBounds(24, 108, 572, 26);
            foreach (string k in Program.TargetOrder)
            {
                TargetInfo ti;
                if (!Program.Targets.TryGetValue(k, out ti)) continue;
                cbTarget.Items.Add(ti);
                if (ti.Key == AppSettings.Target) cbTarget.SelectedItem = ti;
            }
            if (cbTarget.SelectedIndex < 0 && cbTarget.Items.Count > 0) cbTarget.SelectedIndex = 0;
            cbTarget.SelectedIndexChanged += delegate { RefreshState(); };
            Controls.Add(cbTarget);

            lbState = MkLabel("", 24, 140, 9f, SDim, false);
            Controls.Add(lbState);

            lbCount = MkLabel("", 24, 162, 9f, SDim, false);
            Controls.Add(lbCount);

            Controls.Add(MkLabel("② 启动画面等待秒数", 24, 200, 10f, SAcc2, true));

            nuSec = new NumericUpDown();
            nuSec.Minimum = 0;
            nuSec.Maximum = 15;
            int v0 = AppSettings.SplashSeconds;
            if (v0 < 0) v0 = 0;
            if (v0 > 15) v0 = 15;
            nuSec.Value = v0;
            nuSec.BackColor = SEdit;
            nuSec.ForeColor = SFg;
            nuSec.BorderStyle = BorderStyle.FixedSingle;
            nuSec.Font = SF(10f, FontStyle.Regular);
            nuSec.SetBounds(24, 226, 78, 26);
            Controls.Add(nuSec);
            Controls.Add(MkLabel("秒（0 = 不显示启动画面，直接以中文界面拉起）", 112, 231, 9f, SDim, false));

            Controls.Add(MkLabel("③ 开机自动启动", 24, 270, 10f, SAcc2, true));

            ckAuto = new CheckBox();
            ckAuto.Text = "随 Windows 启动时自动以中文界面拉起 Voicemeeter（开机自启不显示启动画面）";
            ckAuto.Checked = AppSettings.AutoStart;
            ckAuto.ForeColor = SFg;
            ckAuto.BackColor = SBg;
            ckAuto.Font = SF(9f, FontStyle.Regular);
            ckAuto.AutoSize = true;
            ckAuto.Left = 24;
            ckAuto.Top = 296;
            Controls.Add(ckAuto);

            Controls.Add(MkLabel("开机自启写入当前用户 Run 注册表项，无需管理员权限；",
                24, 330, 8.5f, SDim, false));
            Controls.Add(MkLabel("启动器本身仍需 UAC 提权，才能把汉化补丁写入 Voicemeeter 进程内存。",
                24, 348, 8.5f, SDim, false));

            Button bDir = MkBtn("打开设置文件目录", 24, 420, 152, false);
            bDir.Click += delegate { OpenSettingsDir(); };
            Controls.Add(bDir);

            Button bSave = MkBtn("保存并应用", 380, 420, 104, true);
            bSave.Click += delegate { SaveAll(); };
            Controls.Add(bSave);

            Button bCancel = MkBtn("取消", 496, 420, 100, false);
            bCancel.Click += delegate { Close(); };
            Controls.Add(bCancel);

            RefreshState();
        }

        void RefreshState()
        {
            TargetInfo ti = cbTarget.SelectedItem as TargetInfo;
            if (ti == null) { lbState.Text = ""; lbCount.Text = ""; return; }
            string p = Program.FindTarget(ti.Key);
            if (p != null)
            {
                lbState.Text = "状态：已在本机检测到，启动时将直接使用";
                lbState.ForeColor = SAcc2;
            }
            else
            {
                lbState.Text = "状态：默认目录未检测到该版本（安装后会自动识别）";
                lbState.ForeColor = Gold;
            }
            lbCount.Text = "内置汉化条目：" + ti.Count + " 条（运行时内存替换，不改动原程序文件）";
        }

        void SaveAll()
        {
            TargetInfo ti = cbTarget.SelectedItem as TargetInfo;
            if (ti == null) return;

            if (Program.FindTarget(ti.Key) == null)
            {
                DialogResult r = MessageBox.Show(
                    "本机默认目录未检测到 " + ti.FileName + "。\n\n仍要保存该目标吗？\n" +
                    "（安装对应版本后，启动器会按默认路径自动识别）",
                    "设置", MessageBoxButtons.YesNo, MessageBoxIcon.Warning);
                if (r != DialogResult.Yes) return;
            }

            int sec = (int)nuSec.Value;
            AppSettings.Target = ti.Key;
            AppSettings.SplashSeconds = sec;
            AppSettings.AutoStart = ckAuto.Checked;
            AppSettings.Save();
            AppSettings.SyncAutoStart();
            dirty = true;

            MessageBox.Show("设置已保存。\n\n目标程序：" + ti.Display +
                "\n启动等待：" + (sec == 0 ? "不显示启动画面" : (sec + " 秒")) +
                "\n开机自启：" + (ckAuto.Checked ? "已开启" : "已关闭"),
                "设置", MessageBoxButtons.OK, MessageBoxIcon.Information);
            Close();
        }

        void OpenSettingsDir()
        {
            try
            {
                string d = AppSettings.DirPath();
                if (!Directory.Exists(d)) Directory.CreateDirectory(d);
                Process.Start("explorer.exe", "\"" + d + "\"");
            }
            catch (Exception ex)
            {
                MessageBox.Show("打开目录失败：" + ex.Message, "设置",
                    MessageBoxButtons.OK, MessageBoxIcon.Warning);
            }
        }
    }

'''


def build(s, consts):
    # 1) using 补充
    s = rep(s, "using System.Text;\nusing System.Windows.Forms;",
            "using System.IO.Compression;\nusing System.Text;\nusing System.Windows.Forms;\n"
            "using Microsoft.Win32;")

    # 2) 补丁数据：删除原 BLOB 常量，换成多套 gzip 常量
    m = re.search(r"        static readonly string BLOB =\s*(.*?);\n", s, re.S)
    assert m, "BLOB const not found"
    s = s[:m.start()] + consts + s[m.end():]

    # 3) Main 与 FindTarget 整体替换
    s = cut_replace(s, "        [STAThread]", "        static string FindTarget()", MAIN_NEW)
    s = cut_replace(s, "        static string FindTarget()", "        static bool ApplyPatches(IntPtr hProc)", FIND_NEW)

    # 4) ApplyPatches 接收 blob 参数
    s = rep(s, "        static bool ApplyPatches(IntPtr hProc)",
            "        internal static bool ApplyPatches(IntPtr hProc, byte[] blob)")
    s = rep(s, '            byte[] blob = Convert.FromBase64String(BLOB.Replace("\\n", "").Replace("\\r", ""));\n'
               "            int pos = 0, ok = 0, total = 0;",
            "            if (blob == null || blob.Length < 8) return false;\n"
            "            int pos = 0, ok = 0, total = 0;")

    # 5) Program 类尾部：Targets / InitTargets / BlobOf / TargetInfo / AppSettings
    s = rep(s, "            return ok > total * 8 / 10;\n        }\n    }\n\n    static class ConfigInfo",
            "            return ok > total * 8 / 10;\n        }\n\n" + TARGETS_NEW + "    static class ConfigInfo")

    # 6) ConfigInfo：按目标版本定位配置文件
    s = rep(s, '''        static string ConfigFile()
        {
            return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                "VoiceMeeterPotatoDefault.xml");
        }''',
            '''        static string ConfigFile()
        {
            string name = "VoiceMeeterPotatoDefault.xml";
            string t = AppSettings.Target;
            if (t != null)
            {
                if (t.StartsWith("banana")) name = "VoiceMeeterBananaDefault.xml";
                else if (t.StartsWith("vm_")) name = "VoiceMeeterDefault.xml";
            }
            return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), name);
        }''')

    # 7) 启动画面：静态 DURATION / 目标
    s = rep(s, "        const int DURATION = 5000;",
            "        static int DURATION = 5000;\n        static TargetInfo Target = null;")

    # 8) 启动画面：三个按钮矩形
    s = rep(s, '''        Rectangle LBtnRect
        {
            get
            {
                int py = H - 84;
                return new Rectangle(40, py - 48, 340, 32);
            }
        }

        Rectangle CBtnRect
        {
            get
            {
                int py = H - 84;
                return new Rectangle(392, py - 48, 168, 32);
            }
        }''',
            '''        Rectangle SBtnRect
        {
            get
            {
                int py = H - 84;
                return new Rectangle(40, py - 48, 92, 32);
            }
        }

        Rectangle CBtnRect
        {
            get
            {
                int py = H - 84;
                return new Rectangle(140, py - 48, 150, 32);
            }
        }

        Rectangle LBtnRect
        {
            get
            {
                int py = H - 84;
                return new Rectangle(298, py - 48, 262, 32);
            }
        }''')

    # 9) ShowSplash 带参数
    s = rep(s, '''        public static bool ShowSplash()
        {
            try
            {
                using (SplashForm sp = new SplashForm())''',
            '''        public static bool ShowSplash(int ms, TargetInfo target)
        {
            try
            {
                Target = target;
                DURATION = ms < 400 ? 400 : ms;
                using (SplashForm sp = new SplashForm())''')

    # 10) 点击命中：设置按钮
    s = rep(s, "            if (CBtnRect.Contains(e.Location)) { ConfigInfo.OpenConfigDir(); return; }",
            '''            if (SBtnRect.Contains(e.Location))
            {
                SettingsForm.ShowSettings();
                int sec = AppSettings.SplashSeconds;
                if (sec <= 0) { ticker.Stop(); Close(); return; }
                DURATION = sec * 1000;
                elapsed = 0;
                try { Opacity = 1.0; } catch { }
                if (!ticker.Enabled) ticker.Start();
                Invalidate();
                return;
            }
            if (CBtnRect.Contains(e.Location)) { ConfigInfo.OpenConfigDir(); return; }''')

    # 11) 版本串与动态文案
    s = rep(s, '"中文界面启动器  ·  V1.2  免安装分享版"', '"中文界面启动器  ·  V1.3  免安装分享版"')
    s = rep(s, 'DrawInfo(g, "适用版本", "Voicemeeter Potato 8.x (64 位)", y, FgMain); y += 42f;',
            'DrawInfo(g, "适用版本", Target == null ? "Voicemeeter" : Target.Display, y, FgMain); y += 42f;')
    s = rep(s, 'DrawBullet(g, "1043 条界面文本汉化：菜单、设置面板、对话框与悬停提示", y); y += 24f;',
            'DrawBullet(g, (Target == null ? 0 : Target.Count) + " 条界面文本汉化：菜单、设置面板、对话框与悬停提示", y); y += 24f;')
    s = rep(s, 'DrawBullet(g, "适用 Windows 10 / 11，需已安装 Voicemeeter Potato 8.x 64 位", y); y += 30f;',
            'DrawBullet(g, "支持 Potato / Banana / Voicemeeter 三个系列，可在「设置」中切换", y); y += 30f;')

    # 12) 授权按钮文案 + 新增设置按钮绘制
    s = rep(s, '                    g.DrawString("授权与激活帮助（挑战码 / 足迹 / REGEN）", fBullet, b, lb, sf);\n            }\n',
            '''                    g.DrawString("授权与激活帮助（挑战码 / REGEN）", fBullet, b, lb, sf);
            }
''')
    s = rep(s, '''                using (SolidBrush b = new SolidBrush(FgMain))
                    g.DrawString("打开配置目录", fBullet, b, cb, sf2);
            }
''',
            '''                using (SolidBrush b = new SolidBrush(FgMain))
                    g.DrawString("打开配置目录", fBullet, b, cb, sf2);
            }

            Rectangle sb = SBtnRect;
            using (GraphicsPath gp = Round(sb, 9))
            {
                using (SolidBrush b = new SolidBrush(Color.FromArgb(30, Accent))) g.FillPath(b, gp);
                using (Pen p = new Pen(Color.FromArgb(130, Accent), 1.2f)) g.DrawPath(p, gp);
            }
            using (StringFormat sf3 = new StringFormat())
            {
                sf3.Alignment = StringAlignment.Center;
                sf3.LineAlignment = StringAlignment.Center;
                using (SolidBrush b = new SolidBrush(FgMain))
                    g.DrawString("设置", fBullet, b, sb, sf3);
            }
''')

    # 13) 底部右侧倒计时文案动态化
    s = rep(s, '                string right = "5 秒后自动开始（点击画面可跳过）";',
            '                string right = ((DURATION + 999) / 1000) + " 秒后自动开始（点击画面可跳过）";')

    # 14) 帮助面板底部：4 按钮 -> 5 按钮（新增设置）
    s = rep(s, '''            Button bOpen = MkBtn("打开激活日志目录", 20, 12, 148);
            bOpen.Click += OpenLogDir;
            foot.Controls.Add(bOpen);

            Button bCopy = MkBtn("复制日志路径", 176, 12, 112);
            bCopy.Click += CopyLogPath;
            foot.Controls.Add(bCopy);

            Button bCfg = MkBtn("打开配置目录", 296, 12, 124);
            bCfg.Click += delegate { ConfigInfo.OpenConfigDir(); };
            foot.Controls.Add(bCfg);

            Button bClose = MkBtn("关闭", 428, 12, 80);''',
            '''            Button bSet = MkBtn("设置", 20, 12, 74);
            bSet.Click += delegate { SettingsForm.ShowSettings(); };
            foot.Controls.Add(bSet);

            Button bOpen = MkBtn("打开激活日志目录", 102, 12, 148);
            bOpen.Click += OpenLogDir;
            foot.Controls.Add(bOpen);

            Button bCopy = MkBtn("复制日志路径", 258, 12, 112);
            bCopy.Click += CopyLogPath;
            foot.Controls.Add(bCopy);

            Button bCfg = MkBtn("打开配置目录", 378, 12, 124);
            bCfg.Click += delegate { ConfigInfo.OpenConfigDir(); };
            foot.Controls.Add(bCfg);

            Button bClose = MkBtn("关闭", 510, 12, 80);''')

    # 15) 插入 SettingsForm 类（放在 LicenseForm 之前）
    s = rep(s, "\n    class LicenseForm : Form\n", "\n" + SETTINGS_FORM + "\n    class LicenseForm : Form\n")
    return s


def main():
    raw = io.open(SRC, "r", encoding="utf-8", newline="").read()

    # 原 Potato x64 blob：从 v8 源码取出后重新 gzip（条目数不变，体积极小）
    m = re.search(r"        static readonly string BLOB =\s*(.*?);\n", raw, re.S)
    assert m
    expr = m.group(1)
    b64_old = eval(re.sub(r"\s+", " ", expr.replace("+", " + ")).strip())
    old_blob = base64.b64decode(b64_old)
    n_potato = count_blob(old_blob)
    print("[potato_x64] 原 blob %d 条, %d 字节" % (n_potato, len(old_blob)))

    j = json.load(io.open(BLOBS, "r", encoding="utf-8"))
    counts = {"potato_x64": n_potato}
    for k, v in j.items():
        if k == "potato_x64":
            continue
        counts[k] = v["count"]

    consts = ""
    consts += cs_const("GZ_POTATO_X64", gz_b64(old_blob))
    name_map = {
        "potato_x86": "GZ_POTATO_X86",
        "banana_x64": "GZ_BANANA_X64",
        "banana_x86": "GZ_BANANA_X86",
        "vm_x64": "GZ_VM_X64",
        "vm_x86": "GZ_VM_X86",
    }
    for k, cn in name_map.items():
        consts += cs_const(cn, j[k]["b64"])

    for k in ["potato_x64", "potato_x86", "banana_x64", "banana_x86", "vm_x64", "vm_x86"]:
        consts += "        internal const int %s_COUNT = %d;\n" % (k.upper(), counts[k])
    consts += "\n"

    out = build(raw, consts)
    io.open(DST, "w", encoding="utf-8", newline="").write(out)
    print("[gen]", DST)
    print("[size]", os.path.getsize(SRC), "->", os.path.getsize(DST))
    print("[counts]", counts)


if __name__ == "__main__":
    main()
