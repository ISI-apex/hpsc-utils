import subprocess
import pytest
import os
import shutil
import re
import time
import threading
import queue
import pexpect
from pexpect.fdpexpect import fdspawn

from qmp import QMP

# If not specifying --run-dir, then make sure that the CODEBUILD_SRC_DIR env
# var is set.  This is the directory where the hpsc-bsp directory is located.
# On AWS CodeBuild, this is done automatically.  In any other environment, it
# needs to be set.

def pytest_configure():
    # This string will be evaluated whenever a call to subprocess.run fails
    pytest.run_fail_str = "\"\\nARGS:\\n\" + str(out.args) + \"\\nRETURN CODE:\\n\" + str(out.returncode) + \"\\nSTDOUT:\\n\" + out.stdout.decode('ascii') + \"\\nSTDERR:\\n\" + out.stderr.decode('ascii')"

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

SPAWN_ARGS = dict(encoding='ascii', codec_errors='ignore', timeout=1000)

# TODO: These might need to be dynamic: not all profiles use all subsystems
trch_port = "serial0"
rtps_port = "serial1"
hpps_port = "serial2"

class Req:
    pass
class ExpectReq(Req):
    def __init__(self, patterns):
        self.patterns = patterns
class SendLineReq(Req):
    def __init__(self, line):
        self.line = line
class SendIntrReq(Req):
    pass
class StartEatReq(Req):
    pass
class StopEatReq(Req):
    pass
class PidReq(Req):
    pass
class WaitReq(Req):
    pass
class StopReq(Req):
    pass

class Resp:
    pass
class ErrorResp(Resp):
    def __init__(self, exc):
        self.exc = exc
class RcResp(Resp):
    def __init__(self, rc, match=None):
        self.rc = rc
        self.match = match
class PidResp(Resp):
    def __init__(self, pid):
        self.pid = pid

class Chan:
    def __init__(self):
        self.req_qu = queue.Queue(maxsize=1)
        self.resp_qu = queue.Queue(maxsize=1)

    # private
    def do_rc_req(self, req):
        self.req_qu.put(req)
        ret = self.resp_qu.get()
        if isinstance(ret, RcResp):
            return ret.rc
        elif isinstance(ret, ErrorResp):
            raise Exception("request to pexpect thread failed") from ret.exc

    def expect(self, patterns):
        # Mimic pexpect interface
        if not isinstance(patterns, list):
            patterns = [patterns]

        self.req_qu.put(ExpectReq(patterns))
        ret = self.resp_qu.get()
        if isinstance(ret, RcResp):
            if ret.match is not None:
                self.match = ret.match
            return ret.rc
        elif isinstance(ret, ErrorResp):
            raise Exception("expect request failed") from ret.exc

    def sendline(self, line):
        return self.do_rc_req(SendLineReq(line))

    def sendintr(self):
        return self.do_rc_req(SendIntrReq())

    # private
    def do_eat_req(self, req):
        self.req_qu.put(req)
        ret = self.resp_qu.get()
        assert isinstance(ret, RcResp)
        assert ret.rc == 0

    def start_eat(self):
        self.do_eat_req(StartEatReq())

    def stop_eat(self):
        self.do_eat_req(StopEatReq())

    def wait(self):
        return self.do_rc_req(WaitReq())

    def pid(self):
        self.req_qu.put(PidReq())
        ret = self.resp_qu.get()
        assert isinstance(ret, PidResp)
        return ret.pid

    def stop(self):
        self.req_qu.put(StopReq())

# We want ability to consume streams in the background to get all log, not just
# the log during our expect calls) and to prevent Qemu CPU thread blocking when
# some FIFO along the serial port output path fills up (not 100% confirmed that
# this is happening, but suspected as root cause of stalls; might be PySerial
# related). So we need background threads that call expect(EOF).
#
# BUT Pexpect handles cannot be passed among threads (accoding to Common
# Problems in the docs; it appwars to work, but we won't risk it), so we need
# to spawn to get a handle within the thread and only use it from that thread.
# Also, having multiple spawns done from the same thread may not be supported
# by pexpect (again, appears to work, but we won't risk it).
def attach_port(port, pty, log, chan):
    conn = os.open(pty, os.O_RDWR|os.O_NONBLOCK|os.O_NOCTTY)
    handle = fdspawn(conn, logfile=log, **SPAWN_ARGS)
    service_loop(handle, chan)
    handle.close() # closes the conn file descriptor

def spawn(cmd, cwd, log, chan):
    handle = pexpect.spawn(cmd, cwd=cwd, logfile=log, **SPAWN_ARGS)
    service_loop(handle, chan)
    handle.close()

