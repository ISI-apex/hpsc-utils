# Booting Linux on HPPS (default is non-SMP -- single core)

$(call push-prof)

include $(CONF)/lib-hpps-a53/Makefile
include $(CONF)/lib-trch-bm-hpps/Makefile

PROF_CONF:=$(CONF)/$(call pop-prof)

# Artifacts not pulled in automatically since not part of any image
PROF_ARTS += \
	$(PROF_BLD)/hpps/conf.sh \
	$(PROF_BLD)/hpps/atf/atf.dbg.elf \
	$(PROF_BLD)/hpps/u-boot/u-boot.dbg.elf \
	$(PROF_BLD)/hpps/linux/linux.dbg.elf \

$(PROF_BLD)/trch/syscfg.ini: $(PROF_CONF)/trch/syscfg.ini
$(PROF_BLD)/trch/boot.sfs.mem.map: $(PROF_CONF)/trch/boot.sfs.mem.map

$(PROF_BLD)/hpps/conf.sh: $(PROF_CONF)/hpps/conf.sh
$(PROF_BLD)/hpps/u-boot.config: $(PROF_CONF)/hpps/u-boot.config
$(PROF_BLD)/hpps/u-boot.env: $(PROF_CONF)/hpps/u-boot.env
$(PROF_BLD)/hpps/u-boot.dts: $$(S_hpps-uboot)/arch/arm/dts/hpsc-hpps.dts
$(PROF_BLD)/hpps/linux.dts: $$(S_hpps-linux)/arch/arm64/boot/dts/hpsc/hpsc.dts

$(PROF_BLD)/qemu/env.sh: $(PROF_CONF)/qemu/env.sh
$(PROF_BLD)/preload-boot.preload.mem.map: $(PROF_CONF)/preload-boot.preload.mem.map

# Default is non SMP, so disable the PSCI mailbox to TRCH
$(PROF_BLD)/hpps/atf.config.mk: $(PROF_CONF)/hpps/atf.config.mk
$(PROF_BLD)/trch/bm.config.mk: $(PROF_CONF)/trch/bm.config.mk
