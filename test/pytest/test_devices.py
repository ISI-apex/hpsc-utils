import pytest
import subprocess
import re
import time

# On timeouts: boot from a fresh NAND takes ~5mins (due to udev initializing
# the HW database), so timeouts need to be around 400s. Subsequent boots are
# much faster, but we want any test to be runnable from fresh NAND
# individually.
#
# TODO: instead of relying on the pytest-timeout annotation marks, add timeouts
# to individual pexect calls, it's more verbose, but it fixes the issue of
# stuck fixture threads when tests fail (under certain circumstances).
# pytest-timeout calls pytest.fail() from a handler, and the fixture cleanup
# does run, but that cleanup is not capable of getting our pexpect threads out
# of whatever # wait (pexpect call) they might be in. An alternative is
# to make the threads non-blocking, so that the fixture can clean them up
# at any point -- ok too. Adding timeouts in the tests might be simpler.

HPPS_LINUX_BOOT_TIME_S = 400

# First connection over ssh takes a long time
HPPS_LINUX_SSH_TIME_S = 100

# NOTE: between these steps there's a ~5 minute delay where Qemu has 0% CPU and
# 0% disk utilization (measure on fresh NAND image!); host disk utilization is
# not saying much because all data is probably in DRAM page caches at this point.
# This delay seems to be caused by systemd-journald (same for both boots from NAND
# and preloaded boots from initramfs image in DRAM):
#   [  510.835845] systemd-journald[92]: Received SIGTERM from PID 1 (systemd-shutdow).
#   [  732.560813] systemd-shutdown[1]: Sending SIGKILL to remaining processes...
HPPS_LINUX_SHUTDOWN_TIME_S = 400


