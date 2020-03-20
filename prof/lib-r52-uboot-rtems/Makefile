# Boot RTEMS on RTPS R52 via U-boot

$(call push-prof)

include $(CONF)/lib-r52-uboot/Makefile

PROF_CONF:=$(CONF)/$(call pop-prof)

$(PROF_BLD)/trch/syscfg.ini: $(PROF_CONF)/trch/syscfg.ini

$(PROF_BLD)/preload-boot.preload.mem.map: $(PROF_CONF)/preload-boot.preload.mem.map
$(PROF_BLD)/trch/boot.sfs.mem.map: $(PROF_CONF)/trch/boot.sfs.mem.map

$(PROF_BLD)/rtps/r52/u-boot.env: $(PROF_CONF)/rtps/r52/u-boot.env
