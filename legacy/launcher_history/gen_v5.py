# -*- coding: utf-8 -*-
"""在 Launcher_v4.cs 基础上加入 5 秒启动画面（Splash），生成 Launcher_v5.cs"""
import io, os, sys

TEMP = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(TEMP, "Launcher_v4.cs")
DST = os.path.join(TEMP, "Launcher_v5.cs")

src = io.open(SRC, "r", encoding="utf-8-sig").read()

# 1) using 增加 Drawing
old_using = "using System.Diagnostics;\r\nusing System.IO;"
if old_using not in src:
    old_using = "using System.Diagnostics;\nusing System.IO;"
nl = "\r\n" if "\r\n" in src else "\n"
new_using = "using System.Diagnostics;" + nl + "using System.Drawing;" + nl + \
            "using System.Drawing.Drawing2D;" + nl + "using System.IO;"
assert old_using in src, "using 段未匹配"
src = src.replace(old_using, new_using, 1)

# 2) Main 开头启用视觉样式
old_main = '        {' + nl + '            string exePath = args.Length > 0 ? args[0] : FindTarget();'
assert old_main in src, "Main 开头未匹配"
new_main = ('        {' + nl +
            '            Application.EnableVisualStyles();' + nl +
            '            Application.SetCompatibleTextRenderingDefault(false);' + nl + nl +
            '            string exePath = args.Length > 0 ? args[0] : FindTarget();')
src = src.replace(old_main, new_main, 1)

# 3) 校验通过后显示启动画面
old_call = ('                return 2;' + nl + '            }' + nl + nl + '            // 已在运行则询问')
assert old_call in src, "splash 插入点未匹配"
new_call = ('                return 2;' + nl + '            }' + nl + nl +
            '            // 启动画面，5 秒后自动消失' + nl +
            '            SplashForm.ShowSplash();' + nl + nl +
            '            // 已在运行则询问')
src = src.replace(old_call, new_call, 1)

