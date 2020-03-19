HPSC Automated Tests
====================

This directory contains PyTest test scripts for testing various HPSC
functionality.

Prerequisites
-------------

Before running the scripts, the user should verify the
following:
* Python3 should be installed locally, along with the following packages:
`pyserial`, `pexpect`, `pytest`, `pytest-timeout`.  On a CentOS 7 machine,
the following commands should suffice:

```shell
yum -y install https://centos7.iuscommunity.org/ius-release.rpm
yum -y install python36-pip
pip3 install --upgrade pip
pip3 install pyserial pexpect pytest pytest-timeout
```

* The `CODEBUILD_SRC_DIR` environment variable should be set to the absolute
path of the directory where the `hpsc-bsp` directory is located (not to the
`hpsc-bsp` directory itself).  On AWS CodeBuild, this is done automatically.
In any other environment, it needs to be set.
* The remote machine which will be tested should be up and running.  In
addition, the local machine should be able to connect to this machine by
hostname alone.  For instance, in order to connect to HPSC QEMU, the following
"config" file can be placed in the user's .ssh directory:

```shell
Host hpscqemu
     HostName localhost
     User root
     Port 3088
     StrictHostKeyChecking no
     UserKnownHostsFile=/dev/null
```

Running the Tests
-----------------

Add to SDK tools to Python module lookup path:

    export PYTHONPATH="$CODEBUILD_SRC_DIR/sdk/tools:$PYTHONPATH"

Once the prerequisites are met,

The full test suite can be run as follows:

    pytest -sv --host [hostname] --durations=0

Individual tests can be run as follows:

    pytest -sv --host [hostname] --durations=0 -k [filter_pattern]

where `[filter_pattern]` can be a substring of the module file, name of the
class (a group of tests) or of the test function itself, and multiple can be
joined by logical operations in Python language (e.g. `or`, `not`).

E.g., to run DMA tests given that Qemu HPPS Linux host is configured under
`hpsc-hpps-qemu` (in `~/.ssh/config`):

    pytest -sv --host hpsc-hpps-qemu --durations=0 -k TestDMA

Log files for Qemu and for each serial port on the machine are placed in the
`logs/` subdirectory in the run directory (current directory by default, or one
specified with `--run-dir`). You may monitor any of the logs as the tests run,
like so:

    tail -f logs/serial0.log

After the exeuction of each Qemu instance, a copy of each log files is saved
in a file named like the original with a timestamp appended, for preservation
of all output that happened during the test session. The monitoring as shown
above will keep displaying the conent, as the "current" file is overwritten by
new Qemu instances as the tests run.

Three of the test group (`TestSRAM` and `TestWDT` classes, and `test_nand.py`)
require a HPPS reboot via a watchdog timeout. These tests will fail in boot
configuration profiles named `sys-preload-*` where binaries are preloaded into
memory by the emulator (as opposed by by TRCH software). Run these tests
against profiles named `sys-nvmem-*`.

Finally, the buildspec file (buildspec.yml) is in this directory and can be pointed to by
AWS CodeBuild in order to execute tests on that service.
