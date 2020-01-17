# Enable HPPS SMC-353 memory controller hardware and configure HPPS DRAM of
# 128MB size in Qemu. Preload TRCH SSW Bare-Metal App binary (configured with
# minimal feature set) into TRCH SRAM, and load a bare-metal image into HPPS
# DRAM by HW emulator (fast).

include $(CONF)/platform/Makefile
include $(CONF)/lib-preload-trch-bm/Makefile
include $(CONF)/lib-trch-bm-min/Makefile
include $(CONF)/lib-trch-bm-preload-boot/Makefile
include $(CONF)/lib-trch-bm-hpps/Makefile
include $(CONF)/lib-hpps-ddr-lo-128M/Makefile
include $(CONF)/lib-hpps-smc/Makefile
include $(CONF)/lib-hpps-bm/Makefile
