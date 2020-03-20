# Preload TRCH SSW Bare-Metal App binary (configured with default feature set)
# into TRCH on-chip SRAM and preload RTEMS to RTPS DRAM. Boot TRCH into SSW BM App
# and have it boot RTPS R52 in lockstep mode into U-boot, which then boots into
# RTEMS.

include $(CONF)/platform/Makefile
include $(CONF)/lib-trch-bm-default/Makefile
include $(CONF)/lib-preload-trch-bm/Makefile
include $(CONF)/lib-trch-bm-preload-boot/Makefile

# RTEMS tests accesses off-chip memory
include $(CONF)/lib-lsio-smc-sram-nvram/Makefile

include $(CONF)/lib-rtps-r52-lock/Makefile
include $(CONF)/lib-r52-uboot-rtems/Makefile
include $(CONF)/lib-r52-rtems-default/Makefile
