import serial
import pytest
from pexpect.fdpexpect import fdspawn

@pytest.mark.timeout(400)

def test_hotplug(qemu_instance_per_fcn):
    qemu_instance_per_fcn['serial2'].sendline('root')
    cpu_path = '/sys/devices/system/cpu/'

    for i in range(1,8):
        qemu_instance_per_fcn['serial2'].sendline('echo 0 > ' + cpu_path + 'cpu' + str(i) + '/online') #turn CPU i off
        qemu_instance_per_fcn['serial2'].sendline('more ' + cpu_path + 'offline')
        assert(qemu_instance_per_fcn['serial2'].expect(str(i)) == 0)

        qemu_instance_per_fcn['serial2'].sendline('echo 1 > ' + cpu_path + 'cpu' + str(i) + '/online') #turn CPU i on
        qemu_instance_per_fcn['serial2'].sendline('more ' + cpu_path + 'online')
        assert(qemu_instance_per_fcn['serial2'].expect('0-7') == 0)
