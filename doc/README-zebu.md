HOW TO: Run the HPSC SSW stack in Qemu and Zebu on SCS server

Get the source
==============

On the `scsrt` server (not `scs` server), create a working directory for you on
the network share:

    $ mkdir /projects/boeing/$(whoami)
    $ cd /projects/boeing/$(whoami)

Get the source by cloning `zebu` branch of the parent repository
non-recursively (because SCS server is offline), and running the init script to
override the (Internet) URLs of nested submodules to the the paths relative to
the parent repository (on the SCS server):

    $ git clone -b zebu /projects/boeing/isi/hpsc
    $ cd hpsc
    $ ./init-relative.sh

Configure the environment for SCS server
========================================

Working on SCS server requires some configuration, to handle the fact
that the server is offline (without Internet access), so create a
per-working-copy config file (you only need to do this once):

	$ cd hpsc
	$ echo 'source ${SELF_DIR}/fetchcache-relative.sh' > .hpscrc

Load the HPSC environment into the shell
========================================

Every time you want to work on the HPSC in a new shell, start a Bash shell and
load the HPSC environment (also, make sure your environment is clean -- ensure
that no environment files been loaded):

    $ cd hpsc
    $ bash
    $ source env.sh

Do not configure your shell to load this environment automatically (e.g. via
`~/.bashrc`) because it will pollute your environment potentially breaking
other work not related to HPSC.

Build the HPSC SDK
==================

Make sure you have setup environment in your current shell,
as described in the previous section.

Enter the top-level directory in the working copy of the HPSC repository:

    $ cd hpsc

Build the sysroot against which the SDK will be build (~5 min on 16 cores):

    $ make sdk/deps/sysroot

Re-load the environment to load the newly built sysroot into the shell:

    $ source env.sh

Build the SDK including Zebu harness (includes Qemu emulator and host tools):

    $ make sdk sdk/zebu

Re-load the environment to load the newly built sysroot into the shell:

    $ source env.sh

More details in the generic documentation in [README.md](README.md).

Build, run, and debug the HPSC System Software Stack
====================================================

Ensure that the HPSC environment has been loaded into the current shell (see
the above).

The following instructions assume you are in top-level `hpsc` directory,
so make targets are prefixed with `ssw/`. Alternatively, you may `cd` into `ssw/`
directory and omit the `ssw/` prefix in targets.

Note: targets must not have a trailing `/`.

The HPSC SSW stack can be built in one of several configuration profiles.  List
the available configuration profiles (runnable profiles are prefixed with
`sys-`):

	$ make ssw
	$ make ssw/list/sys

To list profiles along with descriptions:

	$ make desc
	$ make desc/sys

Note that the profile description indicates if the profile depends on other
profiles, which must be built ahead of time (manually, and in sequence one at a
time -- a current limitation of infrastructure).

Not all profiles are supported on Zebu, currently, the pofiles that are
compatible with Zebu will have the configuration identified in the following
name pattern `sys-preload-trch-bm-min-hpps-128M-*-atf-sev-ub-nodcd-booti-busybox`:
 * `trch-bm-min`: TRCH BM app configured for minimal feature set (relevant when
    the profile is run in Qemu)
 * `hpps-128M`: HPPS SW stack (and Qemu model) is configured for HPPS DDR of
   size 128M
 * `atf-sev`: a ***workaround*** hack is applied to ATF to execute an SEV
   instruction soon after reset, because on Zebu emulator (not on HAPS), the
   A53 processor executes extremely slowly until it executes an SEV instruction.
 * `ub-nodcd`: a ***workaround*** hack is applied to U-boot to not disable
    EL0/EL1 A53 Data Cache before jumping to Linux because doing so generates
    an abort exception on Zebu and on HAPS.
 * `booti`: U-boot is configured to boot uncompressed Linux kernel with `booti`
   command (for faster boot)
 * `busybox`: the HPPS SW stack consists of ATF+U-boot+Linux and Busybox on a
   very basic initramfs

Several profiles that match the above categories are defined with `*` in the
above pattern filled in with:
 * `smc`: enable the SMC-353 controller and drivers
 * `eth-snps`: Synopsys DW QoS Ethernet NIC and driver enabled
 * `smp4` and `smp8`: boot with multiprocessor mode (does not work -- pending a
   way to command Zebu harness to reset secondary CPUs from within Linux/ATF)
 * `` (nothing): without the Dcache disable workaround in U-boot (will hang,
   use for debugging the issue)

Profiles runnable on Zebu are also runnable in Qemu (Qemu will be configured to
match the HW configuration of Zebu):

***IMPORTANT***: When switching between different profiles, make sure to
(shallowly) clean the new profile before using it (for details see section on
switching profiles in `ssw/hpsc-utils/doc/README.md`):

	$ make ssw/prof/PROFILE/bld/clean

To (incrementally) build and run the selected profile in Zebu (subsitute
`PROFILE` with the full profile name):

	$ make ssw/prof/PROFILE/run/zebu

In a different shell (also with SDK environment loaded!), connect to the serial
console on HPPS UART:

    $ screen -r zebu-uart-hpps

