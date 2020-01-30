import subprocess
import pytest

testers = ["interrupt-affinity-tester.sh"]

def run_tester_on_host(hostname, tester_num, tester_pre_args, tester_post_args):
    tester_remote_path = "/opt/hpsc-utils/" + testers[tester_num]
    out = subprocess.run(['ssh', hostname] + tester_pre_args + [tester_remote_path] + tester_post_args, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return out

# Since this first test will boot QEMU, it is given more than the default time
@pytest.mark.timeout(200)
@pytest.mark.parametrize('core_num', range(8))
def test_interrupt_affinity_on_each_core(qemu_instance_per_mdl, host, core_num):
    out = run_tester_on_host(host, 0, [], ['-c', str(core_num)])
    assert out.returncode == 0, eval(pytest.run_fail_str)
