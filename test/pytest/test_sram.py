import serial
import subprocess
import pytest
import re
from pexpect.fdpexpect import fdspawn

testers = ["sram-tester"]

def run_tester_on_host(hostname, cmd):
    out = subprocess.run("ssh " + hostname + " " + cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, shell=True)
    return out

# This SRAM test will modify an array in SRAM, reboot HPPS (using a
# watchdog timeout), then check that the SRAM array is the same.
# Since this test will boot QEMU, then reboot QEMU, it is given more time.
@pytest.mark.timeout(800)
def test_non_volatility(qemu_instance_per_fcn, host):
    # increment the first 100 elements of the SRAM array by 2, then reboot HPPS
    out = run_tester_on_host(host, "/opt/hpsc-utils/sram-tester -s 100 -i 2")
    assert out.returncode == 0, eval(pytest.run_fail_str)
    sram_before_reboot = re.search(r'Latest SRAM contents:(.+)', out.stdout, flags=re.DOTALL).group(1)

    # currently rebooting HPPS requires having the watchdog time out
    qemu_instance_per_fcn['serial2'].sendline("taskset -c 0 /opt/hpsc-utils/wdtester /dev/watchdog0 0")
    assert(qemu_instance_per_fcn['serial2'].expect("hpsc-chiplet login: ") == 0)
    qemu_instance_per_fcn['serial2'].sendline('root')
    assert(qemu_instance_per_fcn['serial2'].expect('root@hpsc-chiplet:~# ') == 0)

    # after the reboot, read the SRAM contents to verify that they haven't changed
    out = run_tester_on_host(host, "/opt/hpsc-utils/sram-tester -s 100")
    assert out.returncode == 0, eval(pytest.run_fail_str)
    sram_after_reboot = re.search(r'Latest SRAM contents:(.+)', out.stdout, flags=re.DOTALL).group(1)
    assert(sram_before_reboot == sram_after_reboot), "SRAM array before reboot was: " + sram_before_reboot + ", while SRAM array after reboot was: " + sram_after_reboot

    # return the SRAM contents to their original state
    out = run_tester_on_host(host, "/opt/hpsc-utils/sram-tester -s 100 -i -2")
    assert out.returncode == 0, eval(pytest.run_fail_str)
