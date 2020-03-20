# Configuration for running on target platforms common across all profiles.
# Include this profile only from profiles that can be run (on *a* platform).
#
# There are two levels of abstraction regarding preloading content into memory.
#   1. The higher abstraction level of a memory map file which declares a list
#	   of files and their destination (memory, address)
#   2. The lower abstraction level of a memory image file. The format may be
#      a byte array one-to-one with physical memory or a sparse format where
#	   spans of bytes are given.
#
# Some platforms for some memories are able to consume the higher level memory
# map file directly, while others need an image file. For all latter cases, we
# build an image file as a build artifact, as opposed to dynamically generating
# it in the launch-(platform) script upon each run.

$(call push-prof)
# includes
PROF_CONF:=$(CONF)/$(call pop-prof)

PLATFORMS = qemu zebu

# Common across all platform platforms

# Merge-base for cross-platform memory map file describing what content to load
# into which memories. Platform-specific configuration files (of various types)
# are generated from this generic config file.
$(PROF_BLD)/preload.mem.map: | $(PROF_BLD)/
PROF_ARTS += $(PROF_BLD)/preload.mem.map

# Common config across platform launch scripts
$(PROF_BLD)/env.sh : | $(PROF_BLD)/

# Merge bases for env (from this profile) and memory config files (from SDK)
# Note: if you add an env.sh override for a platform X, add the relation rule
# 	$(PROF_BLD)/X/env.sh: $(PROF_CONF)/X/env.sh
# to the platform-specific section of this file.
define plat-rule
$(PROF_BLD)/$(1)/env.sh: $(PROF_BLD)/env.sh | $(PROF_BLD)/$(1)/
$(PROF_BLD)/$(1)/mem.ini: $(HPSC_SDK_CONF)/mem.ini \
			  $(PROF_BLD)/mem.ini \
			  $(HPSC_SDK_CONF)/$(1)/mem.ini \
			  | $(PROF_BLD)/$(1)/
$(PROF_BLD)/$(1): $(PROF_BLD)
$(PROF_RUN)/$(1): $(PROF_BLD)/$(1) | $(PROF_RUN)/$(1)/
endef
$(foreach p,$(PLATFORMS),$(eval $(call plat-rule,$(p))))

$(PROF_BLD)/mem.ini: $(PROF_CONF)/mem.ini

# These describe how to make images of different types, rules available to any
# platform, but each platform needs to define a list of which images it wants
# to create (done through the ARTS_* vars below).
#
# NOTE: The naming convention of the output images must match across these
# rules and the *-preload-mem processors of memory map file (the memory map
# file is cross platform and cannot say which images should be created (nor
# what their names should be). The convention is memory_id.suffix.image_format,
# where memory_id is from memory map (and mem.ini), suffix is passed as cli
# argument to *-preload-mem above, and image_format is a property from mem.ini.

# Dependency of images to mem.ini is added below, for each platform
$(PROF_BLD)/%.mem.bin \
$(PROF_BLD)/%.mem.vhex \
: $(PROF_BLD)/preload.exp.mem.map
	mkmemimg -m $(notdir $*) -o $@ -c $(@D)/mem.ini $<

# The source image prereq is generated in the .dep file
# Dependency of images to mem.ini is added below, for each platform
$(PROF_BLD)/%.slice.mem.bin:
	mkmemslice -m $(notdir $*) -o $@ -c $(@D)/mem.ini $<

# Rules for running, generic across platforms

PLAT_BLD_TARGETS := $(patsubst %,$(PROF_BLD)/%,$(PLATFORMS))
PLAT_RUN_TARGETS := $(patsubst %,$(PROF_RUN)/%,$(PLATFORMS))
PLAT_CLEAN_TARGETS := \
	$(patsubst %,$(PROF_RUN)/%/clean,$(PLATFORMS)) \
	$(patsubst %,$(PROF_BLD)/%/clean,$(PLATFORMS)) \

.PHONY: $(PLAT_RUN_TARGETS) $(PLAT_CLEAN_TARGETS)
$(PLAT_RUN_TARGETS) $(PLAT_RUN_TARGETS): $(PROF_BLD)

KEEP_DIRS += $(PLAT_BLD_TARGETS) $(PLAT_RUN_TARGETS)

$(PLAT_RUN_TARGETS): $(PROF_HOME)
	cd $(PROF_RUN)/$(@F) && launch-$(@F) $(PROF_RUN_ARGS) $(ARGS)
