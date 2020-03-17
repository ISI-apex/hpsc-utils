import serial
import pytest
from pexpect.fdpexpect import fdspawn

@pytest.mark.timeout(400)
def test_rt_mmu(trch_serial_per_fnc):
    assert(trch_serial_per_fnc.expect('TEST: rt mmu: map-write-read: success') == 0)
    assert(trch_serial_per_fnc.expect('TEST: rt mmu: write-map-read: success') == 0)
    assert(trch_serial_per_fnc.expect('TEST: rt mmu: mapping swap: success') == 0)
