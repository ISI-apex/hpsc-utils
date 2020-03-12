import serial
import pytest
from pexpect.fdpexpect import fdspawn

@pytest.mark.timeout(400)
@pytest.mark.parametrize('core_num', range(1,8))
def test_hotplug(qemu_instance_per_mdl, core_num):
    qemu_instance_per_mdl['serial2'].sendline('root')
    cpu_path = '/sys/devices/system/cpu/'

    qemu_instance_per_mdl['serial2'].sendline('echo 0 > ' + cpu_path + 'cpu' + str(core_num) + '/online') #turn CPU core_num off
    qemu_instance_per_mdl['serial2'].sendline('more ' + cpu_path + 'offline')
    assert(qemu_instance_per_mdl['serial2'].expect(str(core_num)) == 0)

    qemu_instance_per_mdl['serial2'].sendline('echo 1 > ' + cpu_path + 'cpu' + str(core_num) + '/online') #turn CPU core_num on
    qemu_instance_per_mdl['serial2'].sendline('more ' + cpu_path + 'online')
    assert(qemu_instance_per_mdl['serial2'].expect('0-7') == 0)
