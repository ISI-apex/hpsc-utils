import subprocess
import pytest

testers = ["mboxtester", "mbox-multiple-core-tester"]

def run_tester_on_host(hostname, tester_num, tester_pre_args, tester_post_args):
    tester_remote_path = "/opt/hpsc-utils/" + testers[tester_num]
    out = subprocess.run(['ssh', hostname] + tester_pre_args + [tester_remote_path] + tester_post_args, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return out
    
# Verify that mboxtester works with the process pinned separately to each HPPS core.
# Since this first test will boot QEMU, it is given more than the default time
@pytest.mark.timeout(200)
@pytest.mark.parametrize('core_num', range(8))
@pytest.mark.parametrize('notif', ['none', 'select', 'poll', 'epoll'])
def test_hpps_to_trch_for_each_notification_and_core(qemu_instance_per_mdl, host, core_num, notif):
    out = run_tester_on_host(host, 0, [], ['-n', notif, '-c', str(core_num)])
    assert out.returncode == 0, eval(pytest.run_fail_str)

@pytest.mark.parametrize('core_num', range(8))
@pytest.mark.parametrize('notif', ['none', 'select', 'poll', 'epoll'])
def test_hpps_to_rtps_for_each_notification_and_core(qemu_instance_per_mdl, host, core_num, notif):
    out = run_tester_on_host(host, 0, [], ['-n', notif, '-o', '/dev/mbox/1/mbox0', '-i', '/dev/mbox/1/mbox1', '-c', str(core_num)])
    assert out.returncode == 0, eval(pytest.run_fail_str)

@pytest.mark.parametrize('core_num', range(8))
def test_invalid_outbound_mailbox_for_each_core(qemu_instance_per_mdl, host, core_num):
    out = run_tester_on_host(host, 0, [], ['-c', str(core_num), '-o', '32'])
    assert out.returncode == 1, eval(pytest.run_fail_str)

@pytest.mark.parametrize('core_num', range(8))
def test_invalid_inbound_mailbox_for_each_core(qemu_instance_per_mdl, host, core_num):
    out = run_tester_on_host(host, 0, [], ['-c', str(core_num), '-i', '32'])
    assert out.returncode == 1, eval(pytest.run_fail_str)

# Verify that mboxtester fails with the correct exit code when a timeout
# occurs with the process pinned separately to each HPPS core
@pytest.mark.parametrize('core_num', range(8))
def test_early_timeout_for_each_core(qemu_instance_per_mdl, host, core_num):
    out = run_tester_on_host(host, 0, [], ['-c', str(core_num), '-t', '0'])
    assert out.returncode == 22, eval(pytest.run_fail_str)

# verify that mbox-multiple-core-tester works with core 0 performing a
# write-read followed by core 1 doing another write-read using the same mailbox
def test_multiple_cores_same_mbox(qemu_instance_per_mdl, host):
    out = run_tester_on_host(host, 1, [], ['-C', '0', '-c', '1'])
    assert out.returncode == 0, eval(pytest.run_fail_str)

def test_multiple_cores_same_mbox_invalid_CPU1(qemu_instance_per_mdl, host):
    out = run_tester_on_host(host, 1, [], ['-C', '-1', '-c', '1'])
    assert out.returncode == 1, eval(pytest.run_fail_str)

def test_multiple_cores_same_mbox_invalid_CPU2(qemu_instance_per_mdl, host):
    out = run_tester_on_host(host, 1, [], ['-C', '0', '-c', '9'])
    assert out.returncode == 2, eval(pytest.run_fail_str)
