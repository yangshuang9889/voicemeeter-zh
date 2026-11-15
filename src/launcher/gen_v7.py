# -*- coding: utf-8 -*-
"""生成 Launcher_v7.cs：在 v6 基础上新增「授权与激活帮助」功能。

新增内容：
1. LicenseForm —— 六页授权知识面板（挑战码/足迹恢复/REGEN/排查/历史结论）
2. 启动画面新增「授权与激活帮助」按钮（点击后打开面板，不再注入）
3. 命令行参数 --license / -license / /license / license 直接打开面板
"""
import io, os

TEMP = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(TEMP, "Launcher_v6.cs")
DST = os.path.join(TEMP, "Launcher_v7.cs")

src = io.open(SRC, "r", encoding="utf-8-sig").read()
nl = "\r\n" if "\r\n" in src else "\n"


def replace_method(text, header, new_text):
    """把以 header 开头的整个方法体替换为 new_text（含 header）。"""
    i = text.find(header)
    assert i > 0, "header not found: " + header
    j = text.find(nl + "        }" + nl, i)
    assert j > i, "method end not found: " + header
    j += len(nl + "        }" + nl)
    return text[:i] + new_text + text[j:]


# ---------- 1. 启动画面高度 462 -> 520 ----------
old = "const int W = 600, H = 462;"
assert old in src
src = src.replace(old, "const int W = 600, H = 520;", 1)
src = src.replace("中文界面启动器  ·  V1.0  免安装分享版", "中文界面启动器  ·  V1.1  免安装分享版", 1)

# ---------- 2. 新增字段与按钮矩形 ----------
old = "        int elapsed = 0;"
assert old in src
src = src.replace(old,
    "        int elapsed = 0;" + nl +
    "        public bool LicenseRequested = false;" + nl + nl +
    "        Rectangle LBtnRect" + nl +
    "        {" + nl +
    "            get" + nl +
    "            {" + nl +
    "                int py = H - 84;" + nl +
    "                return new Rectangle(40, py - 48, 340, 32);" + nl +
    "            }" + nl +
    "        }", 1)

# ---------- 3. ShowSplash 改为返回 bool ----------
old_head = "        public static void ShowSplash()"
new_splash = (
    "        public static bool ShowSplash()" + nl +
    "        {" + nl +
    "            try" + nl +
    "            {" + nl +
    "                using (SplashForm sp = new SplashForm())" + nl +
    "                {" + nl +
    "                    sp.ShowDialog();" + nl +
    "                    return sp.LicenseRequested;" + nl +
    "                }" + nl +
    "            }" + nl +
    "            catch { }" + nl +
    "            return false;" + nl +
    "        }" + nl)
src = replace_method(src, old_head, new_splash)

# ---------- 4. OnMouseClick 增加按钮命中 ----------
old_head = "        protected override void OnMouseClick(MouseEventArgs e)"
new_click = (
    "        protected override void OnMouseClick(MouseEventArgs e)" + nl +
    "        {" + nl +
    "            base.OnMouseClick(e);" + nl +
    "            if (LBtnRect.Contains(e.Location)) LicenseRequested = true;" + nl +
    "            ticker.Stop();" + nl +
    "            Close();" + nl +
    "        }" + nl)
src = replace_method(src, old_head, new_click)

# ---------- 5. OnPaint 绘制按钮 ----------
anchor = nl + "            int py = H - 84;"
assert anchor in src
draw_btn = (
    "            Rectangle lb = LBtnRect;" + nl +
    "            using (GraphicsPath gp = Round(lb, 9))" + nl +
    "            {" + nl +
    "                using (SolidBrush b = new SolidBrush(Color.FromArgb(40, Accent))) g.FillPath(b, gp);" + nl +
    "                using (Pen p = new Pen(Color.FromArgb(150, Accent2), 1.2f)) g.DrawPath(p, gp);" + nl +
    "            }" + nl +
    "            using (StringFormat sf = new StringFormat())" + nl +
    "            {" + nl +
    "                sf.Alignment = StringAlignment.Center;" + nl +
    "                sf.LineAlignment = StringAlignment.Center;" + nl +
    "                using (SolidBrush b = new SolidBrush(FgMain))" + nl +
    "                    g.DrawString(" + '"' + "授权与激活帮助（挑战码 / 足迹 / REGEN）" + '"' + ", fBullet, b, lb, sf);" + nl +
    "            }" + nl + nl)
