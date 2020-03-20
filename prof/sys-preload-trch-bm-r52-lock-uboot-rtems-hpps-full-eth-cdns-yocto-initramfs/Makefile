# Enable all HPPS HW blocks including Ethernet NIC (Cadence MACB aka STMMAC
# model) in Qemu machine model and drivers for then in Linux kernel.  Preload
# TRCH SSW Bare-Metal App binary (configured with default feature set) into
# TRCH on-chip SRAM and preload RTPS R52 RTEMS to RTPS DRAM and preload
# ATF+U-boot+Linux binaries into HPPS DRAM. Boot TRCH into SSW BM App and have
# it boot RTPS R52 in lockstep mode into U-boot, which then boots into RTEMS;
# and have TRCH SSW BM App boot HPPS into Linux with Yocto initramfs archive.

include $(CONF)/platform/Makefile
include $(CONF)/lib-preload-trch-bm/Makefile
include $(CONF)/lib-trch-bm-preload-boot/Makefile
include $(CONF)/lib-trch-bm-default/Makefile
include $(CONF)/lib-trch-bm-test-mmu/Makefile # just for pytest
include $(CONF)/lib-rtps-r52-lock/Makefile
include $(CONF)/lib-r52-uboot-rtems/Makefile
include $(CONF)/lib-r52-rtems-default/Makefile
SHARE += lib-hpps-yocto
include $(CONF)/lib-hpps-yocto-initramfs/Makefile
include $(CONF)/lib-hpps-full/Makefile
include $(CONF)/lib-hpps-eth-cdns/Makefile
# TODO: can this be added to full?
include $(CONF)/lib-hpps-smc-sram-nvram/Makefile
include $(CONF)/lib-hpps-linux-tests-all/Makefile

$(PROF_HOME)/test/qemu: TESTS_FILTER+=\
	   TestDMA \
	or TestCPUHotplug \
	or TestIntAffinity \
	or TestMailbox \
	or TestMailboxMultiSystem \
	or TestSharedMem \
	or TestRTITimer \

# These tests require reboot, but this profile preloads binaries so can't reboot
# TestSRAM
# TestWDTimer
# TestNAND

# This test requires NAS Parallel Benchmarks: not in lib-hpps-yocto config,
# also if the Yocto image is much bigger, layout of binaries in memory
# would need to be changed
# TestParallelScaling

# mmu: need to capture TRCH log, and enable the tests
