import serial
import subprocess
import pytest
from pexpect.fdpexpect import fdspawn

def run_tester_on_host(hostname, cmd):
    out = subprocess.run("ssh " + hostname + " " + cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, shell=True)
    return out

# Verify that a file created on the NAND-based rootfs is still present after
# rebooting HPPS.
# Since this test will boot QEMU, then reboot QEMU, it is given more time.
@pytest.mark.timeout(800)
def test_non_volatility(hpps_serial_per_fnc, host):
    test_dir = "/home/root/"
    test_file = "nand_test_file"

    # create the test_file
    out = run_tester_on_host(host, "touch " + test_dir + test_file)
    assert out.returncode == 0, eval(pytest.run_fail_str)

    # currently rebooting HPPS requires having the watchdog time out
    hpps_serial_per_fnc.sendline("taskset -c 0 /opt/hpsc-utils/wdtester /dev/watchdog0 0")
    assert(hpps_serial_per_fnc.expect("hpsc-chiplet login: ") == 0)
    hpps_serial_per_fnc.sendline('root')
    assert(hpps_serial_per_fnc.expect('root@hpsc-chiplet:~# ') == 0)

    # after the reboot, check that the test_file is still there
    out = run_tester_on_host(host, "ls " + test_dir)
    assert out.returncode == 0, eval(pytest.run_fail_str)
    assert(test_file in out.stdout), "File " + test_file + " was not found among the following files listed in directory " + test_dir + ":\n" + out.stdout

    # finally, remove the test_file
    out = run_tester_on_host(host, "rm " + test_dir + test_file)
    assert out.returncode == 0, eval(pytest.run_fail_str)
