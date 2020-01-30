import subprocess
import pytest
import re
import time

# This test measures the load on the system after running the NAS EP benchmark
# with a specified number of OpenMP threads for a specified number of seconds.
# If "num_threads" is assigned a value of "0", then the EP benchmark won't be
# run.  As a result, only the load resulting from running QEMU will be measured.
#
# Note that this test should not be called by default since the filename does not
# begin with the word "test".  If the test is called explicitly, make sure to
# pass the "-s" flag to view the stdout generated during the test, e.g:
#
# pytest -sv --host hpscqemu --durations=0 measure_load.py

# Finally, make sure that the CODEBUILD_SRC_DIR env var is set.  This is the
# directory where the hpsc-bsp directory is located.  On AWS CodeBuild, this is
# done automatically.  In any other environment, it needs to be set.

nas_ep_class = "B"
tester_remote_path = "/opt/nas-parallel-benchmarks/NPB3.3.1-OMP/bin/ep." + nas_ep_class + ".x"

@pytest.mark.timeout(200)
@pytest.mark.parametrize('sleep_sec', [70])
# "0" threads in the num_threads array means that the NAS benchmark won't be run
@pytest.mark.parametrize('num_threads', range(9))
def test_load_with_varying_thread_counts_and_sleep_times(qemu_instance_per_mdl, host, sleep_sec, num_threads):
    if (num_threads > 0):
        # first set OMP_NUM_THREADS and OMP_PROC_BIND, then run the tester asynchronously
        p = subprocess.Popen("ssh " + host + " \"export OMP_NUM_THREADS=" + str(num_threads) +"; export OMP_PROC_BIND=TRUE; " + tester_remote_path + "\"", stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, shell=True)
        time.sleep(1)

        # identify the process ID of the running NAS benchmark
        out = subprocess.run("ssh " + host + " ps ", stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, shell=True)
        pid = re.search(r"\s+(\S+)\s+\S+\s+\S+\s+\S+\s+" + tester_remote_path, out.stdout).group(1)

    # sleep for the prescribed number of seconds, then print out the "uptime" output
    out = subprocess.run("ssh " + host + " \"sleep " + str(sleep_sec) + "; uptime\"", stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, shell=True)
    print("\nFor " + str(num_threads) + " threads sleeping for " + str(sleep_sec) + " seconds:\n", out.stdout)

    if (num_threads > 0):
        # kill the current process before increasing the OMP thread count
        out = subprocess.run("ssh " + host + " kill -9 " + pid, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, shell=True)
        p.terminate()
