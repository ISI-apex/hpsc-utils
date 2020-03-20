# Enable all HW IP blocks in HPPS (with Cadence MACB Ethernet NIC) in Qemu
# machine configuration and configure Linux with drivers and device tree nodes
# for all HW. Preload TRCH BL0 into TRCH SRAM (by emulator). BL0 loads TRCH
# Bare-Metal App (configured with default feature set) from non-volatile
# memory. TRCH BM App loads RTPS Bare-Metal App (configured with default
# feature set) binary and U-boot binary into RTPS DRAM and ATF+U-boot+Linux
# binaries (configured with default full feature set) into HPPS DRAM.  RTPS R52
# U-boot boots RTPS Bare-Metal App. HPPS boots into Yocto Linux with rootfs
# mounted from SMC NAND.
# DEPENDS (must be built beforehand): lib-hpps-yocto

include $(CONF)/platform/Makefile
include $(CONF)/lib-trch-bm/Makefile
include $(CONF)/lib-bl0-trch-bm/Makefile
include $(CONF)/lib-trch-bm-nvmem-boot/Makefile
include $(CONF)/lib-trch-bm-default/Makefile
include $(CONF)/lib-r52-uboot-rtems/Makefile
include $(CONF)/lib-r52-rtems-default/Makefile
SHARE += lib-hpps-yocto
include $(CONF)/lib-hpps-yocto-nand-rootfs/Makefile
include $(CONF)/lib-hpps-full/Makefile
include $(CONF)/lib-hpps-eth-cdns/Makefile
include $(CONF)/lib-hpps-linux-tests-all/Makefile

$(PROF_HOME)/test/qemu: TESTS_FILTER+=\
	   TestDMA \
	or TestCPUHotplug \
	or TestIntAffinity \
	or TestMailbox \
	or TestMailboxMultiSystem \
	or TestSharedMem \
	or TestRTITimer \
	or TestSRAM \
	or TestNAND \
	or TestWDTimer \

# This test requires NAS Parallel Benchmarks: not in lib-hpps-yocto config,
# also if the Yocto image is much bigger, layout of binaries in memory
# would need to be changed
# TestParallelScaling

# mmu: need to capture TRCH log, and enable the tests
