# Voicemeeter Potato 中文启动器（VM8CN）

[![Release](https://img.shields.io/github/v/release/yangshuang9889/voicemeeter-zh?label=release)](https://github.com/yangshuang9889/voicemeeter-zh/releases/latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20x64-blue.svg)](#)

给 VB-Audio Voicemeeter Potato 做界面汉化的 Windows 启动器：**不改磁盘文件，只在进程内存里替换字符串**。
双击启动器 → Voicemeeter 以中文界面启动；退出后原程序仍是英文，程序本体零改动。

- 当前版本：**V1.2**（启动器 v8）｜补丁规模 1043 条字符串｜目标程序 Voicemeeter Potato 3.1.3.0 x64
- 技术细节 / 构建步骤 / 排错表：[docs/开发手册.md](docs/开发手册.md)
- 版本变更：[CHANGELOG.md](CHANGELOG.md)

## 功能

| 功能 | 说明 | 起始版本 |
| --- | --- | --- |
| 界面汉化 | 启动时挂起目标进程 → 按 PE 节表算 RVA 写入中文 → 恢复线程，共 1043 条字符串 | V1.0 |
| 启动画面 | 600×520 自绘无边框画面，5 秒淡出，点一下立即跳过 | V1.0 |
| 授权与激活帮助 | 6 页离线面板：挑战码 / 足迹 / REGEN / 异常排查 / 免责 | V1.1 |
| 打开激活日志目录 | 直达「我的文档\Voicemeeter」并选中日志文件 | V1.1 |
| 打开配置目录 | 一键打开 `%APPDATA%` 并选中 `VoiceMeeterPotatoDefault.xml` | V1.2 |
| 命令行 | `--license` 直接开帮助面板，不启动 Voicemeeter | V1.1 |

## 下载与安装

普通用户无需改代码，直接取打包好的分享包即可：

- 最新版下载页：[Releases](https://github.com/yangshuang9889/voicemeeter-zh/releases/latest)
- 资产：`Voicemeeter中文启动器_V1.2_分享包.zip`（约 125 KB），解压后包含
  `Voicemeeter8中文启动器.exe`、`使用说明.txt`、`分享介绍.md`、`启动界面预览.png`

> 仓库内**不包含** VB-Audio 原版程序，也不包含修改后的 exe；请先从
> [VB-Audio 官网](https://vb-audio.com/Voicemeeter/potato.htm) 自行安装原版 Voicemeeter Potato。

## 使用

1. 本机已安装 Voicemeeter Potato 8.x 64 位（默认安装目录 `C:\Program Files (x86)\VB\Voicemeeter\`）；
2. 运行 `Voicemeeter8中文启动器.exe`，UAC 提权点「是」（内存写入需要管理员权限）；
3. 关闭 Voicemeeter 后即回到原版英文。

> 杀软可能误报：启动器会 `CreateProcess` 挂起 + `WriteProcessMemory`，行为特征与注入类工具相同，
> 属正常现象，请加信任。本工具不联网、不写注册表、不在程序目录留文件。

## 从源码构建

环境：Windows 10 / 11 x64、.NET Framework 4.x（用系统自带
`C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe`）、Python 3.8+。

```powershell
python src\patch\gen_blob4.py            # 1) 翻译表 -> base64 blob（需原始 exe 基准，见下）
python src\launcher\gen_v8.py            # 2) Launcher_v7.cs -> Launcher_v8.cs（嵌入 blob 与文案）
python src\launcher\deploy_v8.py         # 3) 编译 + 校验 + 部署 dist + 刷预览图
python src\launcher\update_docs_v8.py    # 4) 交付文档升版
python src\launcher\pack_v8.py           # 5) 打分享包 zip 并校验
```

单独编译启动器：

```powershell
csc.exe /nologo /target:winexe /platform:x64 /optimize+ /win32manifest:app.manifest `
        /r:System.dll /r:System.Drawing.dll /r:System.Windows.Forms.dll `
        /out:Voicemeeter8中文启动器.exe Launcher_v8.cs
```

> 重新生成 blob 需要一份 **VB-Audio 原版 `voicemeeter8x64.exe`** 作补丁基准
> （`src\patch\gen_blob4.py` 的 `ORIG` 常量）。该文件版权归 VB-Audio，**不随仓库分发**，
> 请自行从官网安装取得。仓库只包含翻译数据与生成脚本。

## 目录结构

| 路径 | 内容 |
| --- | --- |
| `src\launcher\` | 现役构建链：`app.manifest`、`Launcher_v7.cs`（v8 输入）、`Launcher_v8.cs`、`gen_v8.py`、`deploy_v8.py`、`pack_v8.py`、`update_docs_v8.py` |
| `src\patch\` | 翻译数据（`patch_table.json`、`extra_zh*.py`、`utf16_zh.py`）与 blob 生成链（`gen_blob*.py`） |
| `src\analysis\` | 静态扫描、资源枚举、偏移定位脚本与扫描数据 |
| `src\test\` | 窗口截图 / 按钮点击验证脚本（`shot_v8.ps1`、`click_v8.ps1`） |
| `docs\` | 开发手册（架构、PE 内存补丁原理、排错、版本记录） |
| `dist\` | 交付物：启动器 exe、使用说明、分享介绍、预览图、分享包 zip（产物不入库） |
| `legacy\` | 历史版本：早期启动器源码脚本、旧版二进制、已废弃的「直接改 exe」方案 |
| `_private\` | 不入库：VB-Audio 原版 exe 与重复副本 |

## 硬约束（改代码前必读）

1. 磁盘上的 `voicemeeter8x64.exe` **一个字节都不能改** —— 直接改盘约 10 秒后崩溃（`0xC0000005` / `0xC000041D`），
   必须走「挂起创建进程 → 按 RVA 写内存 → `ResumeThread`」；
2. `RVA = 文件偏移 - 节原始大小偏移 + 节虚拟地址`，写内存前必须先解析 PE 节表；
3. 中文编码后长度不得超过原字符串容量，**超长条目跳过而非截断**（截断会破坏相邻字符串）；
4. 生成脚本的 `ORIG` 常量指向 `...\VB\Voicemeeter\voicemeeter8x64.exe1`（官方安装后自带备份），换版本必须同步改；
5. 主界面混音台与插件面板的图形文字在 RCDATA 100–104 加密资源里，字符串层补丁覆盖不到；
6. 自绘 UI 验证一律用 `PrintWindow(hWnd, hdc, 2)` 按窗口句柄截图，不要靠肉眼盯全屏截图。

## 合规边界

- 启动器只做**界面语言辅助**，不修改、不绕过、不模拟 Voicemeeter 的任何授权校验逻辑，也不能代替正版授权；
- 不内嵌、不分发任何响应码、硬件足迹文件或授权数据；
- 涉及价格、授权次数、规则的内容一律标注「以 VB-Audio 官方页面为准」；
- 仓库与分发包内不含 Voicemeeter 任何原始文件，也不含修改后的 exe。

## 许可

本项目源码采用 [MIT License](LICENSE)。
Voicemeeter 及其相关商标、程序版权归 VB-Audio Software 所有，本项目与 VB-Audio 无任何隶属关系。

制作：杨爽工作室 ｜ 制作工具：Marvis ｜ 实测环境：Windows 11 Build 26200 + Voicemeeter Potato 3.1.3 x64