$(PLAT_CLEAN_TARGETS):
	[ ! -d "$(@D)" ] || find "$(@D)" -mindepth 1 -delete

# Qemu rules

# The Qemu DT is another platform-specific config file (overridable by profiles)
$(PROF_BLD)/qemu/hpsc.dts: $(QEMU_DT)/hpsc-arch.dts | $(PROF_BLD)/qemu/
$(PROF_BLD)/qemu/hpsc.cpp.dts: private CFLAGS+=-I$(QEMU_DT)
ARTS_qemu += $(PROF_BLD)/qemu/hpsc.dtb

$(PROF_BLD)/qemu/mem.ini: $(PROF_CONF)/qemu/mem.ini

# Qemu rules for building and preloading images from cross-platform memory map

$(PROF_BLD)/qemu/preload.mem.args: $(PROF_BLD)/preload.exp.mem.map $(PROF_BLD)/qemu/mem.ini
	qemu-preload-mem --root $(abspath .) -c $(PROF_BLD)/qemu/mem.ini \
		--rules $@.dep --artifacts ARTS_qemu --prereqs PROF_ARTS --suffix '.mem' \
		--image-dir $(@D) --run-dir $(PROF_RUN)/qemu -o $@ $<

$(PROF_BLD)/qemu/preload.mem.args.dep: $(PROF_BLD)/qemu/preload.mem.args ;
include $(PROF_BLD)/qemu/preload.mem.args.dep
$(ARTS_qemu): $(PROF_BLD)/qemu/mem.ini $(PROF_BLD)/qemu/env.sh
$(PROF_BLD)/qemu: $(ARTS_qemu)

# For privatizing image files subject to overwriting during run into run directory
$(PROF_RUN)/qemu/%.bin: $(PROF_BLD)/qemu/%.bin | $(PROF_RUN)/qemu/
	cp $< $@

QEMU_ARGS=\
	-d $(abspath $(PROF_BLD)/qemu/hpsc.dtb) \
	-e $(abspath $(PROF_BLD)/qemu/env.sh) \
	-a $(abspath $(PROF_BLD)/qemu/preload.mem.args) \

$(PROF_RUN)/qemu: $(PROF_BLD)/qemu/preload.mem.args
$(PROF_RUN)/qemu: PROF_RUN_ARGS+=$(QEMU_ARGS)

# Zebu rules for building and preloading images from cross-platform memory map

$(PROF_BLD)/zebu/preload.zebu.map: $(PROF_BLD)/preload.exp.mem.map \
				   $(PROF_BLD)/zebu/mem.ini
	zebu-preload-mem --root $(abspath .) -c $(PROF_BLD)/zebu/mem.ini \
		--rules $@.dep --artifacts ARTS_zebu --suffix '.mem' \
		--image-dir $(@D) --extension-bin 'raw' -o $@ $<

$(PROF_BLD)/zebu/preload.zebu.map.dep: $(PROF_BLD)/zebu/preload.zebu.map ;
include $(PROF_BLD)/zebu/preload.zebu.map.dep
$(ARTS_zebu): $(PROF_BLD)/zebu/mem.ini

# Zebu is particular about extensions
$(PROF_BLD)/zebu: $(patsubst %.bin,%.bin.raw,$(ARTS_zebu))
$(PROF_BLD)/zebu/%.bin.raw: $(PROF_BLD)/zebu/%.bin
	$(COPY) $< $@

ZEBU_ARGS=-m $(abspath $(PROF_BLD)/zebu/preload.zebu.map)
$(PROF_RUN)/zebu: $(PROF_BLD)/zebu/preload.zebu.map
$(PROF_RUN)/zebu: PROF_RUN_ARGS+=$(ZEBU_ARGS)

# Text-based hex format (optionally) used by Zebu
$(PROF_BLD)/%.vhex: $(PROF_BLD)/%.bin
	hpsc-objcopy -I binary -O Verilog-H $< $@

# Rules to generate striped images for Zebu

$(PROF_BLD)/%.hpps.x.mem.bin: ADDR_VAR=HPPS_DRAM_ADDR
$(PROF_BLD)/%.hpps.x.mem.bin: BANKS_VAR=HPPS_DRAM_BANKS

$(PROF_BLD)/%.x.mem.bin: $(PROF_BLD)/%.mem.bin $(PROF_BLD)/%.conf.sh
	source $*.conf.sh && \
	memstripe --base $$$(ADDR_VAR) -i $< \
		$$(for i in $$(seq $$$(BANKS_VAR)); do echo $*.ddr.$$i.bin; done)
	touch $@
