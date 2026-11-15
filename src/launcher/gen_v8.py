# -*- coding: utf-8 -*-
"""生成 Launcher_v8.cs：在 Launcher_v7.cs 基础上加入「一键打开配置目录并选中」。

V1.2 新增（相比 v7）：
  1. 启动画面底部右侧新增圆角按钮「打开配置目录」（CBtnRect）
  2. 授权与激活帮助面板底部新增「打开配置目录」按钮（原 3 按钮重排为 4）
  3. 新增静态类 ConfigInfo：ConfigFile() / OpenConfigDir()
     OpenConfigDir 用 explorer.exe /select 打开 %APPDATA% 并选中 VoiceMeeterPotatoDefault.xml
  4. 启动画面副标题版本串 V1.1 -> V1.2

用法：python src\launcher\gen_v8.py
前置：src\launcher\Launcher_v7.cs 存在
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "Launcher_v7.cs")
DST = os.path.join(HERE, "Launcher_v8.cs")

CONFIG_CLASS = '''    static class ConfigInfo
    {
        static string ConfigFile()
        {
            return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                "VoiceMeeterPotatoDefault.xml");
        }

        internal static void OpenConfigDir()
        {
            try
            {
                string f = ConfigFile();
                string dir = Path.GetDirectoryName(f);
                if (File.Exists(f))
                {
                    Process.Start("explorer.exe", "/select,\\"" + f + "\\"");
                }
                else if (Directory.Exists(dir))
                {
                    Process.Start("explorer.exe", "\\"" + dir + "\\"");
                    MessageBox.Show("未找到配置文件：\\n" + f +
                        "\\n\\n已打开所在目录。首次启动 Voicemeeter 后会在此生成默认配置文件。",
                        "打开配置目录", MessageBoxButtons.OK, MessageBoxIcon.Information);
                }
                else
                {
                    MessageBox.Show("未找到配置目录：\\n" + dir,
                        "打开配置目录", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show("打开配置目录失败：" + ex.Message,
                    "打开配置目录", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            }
        }
    }

    class SplashForm : Form
'''


def rep(s, old, new, cnt=1):
    n = s.count(old)
    assert n == cnt, "match %d != %d for: %r" % (n, cnt, old[:70])
    return s.replace(old, new, cnt)


def build(s):
    # 1) 版本串
    s = rep(s, '"中文界面启动器  ·  V1.1  免安装分享版"',
               '"中文界面启动器  ·  V1.2  免安装分享版"')

    # 2) 启动画面：新增配置按钮矩形
    s = rep(s, """                return new Rectangle(40, py - 48, 340, 32);
            }
        }
""",
            """                return new Rectangle(40, py - 48, 340, 32);
            }
        }

        Rectangle CBtnRect
        {
            get
            {
                int py = H - 84;
                return new Rectangle(392, py - 48, 168, 32);
            }
        }
""")

    # 3) 启动画面：点击命中（配置按钮不关闭窗口、不进入帮助面板）
    s = rep(s, """            if (LBtnRect.Contains(e.Location)) LicenseRequested = true;
            ticker.Stop();
            Close();""",
            """            if (CBtnRect.Contains(e.Location)) { ConfigInfo.OpenConfigDir(); return; }
            if (LBtnRect.Contains(e.Location)) LicenseRequested = true;
            ticker.Stop();
            Close();""")

    # 4) 启动画面：绘制第二个按钮
    s = rep(s, """                using (SolidBrush b = new SolidBrush(FgMain))
                    g.DrawString("授权与激活帮助（挑战码 / 足迹 / REGEN）", fBullet, b, lb, sf);
            }
""",
            """                using (SolidBrush b = new SolidBrush(FgMain))
                    g.DrawString("授权与激活帮助（挑战码 / 足迹 / REGEN）", fBullet, b, lb, sf);
            }

            Rectangle cb = CBtnRect;
            using (GraphicsPath gp = Round(cb, 9))
            {
                using (SolidBrush b = new SolidBrush(Color.FromArgb(26, Accent2))) g.FillPath(b, gp);
                using (Pen p = new Pen(Color.FromArgb(120, Accent2), 1.2f)) g.DrawPath(p, gp);
            }
            using (StringFormat sf2 = new StringFormat())
            {
                sf2.Alignment = StringAlignment.Center;
                sf2.LineAlignment = StringAlignment.Center;
                using (SolidBrush b = new SolidBrush(FgMain))
                    g.DrawString("打开配置目录", fBullet, b, cb, sf2);
            }
""")

    # 5) 命名空间级新增 ConfigInfo 静态类
    s = rep(s, "    class SplashForm : Form\n", CONFIG_CLASS)

    # 6) 帮助面板底部：3 按钮 -> 4 按钮
    s = rep(s, """            Button bOpen = MkBtn("打开激活日志目录", 20, 12, 156);
            bOpen.Click += OpenLogDir;
            foot.Controls.Add(bOpen);

            Button bCopy = MkBtn("复制日志路径", 188, 12, 124);
            bCopy.Click += CopyLogPath;
            foot.Controls.Add(bCopy);

            Button bClose = MkBtn("关闭", 324, 12, 92);""",
            """            Button bOpen = MkBtn("打开激活日志目录", 20, 12, 148);
            bOpen.Click += OpenLogDir;
            foot.Controls.Add(bOpen);

            Button bCopy = MkBtn("复制日志路径", 176, 12, 112);
            bCopy.Click += CopyLogPath;
            foot.Controls.Add(bCopy);

            Button bCfg = MkBtn("打开配置目录", 296, 12, 124);
            bCfg.Click += delegate { ConfigInfo.OpenConfigDir(); };
            foot.Controls.Add(bCfg);

            Button bClose = MkBtn("关闭", 428, 12, 80);""")
    return s


def main():
    raw = io.open(SRC, "r", encoding="utf-8", newline="").read()
    out = build(raw)
    io.open(DST, "w", encoding="utf-8", newline="").write(out)
    print("[gen]", DST)
    print("[size]", os.path.getsize(SRC), "->", os.path.getsize(DST), "delta", len(out) - len(raw))


if __name__ == "__main__":
    main()
