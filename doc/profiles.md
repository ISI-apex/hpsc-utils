Configuration Profiles
======================

Overview
--------

HPSC SSW stack ships with a system for building the stack in different
configuration variants, called *profiles*. A profile may control many
aspects of the software configuration (both compile-time and run-time) and
hardware configuration (the latter in case of flexible Qemu machine model):
* which software binaries are loaded to which addresses into offchip and
  onchip memories,
* Kconfig options in Linux, U-boot, Busybox,
* device trees,
* bootloader settings, e.g. kernel command line arguments,
* configuration files of custom software components, e.g. bare-metal
  applications, that control which Chiplet subsystems are booted,
* makefile variable values,
* contents of file system images, e.g. initramfs,
* hardware settings in the Qemu emulator machine model,
* etc. (anything a developer might configure manually should
  be possible to encapsulate in a profile)

For instructions on how to use profiles see [README.md](README.md), for
instructions on how to create profiles, read on.

Each profile is a collection of configuration files that are overlayed on top
of a base configuration to produce a set of merged configuration files that are
then used during the build of the artifacts for the given profile. Each
configuration file in a profile usually contains a configuration fragment that
is relevant to the profile. For example, a profile that configures the MTD
subsystem in Linux to provide access to off-chip memory might want to enable
the `nanddump` utility in Busybox; to do so, the profile would include a
configuration file overlay `busybox.miniconf` for the Busybox Kconfig with
the following fragment:

    CONFIG_NANDDUMP=y

For a given configuration file, when the overlays with fragments are merged
with the base, a complete configuration file is produced. The base of each
configuration file is usually chosen to be the most minimal configuration; or
in some cases, base is the "default" configuration (if a default is defined).

A profile may be a composite of other profiles, referred to as or `library
profiles` and named with the `lib-` prefix. This minimizes duplication of
configuration fragments which are used in more than one profile. For example,
many different profiles (but not all) might want to configure to boot the HPPS
subsystem, so the configuration fragments necessary to boot HPPS (e.g. add HPPS
to the boot list in TRCH bare-metal app configuration, add HPPS to offchip
memory and/or to DRAM memory, etc) should be encapsulated in an overlay and the
overlay should be included from each profile that needs it. Profiles that are
top-level are named with `sys-` profile; even though such profiles are not
usually included into others, they may be when the goal is to create a very
similar variant of the top-level profile.

The profile system itself is implemented within the main makefile
[make/Makefile.ssw](make/Makefile.ssw) in form of recipes for each artifact
needed to build and run the target software. The only way to build the target
SSW stack is to build it in the context of some profile.

To create a new profile, follow the section below, but also consult existing
examples. It is fine to copy an existing profile and then modify it, but please
avoid duplication of code by creating and including library profiles, as
described above.

Profile source structure
------------------------

Each profile is implemented in a subdirectory in `ssw/hpsc-utils/prof/` by a
Makefile and the set of files that are the configuration overlays. The Makefile
defines all overlays that are to be applied to each target configuration file
that the profile wants to modify.

A profile's Makefile starts with a comment that describes the profile. The
comment maybe take multiple lines, as long as each line starts with `#`. After
the comment, there must be one blank line. The top-level target for listing the
profile descriptions (`make ssw/desc`) outputs this comment. The desired
convention for profiles that include other non-library `sys-` profiles is to
say "Like `sys-foo` but with X enabled`, instead of repeating the description
of `sys-foo`.

### Includes

If the profile includes other "library" profiles, these includes must come
first, and are wrapped in the following structure:

      $(call push-prof)

      include $(CONF)/lib-prof-A/Makefile
      include $(CONF)/lib-prof-B/Makefile
      # ... add as many as you need, overlays will be applied in this order

      PROF_CONF:=$(CONF)/$(call pop-prof)

The push and pop is the way chosen to avoid needing to have the profile
name defined inside the Makefile. The latter alternative is simpler, but is
more fragile in the face of refactoring.

### Overlay rules

