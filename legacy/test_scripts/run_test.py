# -*- coding: utf-8 -*-
"""启动指定 exe，观察是否早期崩溃。抑制 WER 弹窗。"""
import ctypes, subprocess, time, sys, os

k32 = ctypes.windll.kernel32
SEM_FAILCRITICALERRORS = 0x0001
SEM_NOGPFAULTERRORBOX = 0x0002
SEM_NOALIGNMENTFAULTEXCEPT = 0x0004
SEM_NOOPENFILEERRORBOX = 0x8000

def run_test(exe, wait=7):
    cwd = os.path.dirname(exe)
    old = k32.SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX | SEM_NOOPENFILEERRORBOX)
    try:
        p = subprocess.Popen([exe], cwd=cwd)
    finally:
        k32.SetErrorMode(old)
    t0 = time.time()
    rc = None
    while time.time() - t0 < wait:
        rc = p.poll()
        if rc is not None:
            break
        time.sleep(0.3)
    if rc is None:
        print("RESULT=RUNNING_OK  存活>=%ds  pid=%d" % (wait, p.pid))
        subprocess.run(["taskkill", "/F", "/PID", str(p.pid)],
                       capture_output=True)
        time.sleep(0.5)
        print("killed")
        return "OK"
    else:
        print("RESULT=CRASH  exitcode=0x%08X (%d)  存活 %.2fs" % (rc & 0xFFFFFFFF, rc, time.time()-t0))
        return "CRASH"

if __name__ == "__main__":
    run_test(sys.argv[1])
