# -*- coding: utf-8 -*-
"""生成 C# 启动器源码。"""
import os

TEMP = os.path.dirname(os.path.abspath(__file__))
b64 = open(os.path.join(TEMP, "patch_blob_b64.txt"), encoding="utf-8").read().strip()
chunks = [b64[i:i+900] for i in range(0, len(b64), 900)]
b64_lines = "\n".join('        + "%s"' % c for c in chunks)
b64_expr = b64_lines.lstrip(" +")

CS = r'''using System;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Windows.Forms;

namespace VM8CN
{
    static class Program
    {
        const uint CREATE_SUSPENDED = 0x00000004;
        const uint PAGE_EXECUTE_READWRITE = 0x40;

        [StructLayout(LayoutKind.Sequential)]
        struct STARTUPINFO
        {
            public int cb; public IntPtr lpReserved; public IntPtr lpDesktop; public IntPtr lpTitle;
            public int dwX, dwY, dwXSize, dwYSize, dwXCountChars, dwYCountChars, dwFillAttribute, dwFlags;
            public short wShowWindow, cbReserved2; public IntPtr lpReserved2;
            public IntPtr hStdInput, hStdOutput, hStdError;
        }

        [StructLayout(LayoutKind.Sequential)]
        struct PROCESS_INFORMATION { public IntPtr hProcess, hThread; public int dwProcessId, dwThreadId; }

        [StructLayout(LayoutKind.Sequential)]
        struct PROCESS_BASIC_INFORMATION
        {
            public IntPtr ExitStatus; public IntPtr PebBaseAddress; public IntPtr AffinityMask;
            public IntPtr BasePriority; public IntPtr UniqueProcessId; public IntPtr InheritedFromUniqueProcessId;
        }

        [DllImport("ntdll.dll")]
        static extern int NtQueryInformationProcess(IntPtr h, int cls, ref PROCESS_BASIC_INFORMATION pbi, int len, out int ret);
        [DllImport("kernel32.dll", SetLastError = true)]
        static extern bool ReadProcessMemory(IntPtr h, IntPtr addr, byte[] buf, IntPtr size, out IntPtr read);
        [DllImport("kernel32.dll", SetLastError = true)]
        static extern bool WriteProcessMemory(IntPtr h, IntPtr addr, byte[] buf, IntPtr size, out IntPtr written);
        [DllImport("kernel32.dll", SetLastError = true)]
        static extern IntPtr VirtualProtectEx(IntPtr h, IntPtr addr, IntPtr size, uint newProtect, out uint oldProtect);
        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Ansi)]
        static extern bool CreateProcess(string app, string cmd, IntPtr pa, IntPtr ta, bool inherit,
            uint flags, IntPtr env, string cwd, ref STARTUPINFO si, out PROCESS_INFORMATION pi);
        [DllImport("kernel32.dll")]
        static extern uint ResumeThread(IntPtr hThread);
        [DllImport("kernel32.dll")]
        static extern bool CloseHandle(IntPtr h);
        [DllImport("kernel32.dll")]
        static extern IntPtr OpenProcess(uint access, bool inherit, int pid);

        static readonly string BLOB =
''' + b64_expr + r''';

        [STAThread]
        static int Main(string[] args)
        {
            string exePath = args.Length > 0 ? args[0] : FindTarget();
            if (exePath == null || !File.Exists(exePath))
            {
                MessageBox.Show("未找到 voicemeeter8x64.exe。\n\n默认路径：\nC:\\Program Files (x86)\\VB\\Voicemeeter\\voicemeeter8x64.exe",
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

            bool patched = false;
            try { patched = ApplyPatches(pi.hProcess); }
            catch { patched = false; }

            ResumeThread(pi.hThread);
            CloseHandle(pi.hThread);
            CloseHandle(pi.hProcess);

            if (!patched)
                MessageBox.Show("界面汉化补丁未能应用，程序已按原版（英文）启动。", "Voicemeeter 中文启动器",
                    MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return 0;
        }

        static string FindTarget()
        {
            string[] cands = {
                @"C:\Program Files (x86)\VB\Voicemeeter\voicemeeter8x64.exe",
                @"C:\Program Files\VB\Voicemeeter\voicemeeter8x64.exe",
                Path.Combine(Path.GetDirectoryName(Application.ExecutablePath), "voicemeeter8x64.exe")
            };
            foreach (var c in cands) if (File.Exists(c)) return c;
            return null;
        }

        static bool ApplyPatches(IntPtr hProc)
        {
            PROCESS_BASIC_INFORMATION pbi = new PROCESS_BASIC_INFORMATION();
            int ret;
            if (NtQueryInformationProcess(hProc, 0, ref pbi, Marshal.SizeOf(typeof(PROCESS_BASIC_INFORMATION)), out ret) != 0)
                return false;
            byte[] buf = new byte[8]; IntPtr got;
            if (!ReadProcessMemory(hProc, (IntPtr)((long)pbi.PebBaseAddress + 0x10), buf, (IntPtr)8, out got))
                return false;
            long imageBase = BitConverter.ToInt64(buf, 0);
            if (imageBase == 0) return false;

            byte[] blob = Convert.FromBase64String(BLOB.Replace("\n", "").Replace("\r", ""));
            int pos = 0, ok = 0, total = 0;
            while (pos + 6 <= blob.Length)
            {
                uint rva = BitConverter.ToUInt32(blob, pos); pos += 4;
                ushort len = BitConverter.ToUInt16(blob, pos); pos += 2;
                if (pos + len > blob.Length) break;
                byte[] data = new byte[len + 1];
                Array.Copy(blob, pos, data, 0, len);
                data[len] = 0;
                pos += len;
                total++;

                IntPtr addr = (IntPtr)(imageBase + rva);
                long pageStart = (long)addr & ~0xFFF;
                IntPtr pageEnd = (IntPtr)(((long)addr + data.Length + 0xFFF) & ~0xFFF);
                uint old;
                VirtualProtectEx(hProc, (IntPtr)pageStart, (IntPtr)((long)pageEnd - pageStart), PAGE_EXECUTE_READWRITE, out old);
                IntPtr written;
                if (WriteProcessMemory(hProc, addr, data, (IntPtr)data.Length, out written)) ok++;
            }
            return ok > total * 8 / 10;
        }
    }
}
'''

out = os.path.join(TEMP, "Launcher.cs")
open(out, "w", encoding="utf-8-sig").write(CS)
print("已生成", out, len(CS), "字符")
