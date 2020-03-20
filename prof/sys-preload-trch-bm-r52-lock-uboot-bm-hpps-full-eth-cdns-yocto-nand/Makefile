# Enable all HPPS HW blocks including Ethernet NIC (Cadence MACB aka STMMAC
# model) in Qemu machine model and drivers for then in Linux kernel.  Preload
# TRCH SSW Bare-Metal App binary (configured with default feature set) into
# TRCH on-chip SRAM and preload RTPS R52 Bare-Metal Application (configured
# with default feature set) to RTPS DRAM and preload ATF+U-boot+Linux binaries
# into HPPS DRAM. Boot TRCH into SSW BM App and have it boot RTPS R52 into
# U-boot, which then boots into SSW BM App; and have TRCH SSW BM App boot HPPS
# into Linux with rootfs mounted from off-chip non-volatile NAND memory.

include $(CONF)/platform/Makefile
include $(CONF)/lib-preload-trch-bm/Makefile
include $(CONF)/lib-trch-bm-preload-boot/Makefile
include $(CONF)/lib-trch-bm-default/Makefile
include $(CONF)/lib-r52-uboot-bm/Makefile
include $(CONF)/lib-r52-bm-default/Makefile
SHARE += lib-hpps-yocto
include $(CONF)/lib-hpps-yocto-nand-rootfs/Makefile
include $(CONF)/lib-hpps-full/Makefile
include $(CONF)/lib-hpps-eth-cdns/Makefile
