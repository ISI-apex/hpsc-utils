import serial
import subprocess
import pytest
import os
import shutil
import re
import time
import threading
import pexpect
from pexpect.fdpexpect import fdspawn

from qmp import QMP

# If not specifying --run-dir, then make sure that the CODEBUILD_SRC_DIR env
# var is set.  This is the directory where the hpsc-bsp directory is located.
# On AWS CodeBuild, this is done automatically.  In any other environment, it
# needs to be set.

def pytest_configure():
    # This string will be evaluated whenever a call to subprocess.run fails
    pytest.run_fail_str = "\"\\nARGS:\\n\" + str(out.args) + \"\\nRETURN CODE:\\n\" + str(out.returncode) + \"\\nSTDOUT:\\n\" + out.stdout + \"\\nSTDERR:\\n\" + out.stderr"

def sink_serial_port(conn, stop_ev):
    """Consume data from a pexpect file descriptor to prevent stall.

    If the FIFO of the PTY fills up, the QEMU thread of the respective target
    processor simply stalls -- this has been observed. Also, this way we
    capture asynchronous output, that may show up at the console at a time not
    tied to our pexpect send-expect calls (e.g. while we're running commands
    over SSH).
    """
    while not stop_ev.is_set():
        poll_interval = 2 # check for request to stop (seconds)
        r = conn.expect([pexpect.TIMEOUT, pexpect.EOF], poll_interval)
        if r == 0:
            continue
        elif r == 1:
            return

def start_sink_thread(fd):
    stop_ev = threading.Event()
    th = threading.Thread(target=sink_serial_port, args=(fd, stop_ev))
    th.start()
    return fd, th, stop_ev

def stop_sink_thread(th, stop_ev):
    stop_ev.set()
    th.join()

# This function will bringup QEMU, expose a serial port for each subsystem (called "serial0",
# "serial1" and "serial2" for TRCH, RTPS, and HPPS respectively in the returned dictionary
# object), then perform a QEMU teardown when the assigned tests complete.
def qemu_instance(config):
    ser_baudrate = 115200
    ser_fd_timeout = 1000
    qemu_stdout_timeout = 1000
    log_dir_name = 'logs'
    tstamp = time.strftime('%Y%m%d%H%M%S')

    qemu_cmd = config.getoption('qemu_cmd')
    run_dir = config.getoption('run_dir')
    if run_dir is None:
        run_dir = os.path.join(os.environ['CODEBUILD_SRC_DIR'], "hpsc-bsp")

    log_dir = os.path.join(run_dir, log_dir_name)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Create a ser_fd dictionary object with each subsystem's serial file descriptor
    ser_fd = dict();
    log_files = []

    # Now start QEMU without any screen sessions
    # Note that the Popen call below combines stdout and stderr together
    qmp_port = None
    qemu_log_name = 'qemu'
    qemu_log = open(os.path.join(log_dir, qemu_log_name + '.log'), "wb")
    qemu = pexpect.spawn(qemu_cmd, cwd=run_dir, timeout=qemu_stdout_timeout,
            logfile=qemu_log)
    log_files.append((qemu_log_name, qemu_log))

    qemu.expect('QMP_PORT = (\d+)')
    qmp_port = int(qemu.match.group(1))

    # Consume, so that FIFO does not fill up, causing the process to halt
    ser_fd["qemu"] = start_sink_thread(qemu)

    qmp = QMP('localhost', qmp_port, timeout=10)

    reply = qmp.command("query-chardev")
    cdevs = reply["return"]
    pty_devs = {}
    for cdev in cdevs:
        devname = cdev[u"filename"]
        if devname.startswith('pty:'):
            pty_devs[cdev[u"label"]] = devname.split(':')[1]
    
    # Association defined by order of UARTs in Qemu machine model (device tree)
    trch_ser_port, rtps_ser_port, hpps_ser_port = "serial0", "serial1", "serial2"

    # Connect to the serial ports, then issue a continue command to QEMU
    trch_ser_log = open(os.path.join(log_dir, trch_ser_port + '.log'), "wb")
    log_files.append((trch_ser_port, trch_ser_log))
    trch_ser_conn = serial.Serial(port=pty_devs[trch_ser_port], baudrate=ser_baudrate)
    trch_ser_fd = fdspawn(trch_ser_conn, timeout=ser_fd_timeout, logfile=trch_ser_log)

    rtps_ser_log = open(os.path.join(log_dir, rtps_ser_port + '.log'), "wb")
    log_files.append((rtps_ser_port, rtps_ser_log))
    rtps_ser_conn = serial.Serial(port=pty_devs[rtps_ser_port], baudrate=ser_baudrate)
    rtps_ser_fd = fdspawn(rtps_ser_conn, timeout=ser_fd_timeout, logfile=rtps_ser_log)

    hpps_ser_log = open(os.path.join(log_dir, hpps_ser_port + '.log'), "wb")
    log_files.append((hpps_ser_port, hpps_ser_log))
    hpps_ser_conn = serial.Serial(port=pty_devs[hpps_ser_port], baudrate=ser_baudrate)
    hpps_ser_fd = fdspawn(hpps_ser_conn, timeout=ser_fd_timeout, logfile=hpps_ser_log)

    qmp.command("cont")

    trch_ser_fd.expect('\[\d+\] Waiting for interrupt...')

    # Check for the RTEMS shell prompt on RTPS
    rtps_ser_fd.expect('SHLL \[/\] # ')

    # Log into HPPS Linux
    hpps_ser_fd.expect('hpsc-chiplet login: ')
    hpps_ser_fd.sendline('root')
    hpps_ser_fd.expect('root@hpsc-chiplet:~# ')

    # Eat the output until a test request a fixture for the respective port
    ser_fd["serial0"] = start_sink_thread(trch_ser_fd)
    ser_fd["serial1"] = start_sink_thread(rtps_ser_fd)
    ser_fd["serial2"] = start_sink_thread(hpps_ser_fd)

    yield ser_fd

    pid = qemu.pid

    for fd, th, ev in ser_fd.values():
        stop_sink_thread(th, ev)
        fd.close()

    qemu.terminate()

    for log_name, log_file in log_files:
        log_file.close()
        shutil.copyfile(os.path.join(log_dir, log_name + '.log'),
                os.path.join(log_dir,
                    log_name + '.' + tstamp + '.' + str(pid) + '.log'))

