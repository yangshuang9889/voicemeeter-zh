# -*- coding: utf-8 -*-
r"""把 dist 下两份交付文档升到 V1.2：标题/副标题/版本记录 + 新增「打开配置目录」章节。

用法：python src\launcher\update_docs_v8.py
前置：deploy_v8.py 已执行（exe 已是 v8）
"""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIST = os.path.join(ROOT, "dist")
TXT = os.path.join(DIST, "使用说明.txt")
MD = os.path.join(DIST, "分享介绍.md")

SEP = "━" * 36

TXT_SECTION = """{sep}

【V1.2 新增】一键打开配置目录

Voicemeeter 的设置（设备选择、混音路由、效果器参数）保存在当前用户
的配置目录里：

    %APPDATA%\\VoiceMeeterPotatoDefault.xml

实际路径示例：
    C:\\Users\\你的用户名\\AppData\\Roaming\\VoiceMeeterPotatoDefault.xml

现在有两个入口可以一键定位到它：

    1. 启动画面右下角按钮「打开配置目录」
    2. 授权与激活帮助面板底部的「打开配置目录」

点一下，资源管理器会打开所在目录并自动选中该 XML 文件。

什么时候用得上
· 换电脑 / 重装系统前，先把这个 XML 备份下来，回头直接覆盖还原；
· 调好一套混音参数，想把配置文件发给朋友；
· 参数改乱了，想对比备份和当前的差异。

两点说明
1. 文件不存在时（从未启动过 Voicemeeter），会先打开目录并提示，
   启动一次 Voicemeeter 后会自动生成；
2. 该 XML 属于当前 Windows 用户，换用户账号路径会不同。

{sep}

""".format(sep=SEP)

MD_SECTION = """
## 八、V1.2 新增：一键定位默认配置文件

Voicemeeter 的设备选择与混音参数，都保存在当前用户的这一份文件里：

```
%APPDATA%\\VoiceMeeterPotatoDefault.xml
```

启动画面右下角、以及授权与激活帮助面板底部，各有一个「打开配置目录」按钮，
点一下就会打开资源管理器并自动选中该 XML 文件。

- 换电脑 / 重装系统前：先备份这个 XML，回头覆盖即可还原整套参数；
- 调好一套混音想分享给朋友：直接把 XML 发过去；
- 参数改乱了：对比备份与当前文件，找出改动的项。

文件不存在时（从未启动过 Voicemeeter）会先打开目录并提示，启动一次即自动生成。
"""


def patch_txt():
    s = io.open(TXT, "r", encoding="utf-8-sig", newline="").read()
    n0 = len(s)
    old = "Voicemeeter Potato 中文界面启动器 V1.1   使用说明"
    assert old in s
    s = s.replace(old, "Voicemeeter Potato 中文界面启动器 V1.2   使用说明", 1)

    old = "    副标题：中文界面启动器 · V1.1 免安装分享版"
    assert old in s
    s = s.replace(old, "    副标题：中文界面启动器 · V1.2 免安装分享版", 1)

    anchor = "- 2026-11-16  V1.1（v7）："
    assert anchor in s
    s = s.replace(anchor,
                  "- 2026-11-16  V1.2（v8）：启动画面与帮助面板新增「打开配置目录」，\n"
                  "  一键打开 %APPDATA% 并选中 VoiceMeeterPotatoDefault.xml\n"
                  + anchor, 1)

    # 帮助面板底部：3 按钮 -> 4 按钮
    old_btns = ("底部三个按钮\n"
                "· 打开激活日志目录   直达「我的文档\\Voicemeeter」，有日志时直接选中文件\n"
                "· 复制日志路径       把 Voicemeeter_ActivationLog.dat 完整路径复制到剪贴板\n"
                "· 关闭\n")
    new_btns = ("底部四个按钮\n"
                "· 打开激活日志目录   直达「我的文档\\Voicemeeter」，有日志时直接选中文件\n"
                "· 复制日志路径       把 Voicemeeter_ActivationLog.dat 完整路径复制到剪贴板\n"
                "· 打开配置目录       打开 %APPDATA% 并选中 VoiceMeeterPotatoDefault.xml\n"
                "· 关闭\n")
    if old_btns in s:
        s = s.replace(old_btns, new_btns, 1)
        print("[txt] 按钮说明已更新为四按钮")

    anchor2 = "【V1.1 新增】授权与激活帮助面板"
    assert anchor2 in s
    s = s.replace(anchor2, TXT_SECTION + anchor2, 1)

    io.open(TXT, "w", encoding="utf-8-sig", newline="").write(s)
    print("[txt]", TXT, n0, "->", len(s))


def patch_md():
    s = io.open(MD, "r", encoding="utf-8", newline="").read()
    n0 = len(s)
    old = "# Voicemeeter Potato 中文界面启动器 V1.1"
    assert old in s
    s = s.replace(old, "# Voicemeeter Potato 中文界面启动器 V1.2", 1)

    old = "| 权限要求 | 需管理员权限（UAC 点击「是」） |"
    assert old in s
    s = s.replace(old,
                  "| 配置定位 | 一键打开 %APPDATA% 并选中 VoiceMeeterPotatoDefault.xml（V1.2） |\n" + old, 1)

    s = s.rstrip("\r\n") + "\r\n" + MD_SECTION.replace("\n", "\r\n")
    io.open(MD, "w", encoding="utf-8", newline="").write(s)
    print("[md]", MD, n0, "->", len(s))


if __name__ == "__main__":
    patch_txt()
    patch_md()
