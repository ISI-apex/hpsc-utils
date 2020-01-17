# Boot ATF+U-boot up to command prompt on RTPS A53

$(call push-prof)

include $(CONF)/lib-rtps-a53/Makefile

PROF_CONF:=$(CONF)/$(call pop-prof)

# Artifacts not pulled in automatically since not part of any image
PROF_ARTS += \
	$(PROF_BLD)/rtps/a53/atf/atf.dbg.elf \
	$(PROF_BLD)/rtps/a53/u-boot/u-boot.dbg.elf \

$(PROF_BLD)/rtps/a53/u-boot.config: $(PROF_CONF)/rtps/a53/u-boot.config
$(PROF_BLD)/rtps/a53/u-boot.env: $(PROF_CONF)/rtps/a53/u-boot.env

$(PROF_BLD)/trch/syscfg.ini: $(PROF_CONF)/trch/syscfg.ini
$(PROF_BLD)/trch/boot.sfs.mem.map: $(PROF_CONF)/trch/boot.sfs.mem.map

# We're using DTB within the u-boot image, but if we ever split it, then:
# $(PROF_BLD)/rtps/a53/u-boot.dts: \
	$$(S_rtps-a53-uboot)/arch/arm/dts/hpsc-rtps-a53.dts

$(PROF_BLD)/preload-boot.preload.mem.map: $(PROF_CONF)/preload-boot.preload.mem.map

# Disable the PSCI mailbox to TRCH (not needed, so far)
$(PROF_BLD)/rtps/a53/atf.config.mk: $(PROF_CONF)/rtps/a53/atf.config.mk
$(PROF_BLD)/trch/bm.config.mk: $(PROF_CONF)/trch/bm.config.mk

# TODO: CPU reset vector should be configurable dynamically by TRCH,
# for now, configure it statically via Qemu DT.
$(PROF_BLD)/qemu/hpsc.dts: $(PROF_CONF)/qemu/hpsc.dts

$(PROF_BLD)/qemu/env.sh: $(PROF_CONF)/qemu/env.sh
