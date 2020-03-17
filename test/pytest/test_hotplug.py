import serial
import pytest
from pexpect.fdpexpect import fdspawn

@pytest.mark.timeout(400)
@pytest.mark.parametrize('core_num', range(1,8))
def test_hotplug(hpps_serial, core_num):
    hpps_serial.sendline('root')
    cpu_path = '/sys/devices/system/cpu/'

    hpps_serial.sendline('echo 0 > ' + cpu_path + 'cpu' + str(core_num) + '/online') #turn CPU core_num off
    hpps_serial.sendline('more ' + cpu_path + 'offline')
    assert(hpps_serial.expect(str(core_num)) == 0)

    hpps_serial.sendline('echo 1 > ' + cpu_path + 'cpu' + str(core_num) + '/online') #turn CPU core_num on
    hpps_serial.sendline('more ' + cpu_path + 'online')
    assert(hpps_serial.expect('0-7') == 0)