@pytest.fixture(scope="module")
def qemu_instance_per_mdl(request):
    yield from qemu_instance(request.config)

@pytest.fixture(scope="function")
def qemu_instance_per_fnc(request):
    yield from qemu_instance(request.config)

def use_console(qemu_inst, serial_port):
    fd, th, ev = qemu_inst[serial_port]

    # Pause eating the output
    stop_sink_thread(th, ev)

    yield fd

    # Resume eating the output
    qemu_inst[serial_port] = start_sink_thread(fd)

# The serial port fixture is always per function, for either Qemu instance scope. */
@pytest.fixture(scope="function")
def trch_serial(qemu_instance_per_mdl):
    yield from use_console(qemu_instance_per_mdl, "serial0")
@pytest.fixture(scope="function")
def rtps_serial(qemu_instance_per_mdl):
    yield from use_console(qemu_instance_per_mdl, "serial1")
@pytest.fixture(scope="function")
def hpps_serial(qemu_instance_per_mdl):
    yield from use_console(qemu_instance_per_mdl, "serial2")

# The serial port fixture is always per function, for either Qemu instance scope. */
@pytest.fixture(scope="function")
def trch_serial_per_fnc(qemu_instance_per_fnc):
    yield from use_console(qemu_instance_per_fnc, "serial0")
@pytest.fixture(scope="function")
def rtps_serial_per_fnc(qemu_instance_per_fnc):
    yield from use_console(qemu_instance_per_fnc, "serial1")
@pytest.fixture(scope="function")
def hpps_serial_per_fnc(qemu_instance_per_fnc):
    yield from use_console(qemu_instance_per_fnc, "serial2")

def pytest_addoption(parser):
    parser.addoption("--host", action="store", help="remote hostname")
    parser.addoption("--run-dir", action="store", help="directory where to invoke Qemu")
    parser.addoption("--qemu-cmd", action="store", help="command to use to invoke Qemu",
            default="./run-qemu.sh -e ./qemu-env.sh -- -S -D")

def pytest_generate_tests(metafunc):
    # this is called for every test
    opts = {
        'host':     metafunc.config.option.host,
    }

    for opt, val in  opts.items():
        if opt in metafunc.fixturenames and val is not None:
            metafunc.parametrize(opt, [val])
