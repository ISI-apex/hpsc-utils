import serial
import subprocess
import pytest
import os
import re
from pexpect.fdpexpect import fdspawn

from qmp import QMP

# Make sure that the CODEBUILD_SRC_DIR env var is set.  This is the directory
# where the hpsc-bsp directory is located.  On AWS CodeBuild, this is done
# automatically.  In any other environment, it needs to be set.

def pytest_configure():
    # This string will be evaluated whenever a call to subprocess.run fails
    pytest.run_fail_str = "\"\\nARGS:\\n\" + str(out.args) + \"\\nRETURN CODE:\\n\" + str(out.returncode) + \"\\nSTDOUT:\\n\" + out.stdout + \"\\nSTDERR:\\n\" + out.stderr"

# This function will bringup QEMU, expose a serial port for each subsystem (called "serial0",
# "serial1" and "serial2" for TRCH, RTPS, and HPPS respectively in the returned dictionary
# object), then perform a QEMU teardown when the assigned tests complete.
def qemu_instance():
    ser_baudrate = 115200
    ser_fd_timeout = 1000

    # Change to the hpsc-bsp directory
    os.chdir(str(os.environ['CODEBUILD_SRC_DIR']) + "/hpsc-bsp")


    flog = open("test.log", "wb")

    # Now start QEMU without any screen sessions
    # Note that the Popen call below combines stdout and stderr together
    p = subprocess.Popen(["./run-qemu.sh", "-e", "./qemu-env.sh", "--", "-S", "-q", "-D"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    for stdout_line in iter(p.stdout.readline, ""):
        flog.write(stdout_line.encode("utf8"))
        flog.flush()
        if ("QMP_PORT = " in stdout_line):
            qmp_port = re.search(r"QMP_PORT = (\d+)", stdout_line).group(1)
            break
    p.stdout.close()

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
    trch_ser_conn = serial.Serial(port=pty_devs[trch_ser_port], baudrate=ser_baudrate)
    trch_ser_fd = fdspawn(trch_ser_conn, timeout=ser_fd_timeout, logfile=flog)

    rtps_ser_conn = serial.Serial(port=pty_devs[rtps_ser_port], baudrate=ser_baudrate)
    rtps_ser_fd = fdspawn(rtps_ser_conn, timeout=ser_fd_timeout, logfile=flog)

    hpps_ser_conn = serial.Serial(port=pty_devs[hpps_ser_port], baudrate=ser_baudrate)
    hpps_ser_fd = fdspawn(hpps_ser_conn, timeout=ser_fd_timeout, logfile=flog)

    qmp.command("cont")


    # Check for the RTEMS shell prompt on RTPS
    rtps_ser_fd.expect('SHLL \[/\] # ')

    # Log into HPPS Linux
    hpps_ser_fd.expect('hpsc-chiplet login: ')
    hpps_ser_fd.sendline('root')
    hpps_ser_fd.expect('root@hpsc-chiplet:~# ')

    # Create a ser_fd dictionary object with each subsystem's serial file descriptor
    ser_fd = dict();
    ser_fd['serial0'] = trch_ser_fd
    ser_fd['serial1'] = rtps_ser_fd
    ser_fd['serial2'] = hpps_ser_fd

    yield ser_fd
    # This is the teardown
    ser_fd['serial0'].close()
    flog.close()
    ser_fd['serial1'].close()
    ser_fd['serial2'].close()
    p.terminate()

@pytest.fixture(scope="module")
def qemu_instance_per_mdl():
    yield from qemu_instance()

@pytest.fixture(scope="function")
def qemu_instance_per_fcn():
    yield from qemu_instance()

def pytest_addoption(parser):
    parser.addoption("--host", action="store", help="remote hostname")

def pytest_generate_tests(metafunc):
    # this is called for every test
    opts = {
        'host':     metafunc.config.option.host,
    }

    for opt, val in  opts.items():
        if opt in metafunc.fixturenames and val is not None:
            metafunc.parametrize(opt, [val])
