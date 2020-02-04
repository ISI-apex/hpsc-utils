# Like sys-preload-trch-bm-min-hpps-128M-ub-nodcd-booti-busybox, but
# with HPPS SMC-353 memory controller hardware model enabled with a NOR
# flash memory chip connected to bank 0 of the SRAM interface and a NAND
# flash memory chip connected to bank 0 of the NAND interface in Qemu
# and drivers enabled in Linux. Upon booting, mount both memory chips
# as JFFS2 file systems.

$(call push-prof)
include $(CONF)/sys-preload-trch-bm-min-hpps-128M-ub-nodcd-booti-busybox/Makefile
include $(CONF)/lib-hpps-smc-sram-nor-jffs2/Makefile
include $(CONF)/lib-hpps-smc-nand-jffs2/Makefile
PROF_CONF:=$(CONF)/$(call pop-prof)

# Need to re-assign the indexes of mtdX devices
$(PROF_BLD)/hpps/initramfs.fs: $(PROF_CONF)/hpps/initramfs.dir