src = src.replace(anchor, draw_btn + anchor, 1)

# ---------- 6. Main 支持 --license ----------
old = "            string exePath = args.Length > 0 ? args[0] : FindTarget();"
assert old in src
lic_branch = (
    "            if (args.Length > 0)" + nl +
    "            {" + nl +
    "                string a0 = args[0].Trim().ToLowerInvariant();" + nl +
    '                if (a0 == "--license" || a0 == "-license" || a0 == "/license" || a0 == "license")' + nl +
    "                {" + nl +
    "                    LicenseForm.ShowLicense();" + nl +
    "                    return 0;" + nl +
    "                }" + nl +
    "            }" + nl + nl)
src = src.replace(old, lic_branch + old, 1)

# ---------- 7. splash 调用处 ----------
old = "            SplashForm.ShowSplash();"
assert old in src
new_call = (
    "            if (SplashForm.ShowSplash())" + nl +
    "            {" + nl +
    "                LicenseForm.ShowLicense();" + nl +
    "                return 0;" + nl +
    "            }")
src = src.replace(old, new_call, 1)

# ---------- 8. 追加 LicenseForm ----------
T1 = r"""Voicemeeter Potato 采用「单设备绑定」的挑战码 / 响应码（Challenge / Response）授权模式，
属于捐赠式软件（Donationware）：先免费试用，长期使用需购买授权。

【挑战码 Challenge】
由软件基于电脑的 CPU、主板等核心硬件信息生成，同时受系统环境与软件版本影响。
每台设备的挑战码具有唯一性，可理解为这台电脑的「指纹编号」。

【响应码 Response】
与挑战码一一对应，只在生成它的那台设备上有效。
激活后无需联网，即可使用授权覆盖的全部功能。

【授权价格分档】
个人 / 非盈利 / 教育场景：可在 P1-P5 档位中自选。
商业 / 专业场景：需在 P3-P5 档位中选择。
采购超过 100 份：可联系官方获取定制报价。

【系统兼容】
Windows XP 至 Windows 11，覆盖 32 位 / 64 位 / ARM64 架构。

【与本启动器的关系】
本工具只做界面文本汉化，不修改、不绕过任何授权逻辑，也不能代替授权使用。
购买与激活请一律通过 VB-Audio 官方渠道。"""

T2 = r"""以下情况都可能导致挑战码变化，进而使原有响应码失效（激活失效）。

一、硬件相关变动
1. 更换 CPU 或主板 —— 最主要的触发原因，挑战码本身由它们生成。
2. BIOS 更新 —— 若更新改动了主板厂商、产品名称、BIOS 厂商等底层信息会触发；
   只做常规安全修补一般不影响，但存在风险。
3. 内存扩容 —— 极少数案例会触发（官方说明内存通常不影响挑战码）。

二、系统与设置变动
1. 重装 Windows 系统（即使同一台机器、同一块硬盘）。
2. 特定 Windows 更新（如 KB5063060 补丁、大版本系统迭代）。
3. 修改计算机名称、系统用户名。
4. 更新硬件驱动（如显卡驱动更新，已有实际触发案例）。

三、软件版本升级
1. 升级到 3.1.1.3：挑战码前缀变更为「G」。
2. 升级到 3.1.2.2：挑战码前缀变更为「H」。
3. 3.0.1.4 之前的旧版本：32 位与 64 位程序切换、Win10 常规更新、
   切换系统用户，都可能造成挑战码变动。

【预防建议】
每次准备重装系统、更换硬件、大幅更新驱动或升级 Voicemeeter 之前，
先备份一次硬件足迹文件（见「变更后怎么办」页），成本几乎为零。"""

