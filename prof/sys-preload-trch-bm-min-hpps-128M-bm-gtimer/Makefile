# Configure HPPS DRAM of 128MB size in Qemu. Preload TRCH SSW Bare-Metal App
# binary (configured with minimal feature set) into TRCH SRAM, and load a
# bare-metal image into HPPS DRAM by HW emulator (fast).

$(call push-prof)

include $(CONF)/platform/Makefile
include $(CONF)/lib-preload-trch-bm/Makefile
include $(CONF)/lib-trch-bm-min/Makefile
include $(CONF)/lib-trch-bm-preload-boot/Makefile
include $(CONF)/lib-trch-bm-hpps/Makefile
include $(CONF)/lib-hpps-ddr-lo-128M/Makefile
include $(CONF)/lib-hpps-bm/Makefile

PROF_CONF:=$(CONF)/$(call pop-prof)

$(PROF_BLD)/preload-boot.preload.mem.map: $(PROF_CONF)/preload-boot.preload.mem.map
