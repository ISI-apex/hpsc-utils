# Preload SSW baremetal application image into TRCH on-chip SRAM (via HW
# emulator), and boot TRCH into this app upon system reset.

$(call push-prof)

include $(CONF)/lib-trch-bm/Makefile

PROF_CONF:=$(CONF)/$(call pop-prof)

$(PROF_BLD)/trch/bm.config.mk: $(PROF_CONF)/trch/bm.config.mk
$(PROF_BLD)/trch/syscfg.ini: $(PROF_CONF)/trch/syscfg.ini

$(PROF_BLD)/preload.mem.map: $(PROF_CONF)/preload.mem.map
