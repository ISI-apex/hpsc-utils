# Like sys-preload-trch-bm-min-hpps-128M-ub-nodcd-booti-busybox, but
# with HPPS SMC-353 memory controller hardware model enabled with a
# NAND flash memory chip connected to bank 0 of the NAND
# interface in Qemu and SMC-353 and drivers enabled in Linux. Upon
# boot mount the memory chip as a JFFS2 file system and perform
# a write, unmount, remount test.

include $(CONF)/sys-preload-trch-bm-min-hpps-128M-ub-nodcd-booti-busybox/Makefile
include $(CONF)/lib-hpps-smc-nand-jffs2/Makefile