To quit ZeBu emulator:

    % quit

A stackdump and a hang on exit from Zebu is commonly observed. If the ZeBu
process fails to exit, then send it to background with `Ctrl-Z` and kill the
job:

    $ kill %1

For more info about running in ZeBu see the respective section in main
[README.md](README.md).

To (incrementally) build run the selected profile in Qemu:

	$ make ssw/prof/PROFILE/run/qemu

In a different shell (also with HPSC environment loaded!) connect to the serial
console screen session printed when Qemu runs.  Use a separate shell for each
serial port (and make sure that each shell has the HPSC environment loaded into
it!), for HPPS:

    $ screen -r hpsc-0-hpps

To alter Zebu configuration and scripts, modify the files in `sdk/zebu/`.

Building memory images and other artifacts invidually
-----------------------------------------------------

The above targets automatically build all artifacts necessary for the
respective run. It is also possible to build those artifacts individually, for
example the memory images loaded into the emulator, as described below.

To only produce the artifacts necessary to run in Zebu (memory images, memory
loader configuration file), without actually running, for the selected profile:

	$ make ssw/prof/PROFILE/bld/zebu

The generated configuration file for Zebu with paths to generated memory images
and the information into which memory each image should be loaded is going to
be generated in the following file:

	$ cat ssw/prof/PROFILE/bld/zebu/preload.zebu.mem.map

The memory images will be in that same directory, named `*.mem.raw` or
`*.mem.vhex`, for example, the memory image for the HPPS DRAM will be:

	$ ls -lh ssw/prof/PROFILE/bld/zebu/hpps.dram.mem.raw

Complete documentation on building and running profiles
-------------------------------------------------------

See instructions in the generic documentation for how to rebuild, run, and
debug a profile in more detail: [README.md](README.md).

Updating your working copy
==========================

Update will be pushed to the remote repository from which you cloned your
working copy. To update your local repository follow the instructions in
the section "Updating your workign copy of the repository" in README.md
at top level of the parent repository.

Transfering commits to and from server
======================================

The `scsrt` server is "offline" (i.e. cannot reach Internet hosts) and cannot
directly push to repositories over the Internet. To push to repos over
the Internet (e.g. Github), commits made in the repository on the server need
to be passed through a clone on an "online" host (e.g. your laptop).

First, for convenience, On the online host, add a host alias for the IP of the
`scsrt` server in `/etc/hosts`:

    1.2.3.4 scsrt

And, configure SSH such that `ssh scsrt` works, in `~/.ssh/config`:

    Host scsrt
        User your_scs_username

And, setup key-based SSH login:

    $ ssh-copy-id scsrt

Next, create a clone on your online host and use that clone to fetch from
or push to the server, and to fetch from and push to the Internet repository.
There are two options for creating this intemediate clone: either clone the
whole repository or clone individual components.

### Option A: clone the whole repository

Clone the repository from the `scsrt` server to your online host and re-point
the submodule paths to refer to the server via SSH (`sdk/qemu` requires an
extra step because it uses submodules itself):

	$ git clone scsrt:/projects/boeing/your_scs_username/hpsc
	$ cd hpsc
	$ sed -i 's#url = /#url = scsrt:/#' .gitmodules
	$ git submodule init
	$ git submodule update sdk/qemu
	$ sed -i 's#url = /#url = scsrt:/#' sdk/qemu/.gitmodules
	$ git submodule update --recursive

For each component you are interested in, add the Internet remote clone, for
example, for HPPS Linux:

	$ cd ssw/hpps/linux
	$ git remote add gh git@github.com:ISI-apex/linux.git

To fetch commits from the server and push them to the (Internet) remote:

	$ cd ssw/hpps/linux
	$ git fetch origin
	$ git push gh origin/somebranch:somebranch

Or, to push commits to the server:

	$ cd ssw/hpps/linux
	$ git push origin hpsc:hpsc

### Option B: clone individual components

Clone each component your are interested in, e.g. for HPPS Linux:

	$ git clone scsrt:/projects/boeing/your_scs_username/hpsc/ssw/hpps/linux
	$ cd linux
	$ git remote add gh git@github.com:ISI-apex/linux.git

Fetching commits from server and pushing them to other remotes is same as
for Option A.

### Option C: add a remote to an existing clone

If you already have a clone of an existing component, then you can add
the server clone as remote, e.g. for HPPS Linux:

	$ cd your/existing/linux
	$ git remote add scsrt scsrt:/projects/boeing/your_scs_username/hpsc/ssw/hpps/linux

To fetch commits from the server and push them to the above remote:

	$ cd ssw/hpps/linux
	$ git fetch scsrt
	$ git push origin scsrt/somebranch:somebranch

Or, to push commits to the server:

	$ cd ssw/hpps/linux
	$ git push scsrt somebranch:somebranch

## Pushing into a clone

Note that to push, the destination repo on the server must not be checked out
at the branch to which you are pushing. If it is, then either push to a
different branch then check it out, or checkout into a different branch on the
server (`git checkout -b local-hpsc`) and then push.