The profile's Makefile defines which overlays to apply in the form of rules,
where the target is the configuration file artifact (known to the main makefile
`Makefile.ssw`) and the dependencies are the overlays (usually supplied by in
the profile's subdirectory). In an earlier example with the profile
that enables the MTD subsystem, the Makefile would contain this rule:

    $(PROF_BLD)/hpps/busybox.miniconf: $(PROF_CONF)/hpps/busybox.miniconf

Certain automatic variables are available within the profile's makefile:
* `PROF_CONF` points to the profile's source directory:
  `ssw/hpsc-utils/prof/PROFILE/`
* `PROF_BLD` points to profile's build directory where profile's artifacts
   are generated: `ssw/prof/PROFILE/`

The convention is to keep the name of the source file with the configuration
fragment the same as the name of the artifact into which it is merged.

Note that these rules do not include a recipe (with the exception of custom
per-profile artifacts, see below). The recipe for the artifact is defined in
the main makefile. Usually, this recipe would define the command that merges
the dependencies (the overlays) to produce the artifact. See section on merging
for more details.

#### Variables

The rule may also define a Makefile variable, for example, to pass a macro to
the preprocessor when building the Linux device tree (in our build recipes, the
device tree source is pre-processed by GCC's preprocessor before compilation by
`dtc`):

    $(PROF_BLD)/hpps/linux.cpp.dts: private CFLAGS+=-DCONFIG_SMC_NAND=1

The `private` modifier keeps the scope to the given artifact, i.e. does not
include the artifacts that depend on the given artifact.

The variable being set is ususually either used in the recipe of the artifact
(like in the example above), or in a Makefile of a nested source tree.

#### Directory trees

Some target artifacts are made from directory trees, e.g. initramfs is
the early filesystem whose contents is a compressed CPIO archive created
from a directory. Profiles may be add or modify the content of such
directory trees, by creating a directory tree in the profile's source
directory e.g. `hpps/initramfs.dir` and a corresponding rule:

    $(PROF_BLD)/hpps/initramfs.fs: $(PROF_CONF)/hpps/initramfs.dir

The result is that the contents of `hpps/initramfs.dir` will be copied
over the initramfs directory that is being packed into the CPIO archive.

Note that here the naming convention differs `.fs` vs `.dir`: this is for
technical reasons relating to `fakeroot` that don't merit attention here.

#### Custom artifacts

A profile may also define entirely new artifacts, as long as it defines
a recipe for how to produce the artifact. For example,

    $(PROF_BLD)/hpps/blob.bin: $(PROF_CONF)/blob.src
        mkblob -o $@ $<

Sucn an artifact may then be referenced from other config files in
the makefile, e.g. from a `preload.mem.map` file to add it to off-chip
memory:

    lsio.smc.sram.0 theblob 0x00100 $PROF_BLD/blob.bin

Creating a custom artifact might be appropriate if it really is relevant to
only one profile (usually, a library profile). However, the convention so
far has been to define almost all artifact recipes in the main makefile,
so that all build recipes are kept together.

Custom artifacts are often useful in library profiles for creating temporary
artifacts that are parametrized by each parent profile that includes the
library profile. For example, the `lib-hpps-linux-tests` profile defines a
recipe that assembles a directory with a chosen set of test binaries, but the
list of the binaries is provided by each parent profile that includes
`lib-hpps-linux-tests`. The library profile than adds this temporary directory
artifact to the `initramfs.fs` artifact as a depedency (in a standard rule
without a recipe).

#### Dependency tracking

Since overlays are specified as dependencies, make tracks the dependency
tree for us, enabling the builds to be incremental. The main profile
system implementation in the main Makefile goes beyong, and scans
certain types of configuration files for dependencies, e.g. it will
add file paths found in a memory map file (`*.mem.map`) as dependencies
of the memory image. Also, files in directory overlays are also automatically
added as dependencies. However, if you modify the profile Makefile itself,
then you have to (shallow-)clean the profile.

### Merging of overlays

Overlays listed as dependencies of artifacts in a profile's Makefile
are merged by the command in the recipe defined in the main Makefile.
The merge command is specific to each file type:
* `*.sh`: shell scripts are concatenated (statements may override variables,
  as they execute at runtime)

* `*.paths`: path lists are concatenated

* `*.config.mk`: custom Makefile configs are merged (statements that override,
  append, modify priously defined variables will naturally take effect when
  interpreted by Make)

* `*.config` and `*.miniconf`: Kconfig human-readable config files (aka.
   miniconfigs or defconfigs, not to be confused with autogenerated `.config`)
   are concatenated, but the merge with base involves feeding the concatenated
   result thorugh `kconfig/merge_config.sh` (sidenote: this script is not
   smart enough to enable dependencies, so you have to ensure your fragments
   are self-sufficient)

* `*.dts`: device trees are concatenated, see `dtc` documentation for
  the semantics of modifying nodes and node properties; in summary, if
  you add a node with the same name as an existing node with a property,
  then that property will be added to the original node; there is also
  support for removing nodes with special syntax.

* `*.ini`: INI files are merged with the `merge-ini` tool in HPSC SDK such that
fields defined in later overlays override, append, or remove earlier fields, by
means of `=`, `+=`, `-=` operators. For example, the following two overlays
applied in sequence produce the result shown below:

   `lib-prof1/config.ini`:

        [sectionA]
        fieldX = 0
        fieldY = abc def ghi
        fieldZ = xyz

   `lib-prof2/config.ini`:

        [sectionA]
        fieldX = 1
        fieldY -= def
        fieldZ += uvw

   `prof/PROFILE/config.ini`:

        [sectionB]
        fieldX = 1
        fieldY = abc ghi
        fieldZ = xyz uvw

* `*.env`: environment key-value dictionaries are merged by the `merge-env`
script from the HSPC SDK that supports the override (`=`), append (`+=`),
remove (`-=`) operators.

* `*.mem.map`: memory maps define contents of memories in a simple custom
syntax and are merged by `merge-map` tool in the HPSC SDK: there is support for
adding files, overriding the address or the data file path for existing files.

* `*.fs`: file-system directories are merged by copying directory trees on
top of each other

## Target artifacts

Target artifacts fall into two categories:
1. Artifacts produced from sources private to a profile
2. Artifacts produces from nested source trees shared among profiles

All artifacts for a profile are generated in `ssw/prof/PROFILE/`. Artifacts
that participate in running the SSW on the target (e.g. are included in a
memory image) are generated in the `bld/` subdirectory.  Artifacts are further
roughly organized in subdirectories by subsystem. Artifacts that are modifiable
at runtime (e.g. offchip memory images) and whose content should persist across
the profile runs, live in the `run/` subdirectory. When debugging profiles,
it is useful to look at and individually rebuild intermediate artifacts in
the build directory. Any artifact can be built by the make target with the path
to the artifact, e.g. `make ssw/prof/PROFILE/bld/hpps/linux.dts` (to force a
re-build, first delete the artifact).

Artifacts produced from a nested source tree are copied from that
nested source tree into a subdirectory dedicated to that nested module, e.g.
`ssw/prof/PROFILE/hpps/linux/`; if you create new artifacts in a profile, do
not place such artifacts in these dedicated directories, e.g. even if the
artifact is related to Linux, it should go into `hpps/` not into `hpps/linux/`.

Nested source trees are built in-place, so a given build in a nested source
tree is for the last built profile. When another profile is built, the an
incremental re-build will happen in the nested source trees whose configuration
has been changed by the new profile. It is desirable to share nested source
trees because the common use case is to modify source (e.g. Linux kernel
source) and test that these modifications work in several profiles. However,
sharing of the build directories is a different question and is not
particularly desirable; so, it would make sense to build the nested modules
that support out-of-tree builds in each profile directory (this is not
implemented, though; and very few of the nested modules support OOT builds).
Useful for certain special cases, the profile system supports fake OOT builds
by brute-force copying of the source directories -- see [README.md](README.md)
for more information.

## Shared artifacts

Some artifacts are very time-consuming to build (e.g. root file system
image of the Yocto distribution takes hours to build). Yet, multiple
profiles may want to use the artifact. For example, one profile may want to
bood Yocto from NAND and another may want to boot Yocto from NOR --
the memory images are different, but the Yocto image archive used to
produce both memory images is the same.

To support this situation, a profile may add support for sharing some
of its artifacts, as follows:

   ifneq ($(call share,$(THIS_PROF),$(SHARE)),)

   $(PROF_BLD)/hpps/prof.yocto.rootfs.tar.gz: \
	   $(call share-art,$(THIS_PROF),hpps/yocto/yocto.rootfs.tar.gz)

   else # not share (build your own)

   PROF_ARTS += $(PROF_BLD)/hpps/yocto/yocto.rootfs.tar.gz

   $(PROF_BLD)/hpps/prof.yocto.rootfs.tar.gz: \
	   $(PROF_BLD)/hpps/yocto/yocto.rootfs.tar.gz

   endif

Then, a profile that wants to use the shared artifacts adds the owner profile
name to the variable `SHARE`, e.g. in `lib-hpps-yocto-initramfs/Makefile`:

      SHARE += lib-hpps-yocto

Before a profile that consumes a shared artifact can be built, the
profile that provides the shared artifact must be built, e.g.:

     $ make ssw/prof/lib-hpps-yocto

If a profile wants to modify an expensive artifact (e.g. add a package
to Yocto image), then it cannot use the shared artifact; with sharing
disabled, the profile in question will have its own build of the artifact.

Currently, there is no support for sharing parts of the build of
artifacts (e.g. different profiles define different Yocto configuration
files, but share a Yocto build directory, but each profile gets a different
final packaged Yocto image) -- this may or may not be feasible, but is
certainly not easy to implement.

## Tool profiles

The profiles named `tool-*` are special profiles that act as tools, i.e. that
can consume input and produce output. An example, is a profile that decodes a
binary trace buffer into text. These profiles cover the cases where a standalone
tool is not available (e.g. decoding a trace buffer requires running the
specific Linux kernel build)

 The I/O is done via buffers in DRAM that are filled and dumped via Qemu QMP
control port.

Common patterns
----------------

### Configure Linux kernel

First, you need to construct a valid configuration fragment, accounting
for dependencies between config options. The Kconfig `menuconfig` GUI
accounts for dependencies, so use it like so:

1. Clean and re-build the profile that you are starting with (that does
not have the config options you are looking to add). This step ensures
that the `.config` in your working copy is the unmodified config as was
generated by the profile. Look through the build log, to get the right
variable values to pass to make (as of now, they are as below):

       cd ssw/hpps/linux
       export ARCH=arm64 CROSS_COMPILE=aarch64-none-linux-gnu- 

2. Generate the human-readable miniconfig from the machine-readable `.config`:

        make hpsc_defconfig
        mv defconfig linux.config.without-mtd

3. Open menuconfig GUI and select your option(s), close and save:

        make menuconfig

4. Generate the human-readable miniconfig from the (modified) machine-readable
`.config`:

        make hpsc_defconfig
        mv defconfig linux.config.with-mtd

5. Find the options that were enabled, this is the configuration fragment:

       diff linux.config.without-mtd linux.config.with-mtd

6. Place your config fragment in a file `hpps/linux.config` in the profile's
source directory, e.g.:

    CONFIG_MTD=y

7. Add the rule to your profile's Makefile:

    $(PROF_BLD)/hpps/linux.config: $(PROF_CONF)/hpps/linux.config

You can also add/remove nodes and override/add properties in the Linux device
tree. Create the fragment in `hpps/linux.dts` in profile source directory.
For example, to override a property to existing node named node, refer to the
node by its label (not its name) in your fragment:

    &smc_sram {
        status = "okay";
    };

Then, add the rule to the profile's Makefile:

    $(PROF_BLD)/hpps/linux.dts: $(PROF_CONF)/hpps/linux.dts

### Configure U-boot

The process for setting U-boot Kconfig options and modifying device tree nodes
is analogous to that for Linux kernel. The analogous artifacts for U-boot are:
* `$(PROF_BLD)/hpps/u-boot.config`: U-boot Kconfig
* `$(PROF_BLD)/hpps/u-boot.dts`: U-boot device tree

U-boot also has an environment file that you can set variables in, so you can
set, e.g. kernel boot arguments in `hpps/u-boot.env` in your profile source
directory:

    bootargs=loglevel=8

Then add the rule in your profile's Makefile:

    $(PROF_BLD)/hpps/u-boot.env: $(PROF_CONF)/hpps/u-boot.env

### Configure Busybox

Busybox is the early userspace system used in many profiles. It is an
alternative to a full Linux distribution like Yocto. Busybox can include
a variety of utilities, controlled by a Kconfig-based configuration file.
The base Busybox config is minimal, and each profile adds whatever
tools are relevant to that profile.

To create a configuration fragment, it is necessary to ensure that dependencies
between configuration options are respected. The Kconfig `menuconfig` GUI
tracks dependencies, so leverage it in this way:

1. Clean and re-build the profile that you are starting with (that does
not have the config options you are looking to add). This step ensures
that the `.config` in your working copy is the unmodified config as was
generated by the profile. Look through the build log, to get the right
variable values to pass to make (as of now, they are as below):

       cd ssw/hpps/busybox
       export CROSS_COMPILE=aarch64-none-linux-gnu- 

2. Generate the human-readable miniconfig from the machine-readable `.config`
(takes up to a few minutes):

        mv .config profile.config
        sed -i '4d' profile.config
        miniconfig.sh profile.config
        mv mini.config busybox.miniconf.without-xyz

3. Open menuconfig GUI and select your option(s), close and save:

        make menuconfig

4. Generate the human-readable miniconfig from the (modified) machine-readable
`.config` (takes up to a few minutes):

        mv .config profile.config
        sed -i '4d' profile.config
        miniconfig.sh profile.config
        mv mini.config busybox.miniconf.with-xyz

5. Find the options that were enabled, this is the configuration fragment:

       diff busybox.miniconf.without-xyz busybox.miniconf.with-xyz

6. Place your config fragment in a file `hpps/busybox.miniconf` in the
profile's source directory, e.g.:

    CONFIG_NANDDUMP=y

7. Create the rule in your profile's Makefile:

    $(PROF_BLD)/hpps/busybox.miniconf: $(PROF_CONF)/hpps/busybox.miniconf

### Enable a hardware device

In the base configuration, only the bare minimum of devices are enabled.  To
enable a device, it is usually necessary to modify at least the Qemu device
tree and the Linux device tree (but usually more, e.g. Linux driver in
Kconfig, etc).

Before making a new profile, check that wheter a library profile for enabling
the device in question already exists. If a profile exists that enables more
than you need, then please factor that profile as needed.

The current convention for the device trees are preprocessor conditionals
around device nodes, so the profile needs to set the respective macros. This is
done by a rule that sets variables (see Variables section above). For example,
to enable the SMC-353 controller for NAND memory, you would add these rules to
your profile.

    $(PROF_BLD)/qemu/hpsc.cpp.dts: private CFLAGS+=-DCONFIG_HPPS_SMC_NAND=1
    $(PROF_BLD)/hpps/linux.cpp.dts: private CFLAGS+=-DCONFIG_SMC_NAND=1

### Add a binary to initramfs

Some Linux profiles boot Linux into the early userspace, aka. initramfs, (as
opposed to instructing the kernel to mount a root file system on some off-chip
memory device and boot directly into it). The contents of the early userspace
filesystem is packed from a directory on the host system as part of profile
build recipe. Usually, at least Busybox is installed into the directory, but
other files may be added as follows.

Create a directory `hpps/initramfs.dir/` in the profile source directory and
add your files to it. Then, add the rule to your profile's makefile:

    $(PROF_BLD)/hpps/initramfs.fs: $(PROF_CONF)/hpps/initramfs.dir

When using profiles that include `lib-hpps-busybox`, which defines an init
script that runs upon boot, it is possible to add custom scripts to also be run
on boot. Create the script file in `etc/init.d` whithin the directory you
created above (`hpps/initramfs.dir/`). The naming convention for the scripts is
`00-some-action`, where the digits are used to control the order of invocation.

You can also add artifacts built as part of the profile build to the initramfs.
First the artifact in question needs to built (usually by a recipe in main
makefile, or by a recipe in the profile); let's assume that that recipe
eventually places the artifact somewhere in the profile build build directory,
e.g. `$(PROF_BLD)/hpps/sometool`. Then, in the profile, add the rule to put the
artifact first into a staging directory, and then add that directory
to the overlay directory:

    $(PROF_BLD)/hpps/initramfs.stage.dir: $(PROF_BLD)/hpps/sometool
        cp $< $@/usr/bin/

    $(PROF_BLD)/hpps/initramfs.fs: $(PROF_BLD)/hpps/initramfs.stage.dir

See `lib-hpps-linux-tests` for an example of this (it also shows how
`fakeroot` can be used so that files are owned by root).

### Add a blob to off-chip memory

The contents of all memories (on-chip and off-chip, SRAM and DRAM, volatile and
non-volatile) can be pre-loaded before the target is reset. The mechanism of
pre-loading differs by memory and by platform (e.g. Qemu vs ZeBu vs HAPS),
but the specification of what should be pre-loaded into each memory is specified
in one platform-independent memory map file: `preload.mem.map`.

The format of `preload.mem.map` is illustrated in the following example:

      # MEM ID	       BLOB ID  ADDR         FILE
      hpps.dram	       hpps-fw  0x0000_0000  $PROF_BLD/hpps/atf/atf.bin
      hpps.dram	       hpps-bl  0x0002_0000  $PROF_BLD/hpps/u-boot/u-boot-nodtb.bin
      lsio.smc.sram.0  boot-sfs *            $PROF_BLD/trch/boot.sfs.mem.bin

Star `*` is an overlay directive that instructs the merge tool to keep the 
field unchanged, while overriding the other fields. The merge tool matches
lines by memory ID.

The memory IDs are the platform-independent IDs from
`sdk/hpsc-sdk-tools/conf/mem.ini`, which defines the memory types and is
overlayed with platform-specific (`PLATFORM/mem.ini`) and profile-specific
overlays. Profiles may overlay `mem.ini` as well as its platform-specific
overlays `PLATFORM/mem.ini` in order to change what off-chip memory is hooked
up to the Chiplet, or to tweak the size of memory.

This memory map file is consumed by platform-specific recipes defined in the
the special `platform` profile (`ssw/hpsc-utils/prof/platform/Makefile`).
The recipe invokes a platform-specific `PLATFORM-preload-mem` script that
produces an image and/or configuration for the platform, depending on
the platform and the memory type. For example, for Qemu, images files for
DRAM memory are never created, instead command line arguments for Qemu are
generated to load each individual blob.

The main makefile (`ssw/Makefile`) has recipes for generating images in various
formats suitable for different types of memories, e.g. NAND. As far as the
`preload.mem.map` is concerned, everything is just a binary blob. It is the
responsibility of the profile writer to add blobs in appropriate formats to the
respective memories.

A profile may add define a `preload.mem.map` configuration fragment in
its source directory, and add the rule to its Makefile:

    $(PROF_BLD)/preload.mem.map: $(PROF_CONF)/preload.mem.map

Note that the profiles `lib-trch-bm-{preload,nvmem}-boot` introduce an
additional layer of logic on top of the `preload.mem.map` file. The profiles
that include these profiles add their memory map fragments to a different
intermediate file (e.g. `preload-boot.preload.mem.map`), and these
`lib-trch-bm-*-boot` profiles then conditionally merge these intermediates into
`preload.mem.map`. This allows a parent profile to apply to different modes
defined by the included profile.
