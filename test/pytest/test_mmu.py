import serial
import pytest
from pexpect.fdpexpect import fdspawn

@pytest.mark.timeout(400)
def test_trch_mmu(qemu_instance_per_fcn):
    assert(qemu_instance_per_fcn['serial0'].expect('MMU map-write-read test success') == 0)
    assert(qemu_instance_per_fcn['serial0'].expect('MMU write-map-read test success') == 0)
    assert(qemu_instance_per_fcn['serial0'].expect('MMU mapping swap test success') == 0)
