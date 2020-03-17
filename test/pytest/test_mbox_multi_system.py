import serial
import subprocess
import pytest
from pexpect.fdpexpect import fdspawn

@pytest.mark.timeout(400)
@pytest.mark.parametrize('core_num', range(8))
def test_rtps_hpps(qemu_instance_per_mdl, host, core_num):
    tester_remote_path = '/opt/hpsc-utils/mbox-server-tester'
    
    qemu_instance_per_mdl['serial1'].sendline('test_mbox_rtps_hpps 3 4')
    assert(qemu_instance_per_mdl['serial1'].expect('TEST: test_mbox_rtps_hpps: begin') == 0)

    out = subprocess.run(['ssh', host] + [tester_remote_path] + ['-c', str(core_num)], universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    assert(qemu_instance_per_mdl['serial1'].expect('TEST: test_mbox_rtps_hpps: success') == 0)

    assert out.returncode == 64 #hpps returns number of bytes sent. we expect 64 bytes
