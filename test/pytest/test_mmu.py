import serial
import pytest
from pexpect.fdpexpect import fdspawn

@pytest.mark.timeout(400)
def test_trch_mmu(qemu_instance_per_fcn):
    assert(qemu_instance_per_fcn['serial0'].expect('TEST: rt mmu: map-write-read: success') == 0)
    assert(qemu_instance_per_fcn['serial0'].expect('TEST: rt mmu: write-map-read: success') == 0)
    assert(qemu_instance_per_fcn['serial0'].expect('TEST: rt mmu: mapping swap: success') == 0)