class SSHTester:
    testers = [] # derived classes override

    def run_cmd_on_host(self, hostname, cmd):
        out = subprocess.run("ssh " + hostname + " " + cmd,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                universal_newlines=False, shell=True)
        assert out.returncode == 0, eval(pytest.run_fail_str)
        return out, out.stdout.decode('ascii')

    # legacy, superceded by run_cmd_on_host
    def run_tester_on_host(self, hostname, tester_num, tester_pre_args,
            tester_post_args):
        tester_remote_path = "/opt/hpsc-utils/" + self.testers[tester_num]
        out = subprocess.run(['ssh', hostname] + tester_pre_args +
                [tester_remote_path] + tester_post_args,
                universal_newlines=False, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        return out, out.stdout.decode('ascii')

# Track step by step, so that if it fails, we quickly get info about where
hpps_linux_boot_steps = [
    r'NOTICE:  ATF running on HPSC',
    r'U-Boot.*HPSC HPPS',
    r'Booting Linux on physical CPU 0x0',

    # TODO: add more key device init messages from kernel log to here
    r'hpsc_msg_lifecycle: 0:',
    r'hpsc_msg_tp_shmem hpsc_msg_tp_shmem@trch: send',

    # TODO: look for failure to init mailbox (observed after WDT reboot
    # (unclean shutdown only?)). Does this need fix in TRCH logic (clear the
    # links on reboot of subsystem?):
    #   hpsc_mbox fff50000.mailbox: src/dest mismatch: 1/1 (expected 80/2d)
    #   hpsc_msg_tp_mbox hpsc_msg_tp_mbox@trch: Unable to startup the chan (-16)
    #   hpsc_msg_tp_mbox hpsc_msg_tp_mbox@trch: Channel request failed: 0
    #   hpsc_msg_tp_mbox: probe of hpsc_msg_tp_mbox@trch failed with error -16

    r"hpsc-chiplet login: ",
]
hpps_linux_shutdown_steps = [
    # careful about the colors/boldface when matching
    r'Reached target .*Power-Off',
    r'systemd-shutdown\[1\]: Syncing filesystems and block devices\.',

    # NOTE: Sometimes fs sync times out, but it is unclear if this can lead
    # to NAND JFFS2 corruption -- it shouldn't since the unmount follows
    # (SYNC_TIMEOUT_USEC hardcoded to 3*10s in systemd, fwiw):
    # systemd-shutdown[1]: Syncing filesystems and block devices - timed
    # out, issuing SIGKILL to PID \d+\.

    r'systemd-shutdown\[1\]: All filesystems unmounted.',
    r'hpsc_msg_lifecycle: 1: 3',
    r'hpsc_msg_tp_shmem hpsc_msg_tp_shmem@trch: send',
    r'reboot: Power down',
]

def expect_hpps_linux_boot(conn):
    for step in hpps_linux_boot_steps:
        idx = conn.expect(step)
        assert idx == 0, "expect failed for: " + step

def expect_hpps_linux_shutdown(conn):
    for step in hpps_linux_shutdown_steps:
        idx = conn.expect([step, hpps_linux_boot_steps[0]])
        assert idx == 0, "clean shutdown did not happen: missed step: " + step

def hpps_linux_login(conn):
    conn.sendline('root')
    assert(conn.expect('root@hpsc-chiplet:~# ') == 0)

def hpps_linux_reboot(conn):
    # TODO: add test like this one but where whole machine (Qemu) is restarted
    # currently HPPS Linux does not activate the watchdog by default, so
    # we need to activate it before issuing the 'shutdown' command.
    conn.sendline("taskset -c 0 /opt/hpsc-utils/wdtester " + \
            "/dev/watchdog0 0 0") # 0=do not kick, 0=open then run for zero seconds

    conn.sendline("shutdown -h now")
    expect_hpps_linux_boot(conn)
    hpps_linux_login(conn)


class TestDMA(SSHTester):
    testers = ["dma-tester.sh"]

    @pytest.mark.timeout(HPPS_LINUX_BOOT_TIME_S + HPPS_LINUX_SSH_TIME_S)
    @pytest.mark.parametrize('buf_size', [8192, 16384, -1])
    def test_test_buffer_size(self, qemu_instance_per_mdl, host, buf_size):
        out, output = self.run_tester_on_host(host, 0, [], ['-b', str(buf_size)])
        if buf_size > 0:
            assert out.returncode == 0, eval(pytest.run_fail_str)
        else:
            assert out.returncode == 1, eval(pytest.run_fail_str)

    @pytest.mark.parametrize('threads_per_chan', [1, 2, 4, -1])
    def test_threads_per_channel(self, qemu_instance_per_mdl, host,
            threads_per_chan):
        out, output = self.run_tester_on_host(host, 0, [], ['-T',
            str(threads_per_chan)])
        if threads_per_chan > 0:
            assert out.returncode == 0, eval(pytest.run_fail_str)
        else:
            assert out.returncode == 2, eval(pytest.run_fail_str)

    @pytest.mark.parametrize('iterations', [1, 2, -1])
    def test_iterations(self, qemu_instance_per_mdl, host, iterations):
        out, output = self.run_tester_on_host(host, 0, [], ['-i', str(iterations)])
        if iterations > 0:
            assert out.returncode == 0, eval(pytest.run_fail_str)
        else:
            assert out.returncode == 3, eval(pytest.run_fail_str)

    @pytest.mark.parametrize('timeouts', [1500, 3000, -1])
    def test_timeouts(self, qemu_instance_per_mdl, host, timeouts):
        out, output = self.run_tester_on_host(host, 0, [], ['-t', str(timeouts)])
        if timeouts > 0:
            assert out.returncode == 0, eval(pytest.run_fail_str)
        else:
            assert out.returncode == 4, eval(pytest.run_fail_str)

    @pytest.mark.parametrize('chan', ["nochan"])
    def test_dma_channels(self, qemu_instance_per_mdl, host, chan):
        out, output = self.run_tester_on_host(host, 0, [], ['-c', chan])
        if chan == "nochan":
            assert out.returncode == 5, eval(pytest.run_fail_str)

class TestCPUHotplug:
    @pytest.mark.timeout(HPPS_LINUX_BOOT_TIME_S)
    @pytest.mark.parametrize('core_num', range(1,8))
    def test_hotplug(self, hpps_serial, core_num):
        hpps_serial.sendline('root')
        cpu_path = '/sys/devices/system/cpu/'

        hpps_serial.sendline('echo 0 > ' + cpu_path + 'cpu' + str(core_num) +
                '/online') #turn CPU core_num off
        hpps_serial.sendline('more ' + cpu_path + 'offline')
        assert(hpps_serial.expect(str(core_num)) == 0)

        hpps_serial.sendline('echo 1 > ' + cpu_path + 'cpu' + str(core_num) +
                '/online') #turn CPU core_num on
        hpps_serial.sendline('more ' + cpu_path + 'online')
        assert(hpps_serial.expect('0-7') == 0)

class TestIntAffinity(SSHTester):
    testers = ["interrupt-affinity-tester.sh"]

    @pytest.mark.timeout(HPPS_LINUX_BOOT_TIME_S + HPPS_LINUX_SSH_TIME_S)
    @pytest.mark.parametrize('core_num', range(8))
    def test_interrupt_affinity_on_each_core(self, qemu_instance_per_mdl, host,
            core_num):
        out, output = self.run_tester_on_host(host, 0, [], ['-c', str(core_num)])
        assert out.returncode == 0, eval(pytest.run_fail_str)

class TestMailboxMultiSystem(SSHTester):
    testers = ['mbox-server-tester']

    @pytest.mark.timeout(HPPS_LINUX_BOOT_TIME_S + HPPS_LINUX_SSH_TIME_S)
    @pytest.mark.parametrize('core_num', range(8))
    def test_rtps_hpps(self, rtps_serial, host, core_num):
        rtps_serial.sendline('test_mbox_rtps_hpps 3 4')
        assert(rtps_serial.expect('TEST: test_mbox_rtps_hpps: begin') == 0)

        out, output = self.run_tester_on_host(host, 0, [], ['-c', str(core_num)])

        assert(rtps_serial.expect('TEST: test_mbox_rtps_hpps: success') == 0)

        # hpps returns number of bytes sent. we expect 64 bytes
        assert out.returncode == 64

class TestMailbox(SSHTester):
    testers = ["mboxtester", "mbox-multiple-core-tester"]

    # Verify that mboxtester works with the process pinned separately to each
    # HPPS core.
    @pytest.mark.timeout(HPPS_LINUX_BOOT_TIME_S + HPPS_LINUX_SSH_TIME_S)
    @pytest.mark.parametrize('core_num', range(8))
    @pytest.mark.parametrize('notif', ['none', 'select', 'poll', 'epoll'])
    def test_hpps_to_trch_for_each_notification_and_core(self,
            qemu_instance_per_mdl, host, core_num, notif):
        out, output = self.run_tester_on_host(host, 0, [], ['-n', notif, '-c',
            str(core_num)])
        assert out.returncode == 0, eval(pytest.run_fail_str)

    @pytest.mark.parametrize('core_num', range(8))
    @pytest.mark.parametrize('notif', ['none', 'select', 'poll', 'epoll'])
    def test_hpps_to_rtps_for_each_notification_and_core(self,
            qemu_instance_per_mdl, host, core_num, notif):
        out, output = self.run_tester_on_host(host, 0, [], ['-n', notif, '-o',
            '/dev/mbox/1/mbox0', '-i', '/dev/mbox/1/mbox1', '-c',
            str(core_num)])
        assert out.returncode == 0, eval(pytest.run_fail_str)

    @pytest.mark.parametrize('core_num', range(8))
    def test_invalid_outbound_mailbox_for_each_core(self,
            qemu_instance_per_mdl, host, core_num):
        out, output = self.run_tester_on_host(host, 0, [], ['-c', str(core_num), '-o',
            '32'])
        assert out.returncode == 1, eval(pytest.run_fail_str)

    @pytest.mark.parametrize('core_num', range(8))
    def test_invalid_inbound_mailbox_for_each_core(self, qemu_instance_per_mdl,
            host, core_num):
        out, output = self.run_tester_on_host(host, 0, [], ['-c', str(core_num),
            '-i', '32'])
        assert out.returncode == 1, eval(pytest.run_fail_str)

    # Verify that mboxtester fails with the correct exit code when a timeout
    # occurs with the process pinned separately to each HPPS core
    @pytest.mark.timeout(200)
    @pytest.mark.parametrize('core_num', range(8))
    def test_early_timeout_for_each_core(self, qemu_instance_per_mdl, host,
            core_num):
        out, output = self.run_tester_on_host(host, 0, [], ['-c', str(core_num), '-t',
            '0'])
        assert out.returncode == 22, eval(pytest.run_fail_str)

    # verify that mbox-multiple-core-tester works with core 0 performing a
    # write-read followed by core 1 doing another write-read using the same
    # mailbox
    def test_multiple_cores_same_mbox(self, qemu_instance_per_mdl, host):
        out, output = self.run_tester_on_host(host, 1, [], ['-C', '0', '-c', '1'])
        assert out.returncode == 0, eval(pytest.run_fail_str)

    def test_multiple_cores_same_mbox_invalid_CPU1(self, qemu_instance_per_mdl,
            host):
        out, output = self.run_tester_on_host(host, 1, [], ['-C', '-1', '-c', '1'])
        assert out.returncode == 1, eval(pytest.run_fail_str)

    def test_multiple_cores_same_mbox_invalid_CPU2(self, qemu_instance_per_mdl,
            host):
        out, output = self.run_tester_on_host(host, 1, [], ['-C', '0', '-c', '9'])
        assert out.returncode == 2, eval(pytest.run_fail_str)

class TestSharedMem(SSHTester):
    testers = ["shm-standalone-tester", "shm-tester"]

    @pytest.mark.timeout(HPPS_LINUX_BOOT_TIME_S + HPPS_LINUX_SSH_TIME_S)
    def test_write_then_read_on_each_shm_region(self, qemu_instance_per_mdl,
            host):
        shm_dir = '/dev/hpsc_shmem/'
        num_write_bytes = 32

        # get a list of shared memory regions
        out, output = self.run_cmd_on_host(host, "ls " + shm_dir)
        shm_regions = output.splitlines()

        for shm_region in shm_regions:
            # write 0xff to each of num_write_bytes consecutive bytes of each shm_region
            out, output = self.run_tester_on_host(host, 0, [], ['-f', shm_dir +
                shm_region, '-s', str(num_write_bytes), '-w', '0xff'])
            assert out.returncode == 0, eval(pytest.run_fail_str)
            # now perform a read to confirm the write
            out, output = self.run_tester_on_host(host, 0, [], ['-f', shm_dir +
                shm_region, '-s', str(num_write_bytes), '-r'])
            read_contents = (re.search(r"Start:(.+)$", output).group(0))[6:]
            assert out.returncode == 0, eval(pytest.run_fail_str)
            assert read_contents == ' 0xff' * num_write_bytes

    def test_hpps_to_trch(self, qemu_instance_per_mdl, host):
        out, output = self.run_tester_on_host(host, 1, [], ['-i',
            '/dev/hpsc_shmem/region0', '-o', '/dev/hpsc_shmem/region1'])
        assert out.returncode == 0, eval(pytest.run_fail_str)

class TestRTITimer(SSHTester):
    testers = ["rtit-tester"]

    @pytest.mark.timeout(HPPS_LINUX_BOOT_TIME_S + HPPS_LINUX_SSH_TIME_S)
    @pytest.mark.parametrize('core_num', range(8))
    def test_rti_timer_on_each_core(self, qemu_instance_per_mdl, host, core_num):
        out, output = self.run_tester_on_host(host, 0, ['taskset', '-c',
            str(core_num)], ["/dev/rti_timer" + str(core_num), str(2000)])
        assert out.returncode == 0, eval(pytest.run_fail_str)

class TestWDTimer:
    # both stages, set in hpsc-baremetal/trch/watchdog.c
    WD_TIMEOUT_SEC = 5 + 400

    # Each core starts its own watchdog timer and then kicks it.
    @pytest.mark.timeout(2 * HPPS_LINUX_BOOT_TIME_S + WD_TIMEOUT_SEC)
    @pytest.mark.parametrize('core_num', range(8))
    def test_kicked_watchdog_on_each_core(self, hpps_serial, core_num):

        do_kick = 1
        time_to_run = self.WD_TIMEOUT_SEC * 1.10 # +10% margin
        hpps_serial.sendline("taskset -c " + str(core_num) + " " +
                "/opt/hpsc-utils/wdtester /dev/watchdog" + str(core_num) +
                " " + str(do_kick) +  " " + str(time_to_run))

        idx = hpps_serial.expect(["Kicking watchdog: yes",
                                    hpps_linux_boot_steps[0]])
        assert idx == 0, "unexpected reboot of HPPS"

        # Wait for indication from wdtester that the time interval has elapsed
        idx = hpps_serial.expect(["Stopping", hpps_linux_boot_steps[0]])
        assert idx == 0, "unexpected reboot of HPPS"

        # The test is successful at this point, but we need to reboot
        # Linux, because WD cannot be deactivated (and we don't want
        # to keep kicking it, because it pollutes the state for the other
        # tests, including the instances of this test for the other cores).
        hpps_linux_reboot(hpps_serial)

    # Each core starts its own watchdog timer but does not kick it.
    #
    # NOTE: To test the hard shutdown (no reaction from kernel), make a similar
    # test without the check for clean shutdown message, and run it on a
    # profile without CONFIG_WATCHDOG_PRETIMEOUT_DEFAULT_GOV_NOTIFIER. Note that
    # this will almost certainly corrupt NAND JFFS2 filesystem (observed).
    @pytest.mark.timeout(2 * HPPS_LINUX_BOOT_TIME_S + HPPS_LINUX_SHUTDOWN_TIME_S)
    @pytest.mark.parametrize('core_num', range(8))
    def test_unkicked_watchdog_on_each_core(self, hpps_serial, core_num):
        do_kick = 0
        time_to_run = 0 # seconds
        hpps_serial.sendline("taskset -c " + str(core_num) + " " +
            "/opt/hpsc-utils/wdtester /dev/watchdog" + str(core_num) +
            " " + str(do_kick) +  " " + str(time_to_run))

        hpps_serial.expect('HPSC WDT: stage 1 interrupt received ' + \
                'for cpu ' + str(core_num) + ' on cpu ' + str(core_num))
        hpps_serial.expect('hpsc_monitor_wdt: initiating poweroff')

        expect_hpps_linux_shutdown(hpps_serial)
        expect_hpps_linux_boot(hpps_serial)
        hpps_linux_login(hpps_serial)

class TestSRAM(SSHTester):
    testers = ["sram-tester"]

    # This SRAM test will modify an array in SRAM, reboot HPPS (using a
    # watchdog timeout), then check that the SRAM array is the same.
    @pytest.mark.timeout(2 * HPPS_LINUX_BOOT_TIME_S + HPPS_LINUX_SSH_TIME_S + \
            HPPS_LINUX_SHUTDOWN_TIME_S)
    def test_non_volatility(self, hpps_serial, host):
        # increment the first 100 elements of the SRAM array by 2
        out, output = self.run_tester_on_host(host, 0, [], ["-s", "100", "-i", "2"])
        assert out.returncode == 0, eval(pytest.run_fail_str)
        sram_before_reboot = re.search(r'Latest SRAM contents:(.+)',
                output, flags=re.DOTALL).group(1)

        hpps_linux_reboot(hpps_serial)

        # after the reboot, read the SRAM contents to verify that they haven't
        # changed
        out, output = self.run_tester_on_host(host, 0, [], ["-s", "100"])
        assert out.returncode == 0, eval(pytest.run_fail_str)
        sram_after_reboot = re.search(r'Latest SRAM contents:(.+)', output,
                flags=re.DOTALL).group(1)
        assert(sram_before_reboot == sram_after_reboot), \
            "SRAM array before reboot was: " + sram_before_reboot + \
            ", while SRAM array after reboot was: " + sram_after_reboot

        # return the SRAM contents to their original state
        out, output = self.run_tester_on_host(host, 0, [], ["-s", "100", "-i", "-2"])
        assert out.returncode == 0, eval(pytest.run_fail_str)

class TestNAND(SSHTester):
    @pytest.mark.timeout(2 * HPPS_LINUX_BOOT_TIME_S + HPPS_LINUX_SSH_TIME_S + \
            HPPS_LINUX_SHUTDOWN_TIME_S)
    def test_non_volatility(self, hpps_serial, host):
        """Verify that a file created on the NAND-based rootfs is still present
        after rebooting HPPS."""
        test_dir = "/home/root/"
        test_file = "nand_test_file"

        # create the test_file
        out, output = self.run_cmd_on_host(host, "touch " + test_dir + test_file)

        hpps_linux_reboot(hpps_serial)

        # after the reboot, check that the test_file is still there
        out, output = self.run_cmd_on_host(host, "ls " + test_dir)
        assert(test_file in output), "File " + test_file + \
            " was not found among the following files listed in directory " + \
            test_dir + ":\n" + output

        # finally, remove the test_file
        out, output = self.run_cmd_on_host(host, "rm " + test_dir + test_file)

class TestParallelScaling(SSHTester):
    nas_ep_class = "S"
    tester_remote_path = "/opt/nas-parallel-benchmarks/NPB3.3.1-OMP/bin/ep." + \
        nas_ep_class + ".x"

    @pytest.mark.timeout(HPPS_LINUX_BOOT_TIME_S + HPPS_LINUX_SSH_TIME_S)
    def test_verify_HPPS_core_count(self, qemu_instance_per_mdl, host):
        """Check the entries in /proc/cpuinfo to confirm that the HPPS has 8 cores"""
        hpps_core_count = 8
        out, output = self.run_cmd_on_host(host, "cat /proc/cpuinfo")
        proc_nums = re.findall(r"processor\s+\S+\s+(\S+)", output)
        assert(len(proc_nums) == hpps_core_count), \
                "The list of processor numbers in /proc/cpuinfo is " + \
                str(proc_nums)

        for i in range(hpps_core_count):
            assert(str(i) in proc_nums), "Processor " + str(i) + \
                    " is missing from the processor list: " + str(proc_nums) + \
                    " from /proc/cpuinfo"

    def test_OMP_speedup(self, qemu_instance_per_mdl, host):
        """Verify that OMP scaling the NAS EP benchmark on the HPPS cores leads
        to speedup.

        NOTE: This test often fails on AWS CodeBuild using 8 vCPUs when scaling
        from 4 to 8 OMP threads.  This is because the vCPUs are overloaded-
        running on 72 vCPUs solves the problem.
        """
        executed_thread_counts = []
        executed_cpu_times = []
        for num_threads in [1,2,4,8]:
            # first set OMP_NUM_THREADS and OMP_PROC_BIND, then run the tester
            out, output = self.run_cmd_on_host(host, "\"export OMP_NUM_THREADS=" + \
                    str(num_threads) +"; export OMP_PROC_BIND=TRUE; " + \
                    self.tester_remote_path + "\"")

            cpu_time = float(re.search(r"(\S+)$", \
                    re.search(r"CPU Time =(\s+)(\S+)", output).group(0))
                    .group(0))
            executed_thread_counts.append(num_threads)
            executed_cpu_times.append(cpu_time)

            returncode = 0
            if (num_threads > 1):
                if (cpu_time >= prior_cpu_time):
                    if (num_threads == 2):
                        returncode = 1
                    elif (num_threads == 4):
                        returncode = 2
                    elif (num_threads == 8):
                        returncode = 3
            assert returncode == 0, "NAS EP class " + self.nas_ep_class + \
                    " run times for " + str(executed_thread_counts) + \
                    " OMP threads are " + str(executed_cpu_times) + \
                    " seconds respectively."
            prior_cpu_time = cpu_time

        # This print statement will only display if pytest is passed the "-s" flag
        print("\nNAS EP class " + self.nas_ep_class + " run times for " +
                str(executed_thread_counts) + " OMP threads are " +
                str(executed_cpu_times) + " seconds respectively.")