def service_loop(handle, chan):
    poll_interval = 2 # check for requests (seconds)
    eat = False
    run = True
    while run:
        try:
            req = chan.req_qu.get(timeout=poll_interval)
            if isinstance(req, ExpectReq) or \
                    isinstance(req, SendLineReq) or \
                    isinstance(req, SendIntrReq):
                try:
                    if isinstance(req, ExpectReq):
                        r = handle.expect(req.patterns)
                        chan.resp_qu.put(RcResp(r, handle.match))
                    elif isinstance(req, SendLineReq):
                        r = handle.sendline(req.line)
                        chan.resp_qu.put(RcResp(r))
                    elif isinstance(req, SendIntrReq):
                        r = handle.sendintr() # not available for fdspawn
                        chan.resp_qu.put(RcResp(r))
                except Exception as e:
                    chan.resp_qu.put(ErrorResp(e))
            elif isinstance(req, StartEatReq):
                eat = True
                chan.resp_qu.put(RcResp(0))
            elif isinstance(req, StopEatReq):
                eat = False
                chan.resp_qu.put(RcResp(0))
            elif isinstance(req, WaitReq):
                r = handle.wait()
                chan.resp_qu.put(RcResp(r))
            elif isinstance(req, PidReq):
                chan.resp_qu.put(PidResp(handle.pid))
            elif isinstance(req, StopReq):
                run = False
        except queue.Empty:
            pass
        if eat:
            # Suprizingly, EOF does happen sometimes, even though files not
            # closed while we're here. Not sure why. Expect EOF too, then.
            handle.expect([pexpect.TIMEOUT, pexpect.EOF], poll_interval)

# This function will bringup QEMU, and create a channel to each serial port
# in the Qemu machine; then perform a QEMU teardown when the assigned tests complete.
def qemu_instance(config):
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
    handles = {}

    # Now start QEMU without any screen sessions
    # Note that the Popen call below combines stdout and stderr together
    qemu_log_name = 'qemu'
    qemu_log = open(os.path.join(log_dir, qemu_log_name + '.log'), "w")
    log_files.append((qemu_log_name, qemu_log))

    qemu = Chan()
    qemu_th = threading.Thread(target=spawn, args=(qemu_cmd, run_dir, qemu_log, qemu))
    qemu_th.start()
    qemu_pid = qemu.pid()

    qemu.expect('QMP_PORT = (\d+)')
    qmp_port = int(qemu.match.group(1))

    qemu.expect('\(qemu\) ') # just for good measure
    qemu.start_eat() # consume to get log and avoid blocking due to full FIFOs

    qmp = QMP('localhost', qmp_port, timeout=10)

    reply = qmp.command("query-chardev")
    cdevs = reply["return"]
    pty_devs = {}
    for cdev in cdevs:
        devname = cdev[u"filename"]
        if devname.startswith('pty:'):
            pty_devs[cdev[u"label"]] = devname.split(':')[1]
    
    # Association defined by order of UARTs in Qemu machine model (device tree)
    serial_ports = ["serial0", "serial1", "serial2"]
    threads = {}
    chans = {}

    # Connect to the serial ports, then issue a continue command to QEMU
    for port in serial_ports:
        log = open(os.path.join(log_dir, port + '.log'), "w")
        log_files.append((port, log))

        chans[port] = Chan()
        threads[port] = threading.Thread(target=attach_port,
                        args=(port, pty_devs[port], log, chans[port]))
        threads[port].start()

    qmp.command("cont")

    # For convenience
    trch = chans[trch_port]
    rtps = chans[rtps_port]
    hpps = chans[hpps_port]

    # Wait for subsystems to boot
    trch.expect('\[\d+\] Waiting for interrupt...')
    rtps.expect('SHLL \[/\] # ')
    # Log into HPPS Linux
    hpps.expect('hpsc-chiplet login: ')
    hpps.sendline('root')
    hpps.expect('root@hpsc-chiplet:~# ')

    # Eat the output until a test requests a fixture for the respective port
    for chan in chans.values():
        chan.start_eat()

    yield chans

    for chan in chans.values():
        chan.stop_eat()
        chan.stop()
    for th in threads.values():
        th.join()

    qemu.stop_eat()
    qemu.sendline("quit")
    qemu.expect(pexpect.EOF)
    rc = qemu.wait()
    assert rc == 0, "Qemu process exited uncleanly"
    qemu.stop()
    qemu_th.join()

    for log_name, log_file in log_files:
        log_file.close()
        shutil.copyfile(os.path.join(log_dir, log_name + '.log'),
                os.path.join(log_dir,
                    log_name + '.' + tstamp + '.' + str(qemu_pid) + '.log'))

@pytest.fixture(scope="module")
def qemu_instance_per_mdl(request):
    yield from qemu_instance(request.config)

@pytest.fixture(scope="function")
def qemu_instance_per_fnc(request):
    yield from qemu_instance(request.config)

def use_console(qemu_inst, serial_port):
    chan = qemu_inst[serial_port]

    chan.stop_eat() # Pause eating the output
    yield chan
    chan.start_eat() # Resume eating the output

# The serial port fixture is always per function, for either Qemu instance scope. */
@pytest.fixture(scope="function")
def trch_serial(qemu_instance_per_mdl):
    yield from use_console(qemu_instance_per_mdl, trch_port)
@pytest.fixture(scope="function")
def rtps_serial(qemu_instance_per_mdl):
    yield from use_console(qemu_instance_per_mdl, rtps_port)
@pytest.fixture(scope="function")
def hpps_serial(qemu_instance_per_mdl):
    yield from use_console(qemu_instance_per_mdl, hpps_port)

# The serial port fixture is always per function, for either Qemu instance scope. */
@pytest.fixture(scope="function")
def trch_serial_per_fnc(qemu_instance_per_fnc):
    yield from use_console(qemu_instance_per_fnc, trch_port)
@pytest.fixture(scope="function")
def rtps_serial_per_fnc(qemu_instance_per_fnc):
    yield from use_console(qemu_instance_per_fnc, rtps_port)
@pytest.fixture(scope="function")
def hpps_serial_per_fnc(qemu_instance_per_fnc):
    yield from use_console(qemu_instance_per_fnc, hpps_port)

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