T3 = r"""方案一：恢复硬件足迹（Footprint）—— 硬件未变更时优先

硬件足迹是设备的硬件特征文件。在 CPU 与主板均未更换的前提下，
恢复足迹可以找回原挑战码，直接复用原有响应码，不消耗任何 REGEN 次数。

备份步骤（必须在授权已激活状态下操作）
1. 打开 Voicemeeter，进入授权激活窗口。
2. 在挑战码输入框上点击鼠标右键。
3. 选择导出足迹，得到文件 VB-Audio_PCFootprint.dat。
4. 保存到 U 盘、网盘等外部存储，不要只留在系统盘。

恢复步骤
1. 打开 Voicemeeter 授权窗口，先填入当初授权绑定的邮箱地址。
2. 在挑战码输入框上点击右键，导入之前备份的 VB-Audio_PCFootprint.dat。
3. 填入原响应码，完成激活。

注意：CPU 或主板已经更换时，足迹文件无法恢复生效，只能走方案二。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

方案二：使用 REGEN 重新生成响应码

操作路径
1. 登录 VB-Audio 官方商店账户。
2. 进入 My License 页面。
3. 找到对应授权，点击 REGEN 按钮。
4. 填入当前的新挑战码，生成新的响应码。
5. 回到软件填入新响应码，完成激活。

注意：REGEN 会消耗授权的 REGEN 次数，次数为 0 时需付费购买。"""

T4 = r"""一、基础与免费赠送权益

1. 每份初始授权自带基础 REGEN 次数。
   可用于挑战码变更后重新生成响应码，也可用于激活第二台设备。

2. 官方大版本迭代时会向所有终端用户免费赠送 REGEN：
   · 2024 年 6 月（3.1.1.3 版本更新）免费发放 1 次
   · 2025 年 11-12 月（3.1.2.2 版本更新）免费发放 1 次

二、付费购买规则（2026 年 6 月起生效）

1. 当该授权的 REGEN 次数为 0 时，My License 页面会出现 BUY REGEN 按钮。
2. 单次购买价格 = 该授权最低档位价格的一半。
3. 同一授权每 90 天仅可购买一次。

【成本提醒】
频繁重装系统、频繁更新驱动，等于在持续消耗 REGEN 次数与购买成本。
硬件没变时优先用足迹备份恢复，能直接省下这笔支出。"""

T5 = r"""1. 出现原因不明的挑战码异常变更时，提取激活日志：
   我的文档 \ Voicemeeter \ Voicemeeter_ActivationLog.dat
   把该文件提交给官方排查，日志里有激活与挑战码变更记录。

2. 重装系统前建议一并备份该日志文件；
   重装系统后放回原目录，便于官方定位问题原因。

3. 授权 / 激活类问题，官方仅通过商店的联系表单处理；
   官方论坛渠道不解决授权问题，发帖基本无回应。

4. 官方客服仅支持英文沟通，不提供中文服务。
   提交时建议写清：设备型号、系统版本、授权邮箱、旧挑战码与新挑战码。

【本启动器能做什么 / 不能做什么】
可以做：查看挑战码变更原因、足迹备份恢复步骤、REGEN 规则、日志目录直达。
不能做：代为申请授权、赠送或修改 REGEN 次数、绕过任何授权校验。"""

T6 = r"""历史沟通记录核心结论（供参考）

· 2021 年 —— 因设备故障导致挑战码变更，申请额外激活次数，
  官方提供了 2 次额外 REGEN，并明确说明后续无法继续免费赠送，需重新购买授权；
  同时建议硬件不变时通过备份足迹避免重复购买。

· 2022 年 —— 更新显卡驱动后挑战码变更，因硬件层面确实发生了相关变动，
  足迹无法恢复生效，最终需重新购买授权。

· 2023 年 —— 未更换硬件但激活失效，
  官方优先建议恢复足迹备份，找回原挑战码以复用原有授权。

可提炼的三条经验
1. 硬件没变：先恢复足迹，不花 REGEN 次数。
2. 硬件已换（CPU / 主板）：足迹无效，只能用 REGEN 或重新购买。
3. 驱动 / 系统更新后失效：先怀疑挑战码已变，别急着重买授权。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

免责声明
以上内容由「杨爽工作室」整理自 VB-Audio 官方公开说明与实际沟通记录，仅供查阅参考；
授权规则、价格、次数以 VB-Audio 官方页面为准。
本启动器为第三方汉化工具，与 VB-Audio 无隶属关系。"""

