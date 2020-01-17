# Second-level base config to load RTPS (through boot loader)

$(call push-prof)

include $(CONF)/lib-rtps-r52/Makefile

PROF_CONF:=$(CONF)/$(call pop-prof)

PROF_ARTS += $(PROF_BLD)/rtps/r52/u-boot/u-boot.dbg.elf

$(PROF_BLD)/trch/syscfg.ini: $(PROF_CONF)/trch/syscfg.ini

$(PROF_BLD)/trch/boot.sfs.mem.map: $(PROF_CONF)/trch/boot.sfs.mem.map
$(PROF_BLD)/preload-boot.preload.mem.map: $(PROF_CONF)/preload-boot.preload.mem.map

$(PROF_BLD)/rtps/r52/u-boot.config: $(PROF_CONF)/rtps/r52/u-boot.config
$(PROF_BLD)/qemu/env.sh: $(PROF_CONF)/qemu/env.sh

