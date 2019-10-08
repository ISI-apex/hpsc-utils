# Booting Linux on HPPS

$(call push-prof)
# includes
PROF_CONF:=$(CONF)/$(call pop-prof)

# Artifacts not pulled in automatically since not part of any image
PROF_ARTS += \
	$(PROF_BLD)/hpps/conf.sh \
	$(PROF_BLD)/hpps/atf/atf.dbg.elf \
	$(PROF_BLD)/hpps/u-boot/u-boot.dbg.elf \
	$(PROF_BLD)/hpps/linux/linux.dbg.elf \

$(PROF_BLD)/trch/syscfg.ini: $(PROF_CONF)/trch/syscfg.ini
$(PROF_BLD)/trch/bm.config.mk: $(PROF_CONF)/trch/bm.config.mk
$(PROF_BLD)/trch/boot.sfs.mem.map: $(PROF_CONF)/trch/boot.sfs.mem.map

$(PROF_BLD)/hpps/conf.sh: $(PROF_CONF)/hpps/conf.sh
$(PROF_BLD)/hpps/u-boot.env: $(PROF_CONF)/hpps/u-boot.env
$(PROF_BLD)/hpps/u-boot.dts: $$(S_hpps-uboot)/arch/arm/dts/hpsc-hpps.dts
$(PROF_BLD)/hpps/linux.dts: $$(S_hpps-linux)/arch/arm64/boot/dts/hpsc/hpsc.dts

$(PROF_BLD)/qemu/env.sh: $(PROF_CONF)/qemu/env.sh
$(PROF_BLD)/preload-boot.preload.mem.map: $(PROF_CONF)/preload-boot.preload.mem.map