LICENSE = r'''
    class LicenseForm : Form
    {
        static readonly Color LBg = Color.FromArgb(13, 19, 28);
        static readonly Color LPanel = Color.FromArgb(19, 27, 38);
        static readonly Color LEdit = Color.FromArgb(24, 33, 45);
        static readonly Color LFg = Color.FromArgb(226, 234, 243);
        static readonly Color LFgDim = Color.FromArgb(148, 170, 192);
        static readonly Color LAccent = Color.FromArgb(47, 129, 247);

        RichTextBox rtb;
        Button[] nav;

        static readonly string[] NavTitles = {
            "① 授权机制",
            "② 挑战码变更原因",
            "③ 变更后怎么办",
            "④ REGEN 权益",
            "⑤ 异常排查与支持",
            "⑥ 历史结论与免责"
        };

        static readonly string[] Bodies = { T1, T2, T3, T4, T5, T6 };

        public static void ShowLicense()
        {
            try
            {
                using (LicenseForm f = new LicenseForm()) f.ShowDialog();
            }
            catch { }
        }

        static Font LF(float sz, FontStyle st)
        {
            try { return new Font("Microsoft YaHei UI", sz, st); }
            catch { return new Font(FontFamily.GenericSansSerif, sz, st); }
        }

        public LicenseForm()
        {
            Text = "Voicemeeter 授权与激活帮助";
            ClientSize = new Size(820, 660);
            MinimumSize = new Size(760, 560);
            StartPosition = FormStartPosition.CenterScreen;
            BackColor = LBg;
            ForeColor = LFg;
            Font = LF(10f, FontStyle.Regular);
            MaximizeBox = false;
            AutoScaleMode = AutoScaleMode.None;
            KeyPreview = true;
            KeyDown += delegate(object s, KeyEventArgs ke) { if (ke.KeyCode == Keys.Escape) Close(); };

            Panel body = new Panel();
            body.Dock = DockStyle.Fill;
            body.BackColor = LBg;
            body.Padding = new Padding(14, 12, 14, 10);
            Controls.Add(body);

            Panel head = new Panel();
            head.Dock = DockStyle.Top;
            head.Height = 74;
            head.BackColor = LPanel;
            Controls.Add(head);

            Label t = new Label();
            t.Text = "Voicemeeter 授权与激活帮助";
            t.Font = LF(15f, FontStyle.Bold);
            t.ForeColor = LFg;
            t.AutoSize = true;
            t.Left = 20;
            t.Top = 12;
            head.Controls.Add(t);

            Label st = new Label();
            st.Text = "挑战码 / 响应码  ·  硬件足迹备份与恢复  ·  REGEN 规则  ·  官方支持渠道";
            st.Font = LF(9f, FontStyle.Regular);
            st.ForeColor = LFgDim;
            st.AutoSize = true;
            st.Left = 22;
            st.Top = 44;
            head.Controls.Add(st);

            Panel navp = new Panel();
            navp.Dock = DockStyle.Left;
            navp.Width = 196;
            navp.BackColor = LPanel;
            Controls.Add(navp);

            nav = new Button[NavTitles.Length];
            for (int i = 0; i < NavTitles.Length; i++)
            {
                Button b = new Button();
                b.Text = NavTitles[i];
                b.TextAlign = ContentAlignment.MiddleLeft;
                b.Padding = new Padding(14, 0, 0, 0);
                b.FlatStyle = FlatStyle.Flat;
                b.FlatAppearance.BorderSize = 0;
                b.SetBounds(10, 12 + i * 46, 176, 38);
                b.BackColor = LPanel;
                b.ForeColor = LFgDim;
                b.Font = LF(9.5f, FontStyle.Regular);
                b.Cursor = Cursors.Hand;
                int idx = i;
                b.Click += delegate { Select(idx); };
                navp.Controls.Add(b);
                nav[i] = b;
            }

            Panel foot = new Panel();
            foot.Dock = DockStyle.Bottom;
            foot.Height = 58;
            foot.BackColor = LPanel;
            Controls.Add(foot);

            rtb = new RichTextBox();
            rtb.Dock = DockStyle.Fill;
            rtb.BackColor = LEdit;
            rtb.ForeColor = LFg;
            rtb.BorderStyle = BorderStyle.None;
            rtb.ReadOnly = true;
            rtb.Font = LF(10.5f, FontStyle.Regular);
            rtb.ScrollBars = RichTextBoxScrollBars.Vertical;
            rtb.DetectUrls = false;
            rtb.WordWrap = true;
            body.Controls.Add(rtb);

            Button bOpen = MkBtn("打开激活日志目录", 20, 12, 156);
            bOpen.Click += OpenLogDir;
            foot.Controls.Add(bOpen);

            Button bCopy = MkBtn("复制日志路径", 188, 12, 124);
            bCopy.Click += CopyLogPath;
            foot.Controls.Add(bCopy);

            Button bClose = MkBtn("关闭", 324, 12, 92);
            bClose.Click += delegate { Close(); };
            foot.Controls.Add(bClose);

            Label tip = new Label();
            tip.Text = "第三方汉化工具，非 VB-Audio 官方产品";
            tip.AutoSize = true;
            tip.ForeColor = LFgDim;
            tip.Font = LF(8.5f, FontStyle.Regular);
            tip.Top = 22;
            foot.Controls.Add(tip);
            foot.Resize += delegate { tip.Left = foot.Width - tip.Width - 18; };

            Select(0);
        }

        Button MkBtn(string text, int x, int y, int w)
        {
            Button b = new Button();
            b.Text = text;
            b.FlatStyle = FlatStyle.Flat;
            b.FlatAppearance.BorderSize = 1;
            b.FlatAppearance.BorderColor = Color.FromArgb(58, 86, 116);
            b.BackColor = LEdit;
            b.ForeColor = LFg;
            b.Font = LF(9f, FontStyle.Regular);
            b.Cursor = Cursors.Hand;
            b.SetBounds(x, y, w, 32);
            return b;
        }

        void Select(int i)
        {
            for (int k = 0; k < nav.Length; k++)
            {
                bool on = (k == i);
                nav[k].BackColor = on ? Color.FromArgb(34, LAccent) : LPanel;
                nav[k].ForeColor = on ? Color.White : LFgDim;
                nav[k].Font = LF(9.5f, on ? FontStyle.Bold : FontStyle.Regular);
            }
            rtb.Text = Bodies[i];
            rtb.SelectionStart = 0;
            rtb.SelectionLength = 0;
            rtb.ScrollToCaret();
        }

        static string LogDir()
        {
            return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "Voicemeeter");
        }

        static string LogFile()
        {
            return Path.Combine(LogDir(), "Voicemeeter_ActivationLog.dat");
        }

        void OpenLogDir(object sender, EventArgs e)
        {
            try
            {
                string dir = LogDir();
                if (!Directory.Exists(dir))
                {
                    MessageBox.Show("未找到目录：\n" + dir +
                        "\n\n说明尚未产生激活日志，或本机未安装 / 未激活过 Voicemeeter。",
                        "Voicemeeter 授权与激活帮助", MessageBoxButtons.OK, MessageBoxIcon.Information);
                    return;
                }
                if (File.Exists(LogFile()))
                    Process.Start("explorer.exe", "/select,\"" + LogFile() + "\"");
                else
                    Process.Start("explorer.exe", "\"" + dir + "\"");
            }
            catch (Exception ex)
            {
                MessageBox.Show("打开目录失败：" + ex.Message,
                    "Voicemeeter 授权与激活帮助", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            }
        }

        void CopyLogPath(object sender, EventArgs e)
        {
            try
            {
                Clipboard.SetText(LogFile());
                MessageBox.Show("已复制到剪贴板：\n" + LogFile(),
                    "Voicemeeter 授权与激活帮助", MessageBoxButtons.OK, MessageBoxIcon.Information);
            }
            catch (Exception ex)
            {
                MessageBox.Show("复制失败：" + ex.Message,
                    "Voicemeeter 授权与激活帮助", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            }
        }
    }
'''

# 文本常量（C# 侧声明）
consts = []
for name, txt in (("T1", T1), ("T2", T2), ("T3", T3), ("T4", T4), ("T5", T5), ("T6", T6)):
    consts.append('        const string %s = @"%s";' % (name, txt))
const_block = nl.join(consts) + nl + nl

lic = LICENSE.strip("\n").replace("\n", nl)
# 在 LicenseForm 类开头插入文本常量
marker = "    class LicenseForm : Form" + nl + "    {" + nl
assert marker in lic
lic = lic.replace(marker, marker + const_block, 1)

idx = src.rfind(nl + "}")
assert idx > 0
src = src[:idx] + nl + nl + lic + nl + src[idx:]

io.open(DST, "w", encoding="utf-8-sig", newline="").write(src)
print("written:", DST, os.path.getsize(DST))
