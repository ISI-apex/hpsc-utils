import pytest
import subprocess
import serial
import re

class SSHTester:
    testers = [] # derived classes override

    def run_tester_on_host(self, hostname, tester_num, tester_pre_args,
            tester_post_args):
        tester_remote_path = "/opt/hpsc-utils/" + self.testers[tester_num]
        out = subprocess.run(['ssh', hostname] + tester_pre_args +
                [tester_remote_path] + tester_post_args,
                universal_newlines=True, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        return out


class TestDMA(SSHTester):
    testers = ["dma-tester.sh"]

    @pytest.mark.timeout(400)
    @pytest.mark.parametrize('buf_size', [8192, 16384, -1])
    def test_test_buffer_size(self, qemu_instance_per_mdl, host, buf_size):
        out = self.run_tester_on_host(host, 0, [], ['-b', str(buf_size)])
        if buf_size > 0:
            assert out.returncode == 0, eval(pytest.run_fail_str)
        else:
            assert out.returncode == 1, eval(pytest.run_fail_str)

    @pytest.mark.parametrize('threads_per_chan', [1, 2, 4, -1])
    def test_threads_per_channel(self, qemu_instance_per_mdl, host,
            threads_per_chan):
        out = self.run_tester_on_host(host, 0, [], ['-T',
            str(threads_per_chan)])
        if threads_per_chan > 0:
            assert out.returncode == 0, eval(pytest.run_fail_str)
        else:
            assert out.returncode == 2, eval(pytest.run_fail_str)

    @pytest.mark.parametrize('iterations', [1, 2, -1])
    def test_iterations(self, qemu_instance_per_mdl, host, iterations):
        out = self.run_tester_on_host(host, 0, [], ['-i', str(iterations)])
        if iterations > 0:
            assert out.returncode == 0, eval(pytest.run_fail_str)
        else:
            assert out.returncode == 3, eval(pytest.run_fail_str)

    @pytest.mark.parametrize('timeouts', [1500, 3000, -1])
    def test_timeouts(self, qemu_instance_per_mdl, host, timeouts):
        out = self.run_tester_on_host(host, 0, [], ['-t', str(timeouts)])
        if timeouts > 0:
            assert out.returncode == 0, eval(pytest.run_fail_str)
        else:
            assert out.returncode == 4, eval(pytest.run_fail_str)

    @pytest.mark.parametrize('chan', ["nochan"])
    def test_dma_channels(self, qemu_instance_per_mdl, host, chan):
        out = self.run_tester_on_host(host, 0, [], ['-c', chan])
        if chan == "nochan":
            assert out.returncode == 5, eval(pytest.run_fail_str)

class TestCPUHotplug(SSHTester):
    @pytest.mark.timeout(400)
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

    @pytest.mark.timeout(400)
    @pytest.mark.parametrize('core_num', range(8))
    def test_interrupt_affinity_on_each_core(self, qemu_instance_per_mdl, host,
            core_num):
        out = self.run_tester_on_host(host, 0, [], ['-c', str(core_num)])
        assert out.returncode == 0, eval(pytest.run_fail_str)

class TestMailboxMultiSystem(SSHTester):
    @pytest.mark.timeout(400)
    @pytest.mark.parametrize('core_num', range(8))
    def test_rtps_hpps(self, rtps_serial, host, core_num):
        tester_remote_path = '/opt/hpsc-utils/mbox-server-tester'

        rtps_serial.sendline('test_mbox_rtps_hpps 3 4')
        assert(rtps_serial.expect('TEST: test_mbox_rtps_hpps: begin') == 0)

        out = subprocess.run(['ssh', host] + [tester_remote_path] + ['-c',
            str(core_num)], universal_newlines=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)

        assert(rtps_serial.expect('TEST: test_mbox_rtps_hpps: success') == 0)

        # hpps returns number of bytes sent. we expect 64 bytes
        assert out.returncode == 64

class TestMailbox(SSHTester):
    testers = ["mboxtester", "mbox-multiple-core-tester"]

    # Verify that mboxtester works with the process pinned separately to each
    # HPPS core.
    @pytest.mark.timeout(400)
    @pytest.mark.parametrize('core_num', range(8))
    @pytest.mark.parametrize('notif', ['none', 'select', 'poll', 'epoll'])
    def test_hpps_to_trch_for_each_notification_and_core(self,
            qemu_instance_per_mdl, host, core_num, notif):
        out = self.run_tester_on_host(host, 0, [], ['-n', notif, '-c',
            str(core_num)])
        assert out.returncode == 0, eval(pytest.run_fail_str)

    @pytest.mark.parametrize('core_num', range(8))
    @pytest.mark.parametrize('notif', ['none', 'select', 'poll', 'epoll'])
    def test_hpps_to_rtps_for_each_notification_and_core(self,
            qemu_instance_per_mdl, host, core_num, notif):
        out = self.run_tester_on_host(host, 0, [], ['-n', notif, '-o',
            '/dev/mbox/1/mbox0', '-i', '/dev/mbox/1/mbox1', '-c',
            str(core_num)])
        assert out.returncode == 0, eval(pytest.run_fail_str)

    @pytest.mark.parametrize('core_num', range(8))
    def test_invalid_outbound_mailbox_for_each_core(self,
            qemu_instance_per_mdl, host, core_num):
        out = self.run_tester_on_host(host, 0, [], ['-c', str(core_num), '-o',
            '32'])
        assert out.returncode == 1, eval(pytest.run_fail_str)

    @pytest.mark.parametrize('core_num', range(8))
    def test_invalid_inbound_mailbox_for_each_core(self, qemu_instance_per_mdl,
            host, core_num):
        out = self.run_tester_on_host(host, 0, [], ['-c', str(core_num), '-i',
            '32'])
        assert out.returncode == 1, eval(pytest.run_fail_str)

    # Verify that mboxtester fails with the correct exit code when a timeout
    # occurs with the process pinned separately to each HPPS core
    @pytest.mark.timeout(200)
    @pytest.mark.parametrize('core_num', range(8))
    def test_early_timeout_for_each_core(self, qemu_instance_per_mdl, host,
            core_num):
        out = self.run_tester_on_host(host, 0, [], ['-c', str(core_num), '-t',
            '0'])
        assert out.returncode == 22, eval(pytest.run_fail_str)

    # verify that mbox-multiple-core-tester works with core 0 performing a
    # write-read followed by core 1 doing another write-read using the same
    # mailbox
    def test_multiple_cores_same_mbox(self, qemu_instance_per_mdl, host):
        out = self.run_tester_on_host(host, 1, [], ['-C', '0', '-c', '1'])
        assert out.returncode == 0, eval(pytest.run_fail_str)

    def test_multiple_cores_same_mbox_invalid_CPU1(self, qemu_instance_per_mdl,
            host):
        out = self.run_tester_on_host(host, 1, [], ['-C', '-1', '-c', '1'])
        assert out.returncode == 1, eval(pytest.run_fail_str)

    def test_multiple_cores_same_mbox_invalid_CPU2(self, qemu_instance_per_mdl,
            host):
        out = self.run_tester_on_host(host, 1, [], ['-C', '0', '-c', '9'])
        assert out.returncode == 2, eval(pytest.run_fail_str)

class TestSharedMem(SSHTester):
    testers = ["shm-standalone-tester", "shm-tester"]

    @pytest.mark.timeout(400)
    def test_write_then_read_on_each_shm_region(self, qemu_instance_per_mdl,
            host):
        shm_dir = '/dev/hpsc_shmem/'
        num_write_bytes = 32

        # get a list of shared memory regions
        out = subprocess.run(['ssh', host, "ls", shm_dir],
                universal_newlines=True, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        assert out.returncode == 0, eval(pytest.run_fail_str)
        shm_regions = out.stdout.splitlines()

        for shm_region in shm_regions:
            # write 0xff to each of num_write_bytes consecutive bytes of each shm_region
            out = self.run_tester_on_host(host, 0, [], ['-f', shm_dir +
                shm_region, '-s', str(num_write_bytes), '-w', '0xff'])
            assert out.returncode == 0, eval(pytest.run_fail_str)
            # now perform a read to confirm the write
            out = self.run_tester_on_host(host, 0, [], ['-f', shm_dir +
                shm_region, '-s', str(num_write_bytes), '-r'])
            read_contents = (re.search(r"Start:(.+)$", out.stdout).group(0))[6:]
            assert out.returncode == 0, eval(pytest.run_fail_str)
            assert read_contents == ' 0xff' * num_write_bytes

    def test_hpps_to_trch(self, qemu_instance_per_mdl, host):
        out = self.run_tester_on_host(host, 1, [], ['-i',
            '/dev/hpsc_shmem/region0', '-o', '/dev/hpsc_shmem/region1'])
        assert out.returncode == 0, eval(pytest.run_fail_str)

class TestRTITimer(SSHTester):
    testers = ["rtit-tester"]

    @pytest.mark.timeout(400)
    @pytest.mark.parametrize('core_num', range(8))
    def test_rti_timer_on_each_core(self, qemu_instance_per_mdl, host, core_num):
        out = self.run_tester_on_host(host, 0, ['taskset', '-c',
            str(core_num)], ["/dev/rti_timer" + str(core_num), str(2000)])
        assert out.returncode == 0, eval(pytest.run_fail_str)

class TestWDTimer(SSHTester):
    testers = ["wdtester"]

    # Each core starts its own watchdog timer and then kicks it.
    @pytest.mark.timeout(400)
    @pytest.mark.parametrize('core_num', range(8))
    def test_kicked_watchdog_on_each_core(self, hpps_serial_per_fnc, host,
            core_num):
        hpps_serial_per_fnc.sendline("taskset -c " + str(core_num) + " " +
                "/opt/hpsc-utils/wdtester /dev/watchdog" + str(core_num) + " 1")

        # the expect call below should return a 0 on a successful match
        assert(hpps_serial_per_fnc.expect("Kicking watchdog: yes") == 0)

    # Each core starts its own watchdog timer but does not kick it.
    @pytest.mark.timeout(800)
    @pytest.mark.parametrize('core_num', range(8))
    def test_unkicked_watchdog_on_each_core(self, hpps_serial_per_fnc, host,
            core_num):
        hpps_serial_per_fnc.sendline("taskset -c " + str(core_num) + " " +
            "/opt/hpsc-utils/wdtester /dev/watchdog" + str(core_num) + " 0")

        # the expect calls below should return a 0 on a successful match
        assert(hpps_serial_per_fnc.expect("Kicking watchdog: no") == 0)
        # after HPPS reboot, its login prompt should appear
        assert(hpps_serial_per_fnc.expect("hpsc-chiplet login: ") == 0)

class TestSRAM(SSHTester):
    testers = ["sram-tester"]

    # This SRAM test will modify an array in SRAM, reboot HPPS (using a
    # watchdog timeout), then check that the SRAM array is the same.
    # Since this test will boot QEMU, then reboot QEMU, it is given more time.
    @pytest.mark.timeout(800)
    def test_non_volatility(self, hpps_serial_per_fnc, host): # TODO: per_mdl shoud work
        # increment the first 100 elements of the SRAM array by 2, then reboot
        # HPPS
        out = self.run_tester_on_host(host, 0, [], ["-s", "100", "-i", "2"])
        assert out.returncode == 0, eval(pytest.run_fail_str)
        sram_before_reboot = re.search(r'Latest SRAM contents:(.+)',
                out.stdout, flags=re.DOTALL).group(1)

        # currently rebooting HPPS requires having the watchdog time out
        hpps_serial_per_fnc.sendline("taskset -c 0 " +
                "/opt/hpsc-utils/wdtester /dev/watchdog0 0")
        assert(hpps_serial_per_fnc.expect("hpsc-chiplet login: ") == 0)
        hpps_serial_per_fnc.sendline('root')
        assert(hpps_serial_per_fnc.expect('root@hpsc-chiplet:~# ') == 0)

        # after the reboot, read the SRAM contents to verify that they haven't
        # changed
        out = self.run_tester_on_host(host, 0, [], ["-s", "100"])
        assert out.returncode == 0, eval(pytest.run_fail_str)
        sram_after_reboot = re.search(r'Latest SRAM contents:(.+)', out.stdout,
                flags=re.DOTALL).group(1)
        assert(sram_before_reboot == sram_after_reboot), \
            "SRAM array before reboot was: " + sram_before_reboot + \
            ", while SRAM array after reboot was: " + sram_after_reboot

        # return the SRAM contents to their original state
        out = self.run_tester_on_host(host, 0, [], ["-s", "100", "-i", "-2"])
        assert out.returncode == 0, eval(pytest.run_fail_str)
