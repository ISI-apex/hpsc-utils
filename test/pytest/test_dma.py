import subprocess
import pytest

testers = ["dma-tester.sh"]

def run_tester_on_host(hostname, tester_num, tester_pre_args, tester_post_args):
    tester_remote_path = "/opt/hpsc-utils/" + testers[tester_num]
    out = subprocess.run(['ssh', hostname] + tester_pre_args + [tester_remote_path] + tester_post_args, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return out

# Since this first test will boot QEMU, it is given more than the default time
@pytest.mark.timeout(200)
@pytest.mark.parametrize('buf_size', [8192, 16384, -1])
def test_test_buffer_size(qemu_instance_per_mdl, host, buf_size):
    out = run_tester_on_host(host, 0, [], ['-b', str(buf_size)])
    if buf_size > 0:
        assert out.returncode == 0, eval(pytest.run_fail_str)
    else:
        assert out.returncode == 1, eval(pytest.run_fail_str)

@pytest.mark.parametrize('threads_per_chan', [1, 2, 4, -1])
def test_threads_per_channel(qemu_instance_per_mdl, host, threads_per_chan):
    out = run_tester_on_host(host, 0, [], ['-T', str(threads_per_chan)])
    if threads_per_chan > 0:
        assert out.returncode == 0, eval(pytest.run_fail_str)
    else:
        assert out.returncode == 2, eval(pytest.run_fail_str)

@pytest.mark.parametrize('iterations', [1, 2, -1])
def test_iterations(qemu_instance_per_mdl, host, iterations):
    out = run_tester_on_host(host, 0, [], ['-i', str(iterations)])
    if iterations > 0:
        assert out.returncode == 0, eval(pytest.run_fail_str)
    else:
        assert out.returncode == 3, eval(pytest.run_fail_str)

@pytest.mark.parametrize('timeouts', [1500, 3000, -1])
def test_timeouts(qemu_instance_per_mdl, host, timeouts):
    out = run_tester_on_host(host, 0, [], ['-t', str(timeouts)])
    if timeouts > 0:
        assert out.returncode == 0, eval(pytest.run_fail_str)
    else:
        assert out.returncode == 4, eval(pytest.run_fail_str)

@pytest.mark.parametrize('chan', ["nochan"])
def test_dma_channels(qemu_instance_per_mdl, host, chan):
    out = run_tester_on_host(host, 0, [], ['-c', chan])
    if chan == "nochan":
        assert out.returncode == 5, eval(pytest.run_fail_str)
