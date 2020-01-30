HPSC Linux Utilities
====================

This directory contains test utilities to be run in Linux on the HPPS subsystem.
To push files to HPPS running in Qemu, use scp:

    scp -P 10022 [FILE]... root@127.0.0.1:

e.g., 

    scp -P 10022 mboxtester rtit-tester shm-standalone-tester shm-tester wdtester root@127.0.0.1:

By default, the files will be in `/home/root/` on HPPS.

Build
-----

First, you must source the poky cross-toolchain environment setup script, then
unset the `LDFLAGS` environment variable, e.g.:

    . /opt/poky/2.6/environment-setup-aarch64-poky-linux
    unset LDFLAGS

Then you may build:

    make

You should see output lines using `aarch64-poky-linux-gcc`, like:

```sh
aarch64-poky-linux-gcc  --sysroot=/opt/poky/2.6/sysroots/aarch64-poky-linux -O0 -g -Wall -Wextra -O1 -g -o shm-tester shm-tester.c
```

If instead you see output like the following, the cross-compiler wasn't used:

```sh
cc -Wall -Wextra -O1 -g -o shm-tester shm-tester.c
```

For additional details, see:
https://www.yoctoproject.org/docs/2.6/sdk-manual/sdk-manual.html#makefile-based-projects

dma-tester.sh
-------------

The DMA tester performs DMA tests using the Linux DMA Test module that is built
into the kernel.  It allows the user to vary the test buffer size, threads per channel,
number of iterations, timeout, and DMA channel.  The usage is:

	./dma-tester.sh [-b TEST_BUF_SIZE] [-T THREADS_PER_CHAN] [-i ITERATIONS] [-t TIMEOUT] [-c CHANNEL] [-h]

Use the `-h` option for details.

interrupt-affinity-tester.sh
----------------------------

The interrupt affinity tester verifies that the interrupt from a DMA controller 
arrives at the specified HPPS core.  This is done by first finding a valid DMA
channel, then looking up the DMA controller for that channel, then identifying
the appropriate IRQ number for this DMA controller.  Next, the SMP affinity for
this IRQ is associated to the specified HPPS core number.  Then, a DMA is
performed (using the DMA Test module) on the DMA channel.  Finally, using
/proc/interrupts, the test verifies that the interrupt count for the specific
IRQ number and HPPS core number has incremented by one, which verifies that
the interrupt affinity for the DMA controller was set properly.  The usage is:

	./interrupt-affinity-tester.sh [-c cpu_num] [-h]

By default, HPPS core 0 is used.  Use the `-h` option for details.

mboxtester and mbox-multiple-core-tester
----------------------------------------

HPSC mboxtester and mbox-multiple-core-tester are Linux applications for sending a
message and reading a reply from a mailbox, either TRCH or RTPS. Both use the
mbox-utils.c file which uses a simple protocol for request and reply messages.
A separate command server processes these requests on TRCH and/or RTPS.

The mboxtester writes a request to the output mailbox and reads a reply from
the input mailbox. The usage is:

	./mboxtester [-o FILE] [-i FILE] [-O FILE] [-I FILE] [-n TYPE] [-t N] [-c CPU] [-h]

Use the `-h` option for details.

The input and output mailboxes can be specified by either the full path to the
device file, e.g. `/dev/mbox/0/mbox0` or as an index which will
be expanded into a path, e.g. `0` will expand into the above path.

If no arguments are specified, the following default is assumed: `./mboxtester -o 0 -i 1`.
Notification methods and timeouts can also be configured.

The mbox-multiple-core-tester has similar functionality to mboxtester, but its goal
is to check whether different HPPS cores can access the same mailboxes in consecutive
write-read mailbox transactions.  The usage is:

	./mbox-multiple-core-tester [-o FILE] [-i FILE] [-n TYPE] [-t N] [-C CPU] [-c CPU] [-l N] [-h]

Again, use the `-h` option for details.

shm-standalone-tester
---------------------

The shared memory standalone tester reads and writes to shared memory regions
specified in the device tree.  The usage is:

	./shm-standalone-tester -f FILE -s SIZE [-w BYTE] [-o OFF] [-p BYTE] [-r] [-l N] [-h]

For example, to read 32 bytes for `region0`:

	./shm-standalone-tester -f /dev/hpsc_shmem/region0 -s 32 -r

or to read and write `0xff` to the 32 bytes:

	./shm-standalone-tester -f /dev/hpsc_shmem/region0 -s 32 -r -w 0xff

The data is verified after writing by re-reading the the specified length.
Other test options include checking for prior values in the region and working
at a page offset within the region.
Use the `-h` option for further details.

shm-tester
----------

The shared memory tester reads and writes to shared memory regions specified in
the device tree that are shared with either TRCH or RTPS.  The tester performs
a simple PING/PONG with the remote server to verify that shared memory is working
and connected properly.  The usage is:

    ./shm-tester [-i FILE] [-o FILE] [-h]

Input and output file defaults are used if none are specified.
Use the `-h` option for further details.

sram-tester
-----------

The SRAM tester prints and modifies offchip SRAM.  In both cases, SRAM is mapped
into memory using mmap and later unmapped using munmap.  The usage is:

    ./sram-tester [-s SIZE] [-i N] [-h]

This tester will automatically print the latest contents of the array in SRAM,
whether it is modified or not.  The `SIZE` parameter above specifies the array size
(in ints).  The `-i` flag is used to modify the array by incrementing each of the
first SIZE elements in the SRAM array by N.  N is an integer but can be positive,
negative, or zero.  For instance, to increment the first 10 elements of the SRAM
array by 2, issue the command:

    ./sram-tester -s 10 -i 2

Use the `-h` option for further details.

wdtester
--------

This tester kicks watchdog devices at regular intervals.  The usage is:

    ./wdtester <device_file> <do_writes>

where `device_file` is the path to a watchdog dev file, e.g., `/dev/watchdog3`
and `do_writes` is a boolean value for whether it will actually kick (1) or not
(0).
Failure to kick a mailbox will result in the watchdog timing out.
The `wdtester` should also be fixed to the core that it's kicking, e.g.:

    taskset -c 3 ./wdtester /dev/watchdog3 1

Note that HPSC watchdogs cannot be stopped once they are started, but the SW
watchdog can.
See `/sys/class/watchdog/watchdog[N]/identity` to check type for watchdog `[N]`.
