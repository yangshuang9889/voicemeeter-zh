---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: b39d940f30a0c1cf547a23c927f28498_0c278b2ce13611f1a768525400cd780f
    ReservedCode1: 8wSjB0G4eQugnI4efd0+ay8f3MFi/66AP/hH/ZKuCzxU/+MPzFfLlbVadluY1GDemqCoOrN6ZATYROzXEP2QzlsS3u2vTqDooWgxIsFYriEzvQhBhvpayXvPnUyqyw9g6IvKPeLUeDQgbqHeMUloRq7TKnkXQQV5On/qke7mmrEzrGCSq0hTHqn/S3k=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: b39d940f30a0c1cf547a23c927f28498_0c278b2ce13611f1a768525400cd780f
    ReservedCode2: 8wSjB0G4eQugnI4efd0+ay8f3MFi/66AP/hH/ZKuCzxU/+MPzFfLlbVadluY1GDemqCoOrN6ZATYROzXEP2QzlsS3u2vTqDooWgxIsFYriEzvQhBhvpayXvPnUyqyw9g6IvKPeLUeDQgbqHeMUloRq7TKnkXQQV5On/qke7mmrEzrGCSq0hTHqn/S3k=
---



# Voicemeeter Potato 中文启动器（VM8CN）

不改磁盘文件、只在内存里换字的中文界面方案。双击启动器 → Voicemeeter 以中文界面启动；关掉即恢复原版英文，程序本体零改动。

- 版本：V1.1（启动器 v7） ｜ 补丁规模：1043 条字符串 ｜ 目标程序：Voicemeeter Potato 3.1.3.0 x64
- 完整技术细节、构建步骤、排错表：见 [docs/开发手册.md](docs/开发手册.md)

## 目录

| 目录 | 内容 |
| --- | --- |
| `dist\` | 交付物：启动器 exe、使用说明.txt、分享介绍.md、启动界面预览.png、V1.1 分享包 zip |
| `src\patch\` | 翻译数据（patch_table.json / extra_zh*.py / utf16_zh.py）与 blob 生成链（gen_blob*.py） |
| `src\launcher\` | C# 启动器源码（Launcher_v6.cs）、源码生成脚本（gen_v6.py）、编译部署脚本（deploy_v6.py） |
| `src\analysis\` | 静态扫描、资源枚举、偏移定位脚本及扫描数据 |
| `src\test\` | 内存补丁验证、窗口截图、各版本验收脚本 |
| `legacy\` | 已废弃的"直接改 exe"方案存档（会因完整性校验崩溃，勿用） |

## 三条命令

```powershell
# 1. 改完翻译后重新生成 blob（需存在 voicemeeter8x64.exe1 原始备份）
python src\patch\gen_blob4.py

# 2. 把 blob 嵌进启动器源码
python src\launcher\gen_v6.py

# 3. 编译 + 写文档 + 打 zip
python src\launcher\deploy_v6.py
```

编译命令（deploy 脚本内部调用）：

```powershell
csc.exe /nologo /target:winexe /platform:x64 /optimize+ /win32manifest:app.manifest `
        /r:System.dll /r:System.Drawing.dll /r:System.Windows.Forms.dll `
        /out:VM8CN_Launcher_v6.exe Launcher_v6.cs
```

## 硬约束

1. 磁盘上的 `voicemeeter8x64.exe` 一个字节都不能改，否则启动约 10 秒崩溃（0xC0000005 / 0xC000041D）；
2. 生成脚本的 `ORIG` 常量指向 `...\VB\Voicemeeter\voicemeeter8x64.exe1`，换版本必须同步改；
3. 中文编码后长度不得超过原字符串容量，超长条目一律跳过而非截断；
4. 主界面混音台与插件面板图形文字在 RCDATA 100–104 加密资源里，字符串层补丁覆盖不到。
*（内容由AI生成，仅供参考）*
*（内容由AI生成，仅供参考）*

## V1.1 新增：授权与激活帮助

| 项 | 值 |
| --- | --- |
| 入口 1 | 启动画面按钮「授权与激活帮助（挑战码 / 足迹 / REGEN）」 |
| 入口 2 | 命令行 `Voicemeeter8中文启动器.exe --license` |
| 面板 | `LicenseForm`，836×699，左 6 页导航 + 右侧富文本 + 底部 3 按钮 |
| 内容常量 | `Launcher_v7.cs` 中 `T1`–`T6` 六个 string 常量 |
| 生成脚本 | `src\launcher\gen_v7.py`（基于 `Launcher_v6.cs` 改造） |
| 部署脚本 | `src\launcher\deploy_v7.py`（编译 + 校验 manifest + 部署 + 刷预览图） |

合规边界：面板只做说明与索引，不修改、不绕过 Voicemeeter 授权校验。
