Guide to HPSC Source Release
============================

Ultra-condensed Quick-start
---------------------------

This section gives a very condensed summary of quickest way to get from an
extracted HPSC Source Release (or a cloned HPSC parent repository) to a BusyBox
prompt on HPPS Linux running in Qemu emulator on CentOS 7 (run as a user with
access to `sudo`, but not as `root`) -- takes about 5 minutes:

    $ source env.sh
    $ make sdk/deps/centos7
    $ make sdk
    $ source env.sh
    $ make ssw/prof/sys-preload-trch-bm-hpps-busybox/run/qemu

In another terminal connect to the target serial port:

    $ screen -r hpsc-0-hpps

Please do read the sections below for complete instructions. The instructions
include information for how to run on other Linux distributions, including
without root acccess, how to run in other target HW emulators, how to boot into
other target configuration profiles (e.g., boot from non-volatile memory, boot
Yocto Linux, etc), and other important information.

Load the HPSC environment into the shell
========================================

The HPSC environment file sets up some useful configuration, e.g.  sets all
invocations of make to be parallel by default, allows the the remote clone of
the source repository to be accessed by multiple users when cloned by file path
on an online server, loads the per-working-copy config, loads the HPSC SDK if
it is built.

Every time you want to work on the HPSC in a new shell, start a Bash shell and
load the HPSC environment (also, make sure your environment is clean -- ensure
that no environment files been loaded):

    $ cd hpsc
    $ bash
    $ source env.sh

Do not configure your shell to load this environment automatically (e.g. via
`~/.bashrc`) because it will pollute your environment potentially breaking
other work not related to HPSC.

Configure miscellaneous settings
--------------------------------

For users of the `vim` editor, to apply syntax highlighting to some of
the custom config files, add to your `~/.vimrc`:

    au BufRead,BufNewFile *.mem.map setfiletype sh

Build the HPSC SDK
==================

To build and run software for the target, you need the SDK for the HPSC
Chiplet. The HPSC SDK provides tools needed to build, run, and debug software
on the HPSC Chiplet hardware; as well as the Qemu emulator for the Chiplet and
tools to run on other emulators. Using the HSPC SDK, you may build and run the
HPSC System Software stack or develop your custom software stack.

The HPSC SDK is distributed in (mostly) source within the HPSC source release
tarball, and is also a module in the parent repository. Both origins ship both
the SDK and the HPSC System Software Stack together. The SDK components are
built in-place within its source tree.

Provide the HPSC SDK dependencies
---------------------------------

Before the HPSC SDK can be built from source, install its dependencies by take
**one** of the following paths:

* Option A: packages installed into the host system (requires root privilege)
* Option B: dependencies built from source to compose a sysroot

If you have root access to the machine, then Option A is recommended.

### Option A: dependencies installed in the system

