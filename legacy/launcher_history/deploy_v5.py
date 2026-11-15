# -*- coding: utf-8 -*-
"""部署 v5 启动器 + 更新使用说明 + 生成分享包"""
import os, shutil, zipfile, io
from PIL import Image

TEMP = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(TEMP), "output", "Voicemeeter8_CN")
os.makedirs(OUT, exist_ok=True)

exe_src = os.path.join(TEMP, "VM8CN_Launcher_v5.exe")
exe_dst = os.path.join(OUT, "Voicemeeter8中文启动器.exe")

# 备份旧版
old = exe_dst
if os.path.exists(old):
    bak = os.path.join(TEMP, "VM8CN_Launcher_v4_backup.exe")
    if not os.path.exists(bak):
        shutil.copy2(old, bak)
        print("旧版已备份:", bak)

shutil.copy2(exe_src, exe_dst)
print("部署 exe:", exe_dst, os.path.getsize(exe_dst))

# 预览图
img_src = os.path.join(TEMP, "v5_splash_2.png")
img_dst = os.path.join(OUT, "启动界面预览.png")
Image.open(img_src).save(img_dst, "PNG")
print("预览图:", img_dst, os.path.getsize(img_dst))

DOC = """Voicemeeter Potato 3.1.3 中文启动器 V1.0  使用说明
================================================================

一、这是什么
本启动器用于把 Voicemeeter Potato 3.1.3（64 位）的字符串型界面文本显示为简体中文。
它不改动硬盘上的任何 exe 文件，避免触发程序内置的文件完整性校验
（直接改盘会导致启动约 10 秒后崩溃）。

二、启动界面（本版新增）
双击启动器后，会先出现一个启动画面，约 5 秒后自动淡出，然后才开始启动 Voicemeeter。
启动画面上显示的分享信息：

    制作：杨爽工作室
    制作工具：Marvis
    适用版本：Voicemeeter Potato 8.x (64 位)

- 启动画面纯展示，不写任何文件、不联网。
- 想马上继续，可以在启动画面上点一下鼠标，它会立即关闭。
- 启动画面消失后，启动器才进入真正的启动流程。

三、使用方法
1. 本机需已安装 Voicemeeter Potato（默认安装目录 C:\\Program Files (x86)\\VB\\Voicemeeter\\）。
   启动器会自动在标准安装目录中查找 voicemeeter8x64.exe。
2. 双击「Voicemeeter8中文启动器.exe」，系统弹出 UAC 提示时选择「是」。
   （启动器需要管理员权限，否则无法写入目标进程内存，汉化会失败。）
3. 看完启动画面后，启动器以挂起方式拉起 voicemeeter8x64.exe，
   向进程内存写入中文文本后再恢复运行，随后正常出现中文界面。
4. 请始终通过本启动器启动 Voicemeeter；直接双击原 exe 仍为英文界面。

四、已汉化范围（1043 条字符串）
- 主菜单 / 右键菜单 / 下拉列表项
- 系统设置、选项面板、设备与驱动选择、延迟与格式下拉
- 关于 / 注册信息、许可证激活、额外 VAIO 功能许可证等对话框的标题与标签
- 各类警告与确认提示、错误提示、录音机面板、效果器参数、VBAN 网络配置、MIDI 面板
- 全部鼠标悬停提示（推子 / 静音 / 独奏 / 压缩 / 门限 / 降噪 / 变调 / 共振峰 / 限幅 / 发送等）
- 星期与月份、高低音等

五、暂未汉化的部分（技术限制，非漏做）
Voicemeeter 把界面中的一部分内容不是以「文字」存放，而是以图像形式打包在程序内部的
5 个加密资源块中（合计约 8.3 MB，实测数据熵 7.999，属强加密/压缩数据，运行期解密后绘制）。
这类内容包括：
- 主界面混音台上的固定标注（POTATO、COMP / GATE / DENOISER、INTELLIPAN、EQ、VOICE、
  HARDWARE OUT、MASTER SECTION、MONO / SOLO / MUTE 等）
- 内置插件面板（Multiband Compressor、Reverb、MultiTap Delay 等）上的全部文字
- 部分对话框的正文描述（如 VAIO 许可证购买说明、VISA / PayPal 图标、网址等）

对这些内容做「文字替换」在技术上无效（它们在文件里根本不是文字）；要汉化只能解密上述
加密资源包并重绘图片，成本高且不保证成功。

六、必须保留英文的内容
内部控件标识符、Voicemeeter API 参数名、XML 配置键、注册表路径、GUID、
设备与驱动名称（VB-Audio Voicemeeter VAIO、WDM / KS / MME / ASIO 等）、
日志与命令行调试串——这些若被翻译会导致程序功能异常，故一律保留原文。

七、常见问题
Q：启动画面没出现 / 一闪就没了？
A：画面停留约 5 秒后自动淡出；若点了鼠标也会立即关闭，属正常现象。

Q：启动后仍显示英文？
A：说明启动器没拿到管理员权限，内存写入被拒绝；请右键以管理员身份运行。

Q：启动后约 10 秒崩溃？
A：说明安装目录下的 voicemeeter8x64.exe 已被改过（旧版汉化补丁）。请用同目录的
   voicemeeter8x64.exe1（原厂文件）覆盖回 voicemeeter8x64.exe，再使用本启动器。

Q：提示「Voicemeeter 正在运行」？
A：启动器需要先关闭已在运行的 Voicemeeter 才能注入中文，选择「是」会自动关闭并重启。

Q：能否把本启动器改名 / 放别处 / 发给别人？
A：可以，位置随意，也可以直接把这个 exe 发给别人；但对方电脑上需已安装 Voicemeeter Potato，
   启动器会自动定位安装目录。

Q：会不会被杀毒软件拦截？
A：启动器会创建挂起进程并写入内存，行为与注入类工具相似，可能被误报。请加信任。

八、版本记录
- 2026-11-14  V1.0（v5）：新增 5 秒启动画面（制作 杨爽工作室 / 制作工具 Marvis），
  可点击跳过；启动流程与汉化补丁同 v4（1043 条字符串）。
- 2026-11-14  v4：补丁条目 530 → 1043 条，覆盖激活/许可证对话框、选项面板、错误提示、
  VBAN / MIDI / 录音机 / 效果器等。字符串层已基本覆盖；图像层受加密资源限制。

（内容由AI生成，仅供参考）
"""

doc_path = os.path.join(OUT, "使用说明.txt")
io.open(doc_path, "w", encoding="utf-8-sig", newline="\r\n").write(DOC)
print("说明:", doc_path, os.path.getsize(doc_path))

# 分享包
zp = os.path.join(OUT, "Voicemeeter中文启动器_V1.0_分享包.zip")
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(exe_dst, "Voicemeeter中文启动器/Voicemeeter8中文启动器.exe")
    z.write(doc_path, "Voicemeeter中文启动器/使用说明.txt")
    z.write(img_dst, "Voicemeeter中文启动器/启动界面预览.png")
print("分享包:", zp, os.path.getsize(zp))
