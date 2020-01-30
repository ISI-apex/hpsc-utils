import serial
import subprocess
import pytest
import os
import re
from pexpect.fdpexpect import fdspawn

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

    # Create a file with unspecified port names so screen sessions to serial ports are disabled
    f = open("./qemu-env-override.sh", "w")
    f.write("SERIAL_PORT_NAMES[serial0]=\"\"\nSERIAL_PORT_NAMES[serial1]=\"\"\nSERIAL_PORT_NAMES[serial2]=\"\"\n")
    f.close()

    # Now start QEMU without any screen sessions
    # Note that the Popen call below combines stdout and stderr together
    p = subprocess.Popen(["./run-qemu.sh", "-e", "./qemu-env.sh", "-e", "./qemu-env-override.sh", "--", "-S"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    for stdout_line in iter(p.stdout.readline, ""):
        if ("QMP_PORT = " in stdout_line):
            qmp_port = re.search(r"QMP_PORT = (\d+)", stdout_line).group(1)
        elif ("(label serial0)" in stdout_line):
            trch_ser_port = re.search(r"char device redirected to (\S+)", stdout_line).group(1)
        elif ("(label serial1)" in stdout_line):
            rtps_ser_port = re.search(r"char device redirected to (\S+)", stdout_line).group(1)
        elif ("(label serial2)" in stdout_line):
            hpps_ser_port = re.search(r"char device redirected to (\S+)", stdout_line).group(1)
            break
    p.stdout.close()
    
    # Connect to the serial ports, then issue a continue command to QEMU
    # TEMPORARILY NOT LISTENING ON TRCH SERIAL PORT TO AVOID ISSUES ON AWS CODEBUILD
#    trch_ser_conn = serial.Serial(port=trch_ser_port, baudrate=ser_baudrate)
#    trch_ser_fd = fdspawn(trch_ser_conn, timeout=ser_fd_timeout)

    rtps_ser_conn = serial.Serial(port=rtps_ser_port, baudrate=ser_baudrate)
    rtps_ser_fd = fdspawn(rtps_ser_conn, timeout=ser_fd_timeout)

    hpps_ser_conn = serial.Serial(port=hpps_ser_port, baudrate=ser_baudrate)
    hpps_ser_fd = fdspawn(hpps_ser_conn, timeout=ser_fd_timeout)

    subprocess.run(["python3", "sdk/tools/qmp-cmd", "localhost", qmp_port, "cont"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)

    # Check for the RTEMS shell prompt on RTPS
    rtps_ser_fd.expect('SHLL \[/\] # ')

    # Log into HPPS Linux
    hpps_ser_fd.expect('hpsc-chiplet login: ')
    hpps_ser_fd.sendline('root')
    hpps_ser_fd.expect('root@hpsc-chiplet:~# ')

    # Create a ser_fd dictionary object with each subsystem's serial file descriptor
    ser_fd = dict();
#    ser_fd['serial0'] = trch_ser_fd
    ser_fd['serial1'] = rtps_ser_fd
    ser_fd['serial2'] = hpps_ser_fd

    yield ser_fd
    # This is the teardown
#    ser_fd['serial0'].close()
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
    option_value = metafunc.config.option.host
    if 'host' in metafunc.fixturenames and option_value is not None:
        metafunc.parametrize("host", [option_value])