Follow this option to prepare to build the SDK against libraries and tools
installed in the system (i.e. from the OS distribution's packages).

Distributions on which the installation was successfully done (not all are
officially supported):
* `centos7`: CentOS 7
* `arch`: Arch Linux

First, ensure that your user has sudo priviledge. On Cent OS and on Arch
distributions, it is enough to add the user to the `wheel` group and
re-login for it to take effect:

    # usermod -a -G wheel USERNAME

Optionally, to allow running `sudo` without prompting password, run `sudo
visudo` and uncomment the following line:

    %wheel  ALL=(ALL)       NOPASSWD: ALL

To install the necessary packages into your host system, run the following
target as root (`#` indicates a prompt with root privileges, which usually
means to run the command via `sudo`), replacing `DISTRO` with the identifier
for your distribution from above:

    # make sdk/deps/DISTRO

In case you need to repeat this step, clean it with the following before
repeating the above:

    # make sdk/deps/clean

### Option B: dependencies from a sysroot built from source

Follow this option to prepare to build the SDK against a sysroot built
from source. This option may be used on any distribution without root access --
however, manual fixing may be required if the sysroot fails to build on your
system out of the box (untested territory, by definition).  This sysroot is not
a complete sysroot -- it does rely on some most basic libraries and tools in
the system, but those are expected to be present on most Linux systems.

This section provides instructions on how to use the custom sysroot builder
shipped in the HPSC SDK to build the sysroot.

If the machine is offline without internet access, and if the HPSC source
release you have did not ship the sysroot source tarballs (check
`sdk/sysroot/bld/fetch`), then first fetch the source archives on a machine
with internet acccess, and copy the folling directories to the same paths in
the working copy of the source tree on the offline machine (in this example
using Rsync over SSH):

	online_host$ cd hpsc
	online_host$ make sdk/sysroot/fetch
	online_host$ rsync -aq sdk/sysroot/bld/fetch/ offline_host:/path/to/hpsc/sdk/sysroot/bld/fetch/

To build the sysroot and set it up as dependency for the SDK:

	$ make sdk/deps/sysroot

Re-load the environment to load the sysroot into the shell:

        $ source env.sh

#### Troubleshooting the sysroot

Should any components fail to build, these tips may be helpful.

Individual components can be built from top level by name; names are intuitive,
with dashes replaced by underscores, defined in `DEPS_*` vars in
`sdk/hpsc-sdk-tools/sysroot/Makefile`:

	$ cd sdk/hpsc-sdk-tools/sysroot/COMPONENT/clean
	$ cd sdk/hpsc-sdk-tools/sysroot/COMPONENT

Or, having navigated to the sysroot builder `sdk/hpsc-sdk-tools/sysroot`:

		$ make COMPONENT/clean
		$ make COMPONENT

The clean here wipes the build directory entirely.

To diagnose failures examine/edit the recipe for any component in `Makefile`.
You can also navigate to the component's build directory
`bld/work/COMPONENT_DIR`, modify sources, and re-run the make command at the
top level for an incremental rebuild.

Prepare an offline build
------------------------

The HPSC SDK includes some components whose source is shipped within the SDK,
and other external components whose source is fetched from upstream release
point and which are then built from source.

If the host on which you want to build the HPSC SDK is offline (cannot reach
the Internet), then you have to obtain the source tarballs somehow. The HPSC
source release may contain the source tarballs for external components, but if
you have cloned from Git, then follow the instructins in this section to fetch 
the components on an online host and transfer them to the offline host.

	online_host$ cd hpsc
	online_host$ make sdk/fetch
	online_host$ rsync -aq sdk/bld/fetch/ offline_host:/path/to/hpsc/sdk/bld/fetch/

Build the HPSC SDK
------------------

Ensure that the HPSC environment has been loaded into the shell (see above).

To build the HPSC SDK from source, in place within the source tree:

    $ make sdk

If you want to use networking via TUN/TAP devices, you need access to `sudo`
for root privileges to run the following installation target (run this target
as normal user, `sudo` will be invoked on demand):

    $ make sdk/qemu/install

### Troubleshoot HPSC SDK build

Components of the HPSC SDK can be cleaned and re-built individually on demand,
using targets that correspond to files and folders in the build directory tree
or the source directory tree. To rebuilt a target, append `/clean` to the
target, e.g. to rebuild the `env` target: `make env/clean && make env`. Summary
of targets:

* `qemu` (or `bld/qemu`): build and install Qemu emulator (out-of-tree)
* the target for a component built in-place is its source directory path:
  `hpsc-sdk-tools`, `qemu-devicetrees`
* the target for a component built out-of-tree is its build directory path:
  `bld/qemu` (this particular one is also aliased to `qemu`)
* `bld/sysroot/opt/bintc`: extract binary toolchains; to rebuild an individual
   toolchain, append its subdirectory followed by `/clean`
* `bld/extern`: build components fetched and built from source; to clean a
   component append its subdirectory followed by `/clean`; to extract only
   make the subdirectory target, to trigger build, make `bld/extern/COMPONENT`,
   where COMPONENT is the name without the version, e.g. `gdb`.
* `env` : generate environment file for loading the SDK into the shell

The SDK installs pre-compiled binary toolchains distributed by ARM/Linaro.
On hosts which are very old, with a glibc older than the one the toolchains
were linked against, the SDK builder will build a mini-sysroot with the
glibc built from source, and relocate the toolchain binaries to it. This will
happen automatically based on libc version detection, but for trouleshooting
the relevant targets are:

* `bld/bintc-sysroot`: build the mini-sysroot with a recent glibc
* `bld/sysroot/opt/bintc/TOOLCHAIN_SUBDIR/relocate`: perform relocation of
  the given toolchain

Load the HPSC SDK
-----------------

Re-load the HPSC environment to load the newly built SDK:

    $ source env.sh

Build the HPSC System Software Stack for the Chiplet target
===========================================================

Make sure you have loaded the HPSC SDK into your current shell (see above).

Change to the directory of the HSPC System Software Stack:

	$ cd ssw

The HPSC SSW stack can be built in one of several configuration profiles.  List
the available configuration profiles, and their descriptions, runnable profiles
are prefixed with `sys-`:

	$ make
	$ make desc

To list only runnable profiles:

	$ make list/sys
	$ make desc/sys

Pick a desired profile from the list, say `sys-preload-hpps-busybox` which
has the emulator preload the TRCH SSW bare-metal application into TRCH on-chip
SRAM and binaries for the HPPS stack into HPPS DRAM, then boots TRCH into the
SSW bare-metal application, and lets TRCH boot HPPS into Busybox on Linux via
Arm Trusted Firware and U-boot bootloader.

In the following commands, instead of the symbolic string `PROFILE`, subsitute
the name of the selected, profile, like `sys-preload-hpps-busybox`. Storing the
profile name in an environment variable is generally not advantageous, because
after the first build of the profile, paths in the file system will exist, and
autocomplete on target strings will work. If you do use shell environment
variables, do not use `$PROF` since this name is reserved in the Makefile.

To build the profile incrementally, invoking nested builds:

	$ make prof/PROFILE

Deeply clean a profile (invokes clean on nested modules too):

	$ make prof/PROFILE/clean

Shallowly clean only the artifacts in `prof/PROFILE/bld/` (does not invoke
clean within the nested modules):

	$ make prof/PROFILE/bld/clean

## Switch between profiles

When working on multiple profiles, must be taken when building (and running)
then one after another.

After having built/run a profile X, before building/running a profile Y, you
must issue the shallow profile clean:

	$ make prof/PROFILE_X
	$ make prof/PROFILE_Y/bld/clean
	$ make prof/PROFILE_Y

The clean is necessary because the nested build artifacts built during the
build of X may be newer than the profile config files of profile Y that they
also depend on. If the target artifact is newer than its prerequisites, then
the artifact will not get rebuilt, so at the end of the build of profile Y,
some artifacts would still reflect the configuration of X. This is relevant
only when X and Y change the config of the artifact, but the clean step
should just be done in all cases, it doesn't cost anything.

## Invoke parts of the build explicitly

Invoke incremental nested build on a particular nested module (invokes only
strictly the nested build, does not rebuild artifacts in `prof/PROFILE/bld/`):

    $ make prof/PROFILE/bld/hpps/linux

Clean a module (invoke the nested build: only cleans artifacts within the
module's nested source tree, does not clean artifacts in `prof/PROFILE/bld/`):

    $ make prof/PROFILE/bld/hpps/linux/clean

Build a non-nested artifact individually -- any artifact in the
`prof/PROFILE/bld/` can be rebuilt this way, but not artifacts that are within
the source trees of the nested modules (e.g. inside `hpps/linux/`), since the
nested dependency tree is opaque to the top-level dependency tree:

	$ make prof/PROFILE/bld/trch/syscfg.bin

## Control the depth of the build

All builds are incremental, and will only rebuild artifacts that are missing
or out of date with respect to their dependencies. However, dependency
trees of the nested modules are not visible to the the top-level (this is not
feasible, nor sensible, since nested build systems might not even be based on
make!). Therefore, to incrementally build an artifact that depends on an
source or artifact a the nested module, the nested build must be invoked.

When the nested build system is designed well, it will do nothing or very
little when invoked on a completed build, however in practice some may
take a while to run, and may even rebuild artifacts for no reason. This is
still fast, though, and may be ignored, but to eliminate this wasted time,
the top-level build may be explicitly instructed to be shallow, i.e. not invoke
the nested build, at the risk of artifacts not being rebuilt when they
should and would have in a normal deep build.

To control the depth of the build, set `DEEP` (alias `D`) or `SHALLOW` (alias
`S`) variable to a pattern that matches names of nested module, where `%` is
the wildcard, and value `1` matches everything (equivalent to value `%`) and
`0` matches nothing.  For example, all of the following will prevent (at least)
the nested build in HPPS U-boot source tree from being invoked:

	$ make bld/PROFILE S=1
	$ make bld/PROFILE S=hpps-uboot
	$ make bld/PROFILE S=hpps-%

Only set a build to be shallow when you know that the artifacts produced by the
nested build in question did not change.

## Peudo out-of-tree build of nested modules

By default, a nested module is built in place, in the module's souce tree.
This is desirable, because it supports the edit, build, run development loop,
including unrestricted usage of the nested build system directly (without
the top-level), as needed for example for `make menuconfig` in Linux. Also,
this allows profiles (that do not change the compile-time configuration of the
module) to seemlessly share the build.

However, for some rare use cases, it is possible to build a module quasi out of
tree, without relying on out-of-tree build supprot from the module's build
system (rarely available). The top-level builder supports optional
"privatization" of the source tree of a nested module, by coping the nested
module's source tree (from its usual location) into the profile's private build
directory, cleaning it (because the copy will pickup build outputs, not
possible to exclude in a generic way), and building the module there.

To build a profile in privatized mode (privatizes the set of modules used by
the profile):

	$ make PRIV=1 prof/PROFILE

Making use of the out-of-tree build feature of modules to implement the
out-of-tree build option for the profile is not implemented, but would be nice.

Currently, privatization is only used for special profiles of type "tool",
which are used to produce artifacts that require invoking the emulator and
running the target software stack (e.g. to translate an ftrace dump).
Privatization may be useful in the testing context, to build multiple profiles
in the build step, and then run them in the run-test step (otherwise, the test
step will have to perform a build if more than one profile is to be tested).

Run a SSW stack profile on a target platform
=============================================

Currently supported target HPSC Chiplet platforms (conceptually, boards) are:
* `qemu`: Qemu, a software emulator (shipped in the HSPCC SDK)
* `zebu`: Synopsys FPGA-based emulator (to use it, you need to get the HPSC
software stack source release of the `zebu` branch, which contains an
expanded HPSC SDK with `sdk/zebu` module, and you need to build and run the SSW
stack on the specific Synopsys SCS server).

In the followin commands, replace the `PLATFORM` string with one of the
platforms in the above list.

To run a profile on a target platform:

	$ make prof/PROFILE/run/PLATFORM

You may also pass arguments to the launch script via `ARGS` variable. For
example, to launch Qemu in the GDB debugger, and wait for attachment:

	$ make prof/PROFILE/run/qemu ARGS="-S gdb"

Invoking the above run target also invokes:
* the incremental build of the profile -- so in edit-build-run
  development loop, after modifying source code, it is sufficient to
  invoke only this run target (with the exception of when switching between
  profiles, which requires a shallow clean step -- see an earlier section).
* a build of artifacts needed to run on the given platform (e.g. memory
  images in the platform-specific format, CLI arguments, etc); these
  artifacts can be cleaned and re-built explicitly via:

		$ make prof/PROFILE/bld/PLATFORM/clean
		$ make prof/PROFILE/bld/PLATFORM

Non-volatile state of the target machine (e.g. contents of non-volaitile
off-chip memories) will persist across runs, until you explicitly clean the run
state, either for a given platform:

	$ make prof/PROFILE/run/PLATFORM/clean

Or, for all platforms:

	$ make prof/PROFILE/run/clean

The configuration files related to running profiles on platforms are
defined by the `platform` profile (in `ssw/hpsc-utils/prof/platform/`).
The files there are consumed to produce profile-specific configuration
files in `prof/PROFILE/bld`.

All platforms are configured via a generic cross-platform memory map file
that describes which blobs are loaded into which memories at which addresses:

	$ cat prof/PROFILE/bld/preload.mem.map

Also, the platforms consume a configuration file with memory parameters,
that is merged from a cross-platform base configuration with platform-specific
overriding overlays on top:

	$ cat prof/PROFILE/bld/PLATFORM/mem.ini

Each platform consumes a configuration in this generic format and builds
memory images and other platform-specific configuration, like command line
arguments in `prof/PROFILE/bld/PLATFORM/`.

## Run a profile in Qemu

Build the and run the selected profile in Qemu, in one command:

    $ make prof/PROFILE/run/qemu

In a different shell (also will SDK environment loaded!) connect to the serial
console screen session printed when Qemu runs.

Use a separate shell for each serial port (and make sure that each shell
has the SDK environment loaded into it!), for HPPS:

    $ screen -r hpsc-0-hpps

Default names of the screen sessions for each serial port on the Chiplet are:

	* `hpsc-0-lsio0`: LSIO UART #0 (used by TRCH in the SSW Stack)
	* `hpsc-0-lsio1`: LSIO UART #1 (used by RTPS in the SSW stack)
	* `hpsc-0-hpps`: HPPS UART

To terminate the target, in the shell where Qemu was run via
`prof/PROFILE/run/qemu`, at the `(qemu)` monitor prompt (press enter if you do
not see the prompt):

    (qemu) quit

The platform-specific artifacts for Qemu in `prof/PROFILE/bld/qemu` are:

* `preload.mem.map.args`: command line arguments for loading data into memories,
  generated from a generic cross-platform specification in
  `bld/PROFILE/preload.mem.map`
* `*.mem.bin`: images for non-volatile memory (generated from same map
  specification), if not mentioned in the map, then a blank image is created.
* `env.sh`: parameters for `launch-qemu` script (specifies network ports, etc.)

## Run a profile in the Synopsis Zebu emulator

This will only work when you got the HPSC release, built it, and are running,
all on the specific Synopsys SCS server.

Build the and run the selected profile in Zebu, in one command:

    $ make prof/PROFILE/run/zebu

In a different shell (also with SDK environment loaded!), connect to the serial
console on HPPS UART:

    $ screen -r zebu-uart-hpps

At the `zRci` prompt, to pause the target execution:

	% run 1

When paused, to continue running for some cycles:

    % run 10000000

To exit:

    % quit

A stackdump on exit is commonly observed. If the process fails to exit,
then send it to background with `Ctrl-Z` and kill the job:

    $ kill %1

The platform-specific artifacts for Zebu in `prof/PROFILE/bld/zebu` are:

* `*.mem.bin` or `*.mem.vhex`: memory images for each memory, with contents
  specified in the generic cross-platform specification
  `bld/PROFILE/preload.mem.map`
* `preload.zebu.mem.map`: directives for loading images into memories for Zebu
   TCL scripts

Debugging
=========

The profile build places binaries in ELF format with debug symbols in
the profile build directory along with the packed images for booting:

	$ find prof/sys-preload-hpps-busybox/bld -name '*.dbg.elf'

To disassemble a built binary, invoke architecture-specific objdump tool
(shipped in HPSC SDK) on the binary in ELF format:

    $ aarch64-poky-linux-objdump -D path/to/elf_binary > binary.S

The images can be loaded into the multi-arch GDB (shipped in the HPSC SDK)
or presumably into any standard debugger with/without IDE, like ARM DS.

## Debugging code running in Qemu using GDB

The HPSC SDK and with SDK environment loaded into the shell, start `gdb` on one
of the ELF binaries corresponding to code that you know has been loaded into
target memory and is executable:

	$ gdb prof/PROFILE/bld/hpps/linux/linux.dbg.elf

### Attaching to Qemu with GDB

Depending on the version of Qemu, the instructions differ. The current
supported version is v2.x.

First, launch Qemu with an argument telling it to wait for a debugger
connection instead of resetting the machine immediately:

    $ make prof/PROFILE/run/qemu ARGS="-S"

Then spot the GDB port printed in the output (your port number will differ):

    GDB_PORT = 3032

#### Attaching to Qemu v2.x

Qemu v2.x supports attaching the debugger to only one of the processor clusters
in the machine, for a given build of Qemu. To attach to a different CPU
cluster, you need to rebuild Qemu, passing the desired cluster index to the
configure script. Furthermore, since profiles generate machine configurations
with different sets of clusters (e.g. HPPS A53x8 only, without RTPS R52, etc),
to debug different profiles, may require rebuilding Qemu. To rebuild Qemu
for a cluster at index `INDEX`:

    $ make sdk/qemu/clean/all
    $ make QEMU_GDB_TARGET_CLUSTER=INDEX sdk/qemu/all

To get the cluster index, count in the following list starting at 0 and
skipping any clusters that your profile does not enable:

    TRCH
    RTPS R52
    RTPS A53
    HPPS A53

For example, if your profile instantiates only TRCH and HPPS A53 cluster
and you want to debug code on the HPPS A53 cluster, then `INDEX=1`.

To connect to a running Qemu instance (replace GDB_PORT with the port number
printed when Qemu is launched):

	(gdb) target remote :GDB_PORT

The following warning may be printed -- it is safe to ignore it:

    warning: Selected architecture aarch64 is not compatible with reported
        target architecture arm
    warning: Architecture rejected target-supplied description

#### Attaching to Qemu v4.x and higher

To connect to a running Qemu instance (replace GDB_PORT with the port number
printed when Qemu is launched):

	(gdb) target extended :GDB_PORT

Each clusters in the Chiplet is presented in GDB as a proceses (see GDB's
multi-process functionality), and each CPU in that cluster maps to a thread in
that process. To instantiate each cluster:

	(gdb) add-inferior # TRCH cluster
	(gdb) add-inferior # RTPS R52 cluster
	(gdb) add-inferior # RTPS A53 cluster
	(gdb) add-inferior # HPPS A53 cluster

To attach one of the above clusters, by index, e.g. for HPPS:

	(gdb) inferior 3
	(gdb) attach 3
	(gdb) info threads

### Debugging code on the target processor with GDB

Keep in mind that after attaching, the processor is still halted, so will still
be at the ATF entry point even though u-boot binary or Linux kernel binary are
loaded into the GDB debugger.

It is possible to load multiple binaries into GDB at once, but for binaries
that relocate themselves (e.g. U-boot), you need to get the relocation offset
(need to compile U-boot with debug output enabled -- TODO: provide
instructions).

To execute until entry into u-boot, set a breakpoint at the u-boot entry point:

    (gdb) break *0x80020000

To execute until entry into kernel, set a breakpoint at the kernel entry point:

    (gdb) break *0x80480000

To tell GDB to automatically display the current program counter after every step:

    (gdb) display/i $pc

To see register values:

    (gdb) info reg

To step to the next instruction:

    (gdb) stepi

When GDB attaches, the target execution is halted, to continue execution:

    (gdb) cont

To set a breakppoint (tab completion on the function name should work):

    (gdb) break c_function_name

To set a breakpoint at an address:

    (gdb) break *0x80000000

To set a breakpoint at line 123 in file `file.c`:

    (gdb) break file.c:123

To continue after a breakpoint:

    (gdb) cont

To end debugging session, detach from gdb with:

    (gdb) detach

