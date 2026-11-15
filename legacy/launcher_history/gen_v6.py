# -*- coding: utf-8 -*-
"""鐢熸垚 Launcher_v6.cs锛氬湪 v4 鍩虹涓婂姞鍏ヤ俊鎭洿瀹屾暣鐨?5 绉掑惎鍔ㄧ敾闈?""
import io, os

TEMP = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(TEMP, "Launcher_v4.cs")
DST = os.path.join(TEMP, "Launcher_v6.cs")

src = io.open(SRC, "r", encoding="utf-8-sig").read()
nl = "\r\n" if "\r\n" in src else "\n"

# using
old_using = "using System.Diagnostics;" + nl + "using System.IO;"
assert old_using in src
src = src.replace(old_using, "using System.Diagnostics;" + nl + "using System.Drawing;" + nl +
                  "using System.Drawing.Drawing2D;" + nl + "using System.IO;", 1)

# Main 寮€澶?old_main = '        {' + nl + '            string exePath = args.Length > 0 ? args[0] : FindTarget();'
assert old_main in src
src = src.replace(old_main,
    '        {' + nl +
    '            Application.EnableVisualStyles();' + nl +
    '            Application.SetCompatibleTextRenderingDefault(false);' + nl + nl +
    '            string exePath = args.Length > 0 ? args[0] : FindTarget();', 1)

# splash 璋冪敤
old_call = ('                return 2;' + nl + '            }' + nl + nl + '            // 宸插湪杩愯鍒欒闂?)
assert old_call in src
src = src.replace(old_call,
    '                return 2;' + nl + '            }' + nl + nl +
    '            // 鍚姩鐢婚潰锛? 绉掑悗鑷姩娑堝け' + nl +
    '            SplashForm.ShowSplash();' + nl + nl +
    '            // 宸插湪杩愯鍒欒闂?, 1)

SPLASH = r'''
    class SplashForm : Form
    {
        const int W = 600, H = 462;
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

        Font fTitle, fSub, fBody, fKey, fBullet, fSmall, fIcon, fCopy;

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
            fBullet = MkFont(9.5f, FontStyle.Regular);
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
                try { return new Font("寰蒋闆呴粦", sz, st); }
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

        void DrawInfo(Graphics g, string key, string val, float y, Color vc)
        {
            using (SolidBrush kb = new SolidBrush(FgSub)) g.DrawString(key, fKey, kb, 40f, y + 2f);
            using (SolidBrush vb = new SolidBrush(vc)) g.DrawString(val, fBody, vb, 138f, y);
        }

        void DrawBullet(Graphics g, string text, float y)
        {
            using (SolidBrush dot = new SolidBrush(Accent2))
                g.FillEllipse(dot, 42f, y + 7f, 5f, 5f);
            using (SolidBrush tb = new SolidBrush(FgMain))
                g.DrawString(text, fBullet, tb, 58f, y);
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
                gp.AddEllipse(W - 300, -200, 470, 470);
                using (PathGradientBrush pgb = new PathGradientBrush(gp))
                {
                    pgb.CenterColor = Color.FromArgb(95, Accent);
                    pgb.SurroundColors = new Color[] { Color.FromArgb(0, Accent) };
                    g.FillPath(pgb, gp);
                }
            }
            using (GraphicsPath gp = new GraphicsPath())
            {
                gp.AddEllipse(-180, H - 180, 400, 400);
                using (PathGradientBrush pgb = new PathGradientBrush(gp))
                {
                    pgb.CenterColor = Color.FromArgb(60, Accent2);
                    pgb.SurroundColors = new Color[] { Color.FromArgb(0, Accent2) };
                    g.FillPath(pgb, gp);
                }
            }

            using (Pen pen = new Pen(Color.FromArgb(120, Accent2), 2f))
                g.DrawLine(pen, 8, 1.5f, W - 8, 1.5f);

            Rectangle ico = new Rectangle(40, 40, 56, 56);
            using (GraphicsPath gp = Round(ico, 16))
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

            using (SolidBrush b = new SolidBrush(FgMain)) g.DrawString("Voicemeeter Potato", fTitle, b, 114f, 40f);
            using (SolidBrush b = new SolidBrush(FgSub)) g.DrawString("涓枃鐣岄潰鍚姩鍣? 路  V1.0  鍏嶅畨瑁呭垎浜増", fSub, b, 116f, 78f);

            using (Pen pen = new Pen(Color.FromArgb(55, 255, 255, 255)))
                g.DrawLine(pen, 40, 118, W - 40, 118);

            float y = 136f;
            DrawInfo(g, "鍒朵綔", "鏉ㄧ埥宸ヤ綔瀹?, y, Gold); y += 34f;
            DrawInfo(g, "鍒朵綔宸ュ叿", "Marvis", y, FgMain); y += 34f;
            DrawInfo(g, "閫傜敤鐗堟湰", "Voicemeeter Potato 8.x (64 浣?", y, FgMain); y += 44f;

            using (SolidBrush b = new SolidBrush(Accent2)) g.DrawString("瀹冭兘鍋氫粈涔?, fKey, b, 40f, y); y += 26f;
            DrawBullet(g, "1043 鏉＄晫闈㈡枃鏈眽鍖栵細鑿滃崟銆佽缃潰鏉裤€佸璇濇涓庢偓鍋滄彁绀?, y); y += 24f;
            DrawBullet(g, "杩愯鏃跺湪鍐呭瓨涓浛鎹紝涓嶆敼鍔ㄥ師绋嬪簭鏂囦欢锛屽叧闂嵆鎭㈠鍘熺増", y); y += 24f;
            DrawBullet(g, "閫傜敤 Windows 10 / 11锛岄渶宸插畨瑁?Voicemeeter Potato 8.x 64 浣?, y); y += 26f;

            using (SolidBrush b = new SolidBrush(FgSub))
                g.DrawString("鍚姩闇€绠＄悊鍛樻潈闄愶紙UAC 鎻愭潈锛夛紝璇峰湪鎻愮ず妗嗙偣鍑汇€屾槸銆?, fSmall, b, 40f, y);

            int py = H - 84;
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
                g.DrawString("姝ｅ湪鍑嗗涓枃鐣岄潰鈥?, fSmall, b, 40f, py + 14f);
                string right = "5 绉掑悗鑷姩寮€濮嬶紙鐐瑰嚮鐢婚潰鍙烦杩囷級";
                SizeF rs = g.MeasureString(right, fSmall);
                g.DrawString(right, fSmall, b, W - 40 - rs.Width, py + 14f);
            }

            using (SolidBrush b = new SolidBrush(CopyC))
            {
                string copy = "漏 鏉ㄧ埥宸ヤ綔瀹?  路   Powered by Marvis   路   鍏嶈垂鍒嗕韩锛岃鍕垮晢鐢?;
                SizeF cs = g.MeasureString(copy, fCopy);
                g.DrawString(copy, fCopy, b, (W - cs.Width) / 2f, H - 28f);
            }
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing)
            {
                try { ticker.Stop(); ticker.Dispose(); } catch { }
                foreach (Font f in new Font[] { fTitle, fSub, fBody, fKey, fBullet, fSmall, fIcon, fCopy })
                    try { if (f != null) f.Dispose(); } catch { }
            }
            base.Dispose(disposing);
        }
    }
'''

idx = src.rfind(nl + "}")
assert idx > 0
src = src[:idx] + nl + nl + SPLASH.strip("\n").replace("\n", nl) + nl + src[idx:]

io.open(DST, "w", encoding="utf-8-sig", newline="").write(src)
print("written:", DST, os.path.getsize(DST))

