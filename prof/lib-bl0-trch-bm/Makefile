# Preload SSW baremetal application image into TRCH on-chip SRAM (via HW
# emulator), and boot TRCH.

$(call push-prof)

include $(CONF)/lib-lsio-smc-sram-nvram/Makefile
include $(CONF)/lib-bl0/Makefile
include $(CONF)/lib-trch-bm/Makefile

PROF_CONF:=$(CONF)/$(call pop-prof)

$(PROF_BLD)/trch/bm.config.mk: $(PROF_CONF)/trch/bm.config.mk
$(PROF_BLD)/trch/bl0cfg.ini: $(PROF_CONF)/trch/bl0cfg.ini

$(PROF_BLD)/trch/syscfg.ini: $(PROF_CONF)/trch/syscfg.ini

$(PROF_BLD)/preload.mem.map: $(PROF_CONF)/preload.mem.map
