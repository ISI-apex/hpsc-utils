# Like sys-preload-trch-bm-min-hpps-128M-ub-nodcd-booti-busybox, but
# with HPPS SMC-353 memory controller hardware model with NOR Flash
# memory chip connected to bank 0 of SRAM interface enabled in Qemu and
# SMC-353 and drivers enabled in Linux.

$(call push-prof)

include $(CONF)/sys-preload-trch-bm-min-hpps-128M-ub-nodcd-booti-busybox/Makefile
include $(CONF)/lib-hpps-smc-sram-nor/Makefile
include $(CONF)/lib-hpps-linux-tests/Makefile

PROF_CONF:=$(CONF)/$(call pop-prof)

$(PROF_BLD)/hpps/linux-tests.paths: $(PROF_CONF)/hpps/linux-tests.paths
$(PROF_BLD)/hpps/initramfs.fs: $(PROF_CONF)/hpps/initramfs.dir