SPLASH = r'''
    class SplashForm : Form
    {
        const int W = 560, H = 366;
        const int DURATION = 5000;
        readonly Timer ticker = new Timer();
        int elapsed = 0;

        static readonly Color BgTL = Color.FromArgb(13, 19, 28);
        static readonly Color BgBR = Color.FromArgb(28, 42, 60);
        static readonly Color Accent = Color.FromArgb(47, 129, 247);
        static readonly Color Accent2 = Color.FromArgb(56, 217, 192);
        static readonly Color FgMain = Color.FromArgb(232, 239, 247);
        static readonly Color FgSub = Color.FromArgb(142, 166, 190);
        static readonly Color Gold = Color.FromArgb(255, 185, 90);
        static readonly Color CopyC = Color.FromArgb(96, 140, 165, 190);

        Font fTitle, fSub, fBody, fKey, fSmall, fIcon, fCopy;

        public static void ShowSplash()
        {
            try
            {
                using (SplashForm sp = new SplashForm()) sp.ShowDialog();
            }
            catch { }
        }

        public SplashForm()
        {
            FormBorderStyle = FormBorderStyle.None;
            StartPosition = FormStartPosition.CenterScreen;
            ClientSize = new Size(W, H);
            ShowInTaskbar = false;
            TopMost = true;
            BackColor = BgTL;
            AutoScaleMode = AutoScaleMode.None;
            SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.UserPaint | ControlStyles.OptimizedDoubleBuffer, true);
            DoubleBuffered = true;
            try { Region = new Region(Round(new Rectangle(0, 0, W, H), 16)); } catch { }

            fTitle = MkFont(21f, FontStyle.Bold);
            fSub = MkFont(9.5f, FontStyle.Regular);
            fBody = MkFont(12f, FontStyle.Regular);
            fKey = MkFont(10f, FontStyle.Regular);
            fSmall = MkFont(9f, FontStyle.Regular);
            fIcon = MkFont(15f, FontStyle.Bold);
            fCopy = MkFont(8.5f, FontStyle.Regular);

            ticker.Interval = 40;
            ticker.Tick += Ticker_Tick;
            ticker.Start();
        }

        static Font MkFont(float sz, FontStyle st)
        {
            try { return new Font("Microsoft YaHei UI", sz, st); }
            catch
            {
                try { return new Font("微软雅黑", sz, st); }
                catch { return new Font(FontFamily.GenericSansSerif, sz, st); }
            }
        }

        void Ticker_Tick(object sender, EventArgs e)
        {
            elapsed += ticker.Interval;
            if (elapsed >= DURATION - 400)
            {
                double k = (double)(elapsed - (DURATION - 400)) / 400.0;
                if (k > 1) k = 1;
                if (k < 0) k = 0;
                try { Opacity = 1.0 - k; } catch { }
            }
            if (elapsed >= DURATION)
            {
                ticker.Stop();
                Close();
                return;
            }
            Invalidate();
        }

        protected override void OnMouseClick(MouseEventArgs e)
        {
            base.OnMouseClick(e);
            ticker.Stop();
            Close();
        }

        static GraphicsPath Round(Rectangle r, int rad)
        {
            GraphicsPath gp = new GraphicsPath();
            int d = rad * 2;
            if (d > r.Width) d = r.Width;
            if (d > r.Height) d = r.Height;
            if (d <= 0) { gp.AddRectangle(r); return gp; }
            gp.AddArc(r.X, r.Y, d, d, 180, 90);
            gp.AddArc(r.Right - d, r.Y, d, d, 270, 90);
            gp.AddArc(r.Right - d, r.Bottom - d, d, d, 0, 90);
            gp.AddArc(r.X, r.Bottom - d, d, d, 90, 90);
            gp.CloseFigure();
            return gp;
        }

        void DrawInfo(Graphics g, string key, string val, float y, Color vc, Font vf)
        {
            using (SolidBrush kb = new SolidBrush(FgSub)) g.DrawString(key, fKey, kb, 40f, y + 2f);
            using (SolidBrush vb = new SolidBrush(vc)) g.DrawString(val, vf, vb, 132f, y);
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            Graphics g = e.Graphics;
            g.SmoothingMode = SmoothingMode.AntiAlias;
            g.TextRenderingHint = System.Drawing.Text.TextRenderingHint.AntiAlias;

            Rectangle full = new Rectangle(0, 0, W, H);
            using (LinearGradientBrush br = new LinearGradientBrush(full, BgTL, BgBR, 45f))
                g.FillRectangle(br, full);

            using (GraphicsPath gp = new GraphicsPath())
            {
                gp.AddEllipse(W - 280, -190, 440, 440);
                using (PathGradientBrush pgb = new PathGradientBrush(gp))
                {
                    pgb.CenterColor = Color.FromArgb(95, Accent);
                    pgb.SurroundColors = new Color[] { Color.FromArgb(0, Accent) };
                    g.FillPath(pgb, gp);
                }
            }
            using (GraphicsPath gp = new GraphicsPath())
            {
                gp.AddEllipse(-170, H - 170, 380, 380);
                using (PathGradientBrush pgb = new PathGradientBrush(gp))
                {
                    pgb.CenterColor = Color.FromArgb(60, Accent2);
                    pgb.SurroundColors = new Color[] { Color.FromArgb(0, Accent2) };
                    g.FillPath(pgb, gp);
                }
            }

            using (Pen pen = new Pen(Color.FromArgb(120, Accent2), 2f))
                g.DrawLine(pen, 8, 1.5f, W - 8, 1.5f);

            Rectangle ico = new Rectangle(40, 40, 54, 54);
            using (GraphicsPath gp = Round(ico, 15))
            {
                using (LinearGradientBrush br = new LinearGradientBrush(ico, Accent, Accent2, 45f))
                    g.FillPath(br, gp);
                using (StringFormat sf = new StringFormat())
                {
                    sf.Alignment = StringAlignment.Center;
                    sf.LineAlignment = StringAlignment.Center;
                    g.DrawString("VM", fIcon, Brushes.White, ico, sf);
                }
            }

            using (SolidBrush b = new SolidBrush(FgMain)) g.DrawString("Voicemeeter Potato", fTitle, b, 110f, 40f);
            using (SolidBrush b = new SolidBrush(FgSub)) g.DrawString("中文界面启动器  ·  V1.0  免安装分享版", fSub, b, 112f, 76f);

            using (Pen pen = new Pen(Color.FromArgb(55, 255, 255, 255)))
                g.DrawLine(pen, 40, 114, W - 40, 114);

            float y = 134f;
            DrawInfo(g, "制作", "杨爽工作室", y, Gold, fBody); y += 34f;
            DrawInfo(g, "制作工具", "Marvis", y, FgMain, fBody); y += 34f;
            DrawInfo(g, "适用版本", "Voicemeeter Potato 8.x (64 位)", y, FgMain, fBody); y += 36f;

            using (SolidBrush b = new SolidBrush(FgSub))
            {
                g.DrawString("汉化范围：主界面 · 音频引擎面板 · 各类对话框文本", fSmall, b, 40f, y);
                g.DrawString("界面文本在内存中替换，不改动原程序文件；启动需管理员权限", fSmall, b, 40f, y + 22f);
            }

            int py = H - 74;
            Rectangle track = new Rectangle(40, py, W - 80, 6);
            using (GraphicsPath gp = Round(track, 3))
            using (SolidBrush b = new SolidBrush(Color.FromArgb(48, 255, 255, 255)))
                g.FillPath(b, gp);

            double ratio = (double)elapsed / DURATION;
            if (ratio > 1) ratio = 1;
            int pw = (int)((W - 80) * ratio);
            if (pw > 3)
            {
                Rectangle bar = new Rectangle(40, py, pw, 6);
                Rectangle glow = new Rectangle(40, py, Math.Max(pw, 12), 6);
                using (GraphicsPath gp = Round(bar, 3))
                using (LinearGradientBrush br = new LinearGradientBrush(glow, Accent, Accent2, 0f))
                    g.FillPath(br, gp);
            }

            using (SolidBrush b = new SolidBrush(FgSub))
            {
                g.DrawString("正在准备中文界面…", fSmall, b, 40f, py + 14f);
                string right = "5 秒后自动开始";
                SizeF rs = g.MeasureString(right, fSmall);
                g.DrawString(right, fSmall, b, W - 40 - rs.Width, py + 14f);
            }

            using (SolidBrush b = new SolidBrush(CopyC))
            {
                string copy = "© 杨爽工作室   ·   Powered by Marvis";
                SizeF cs = g.MeasureString(copy, fCopy);
                g.DrawString(copy, fCopy, b, (W - cs.Width) / 2f, H - 26f);
            }
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing)
            {
                try { ticker.Stop(); ticker.Dispose(); } catch { }
                foreach (Font f in new Font[] { fTitle, fSub, fBody, fKey, fSmall, fIcon, fCopy })
                    try { if (f != null) f.Dispose(); } catch { }
            }
            base.Dispose(disposing);
        }
    }
'''

idx = src.rfind(nl + "}")
assert idx > 0, "文件尾部未匹配"
src = src[:idx] + nl + nl + SPLASH.strip("\n").replace("\n", nl) + nl + src[idx:]

io.open(DST, "w", encoding="utf-8-sig", newline="").write(src)
print("written:", DST, os.path.getsize(DST))
