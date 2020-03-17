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

Once the prerequisites are met, individual tests can be run as follows:

    pytest -sv --host [hostname] --durations=0 [test_file1] [test_file2] ... [test_fileN]

e.g., for a host named hpscqemu:

    pytest -sv --host hpscqemu --durations=0 test_dma.py test_hotplug.py test_interrupt_affinity.py test_mbox.py test_mbox_multi_system.py test_mmu.py test_parallel_scaling.py test_shm.py test_timer_interrupt.py

In addition, the full test suite can be run as follows:

    pytest -sv --host [hostname] --durations=0

e.g.,

    pytest -sv --host hpscqemu --durations=0

However, three of the tests (test_nand.py, test_sram.py, and test_wdt.py) will fail with
the default boot configuration since they require a HPPS reboot via a watchdog timeout.  
In order for these three tests to succeed, the following needs to be specified in syscfg.ini:

    bin_loc = TRCH_SMC_SRAM
    rootfs_loc = HPPS_SMC_NAND

Finally, the buildspec file (buildspec.yml) is in this directory and can be pointed to by
AWS CodeBuild in order to execute tests on that service.
