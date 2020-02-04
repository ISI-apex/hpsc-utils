# Like sys-preload-trch-bm-min-hpps-128M-ub-nodcd-booti-busybox, but with
# HPPS SMC-353 memory controller hardware model with NOR Flash memory chip
# connected to bank 0 of SRAM interface enabled in Qemu and SMC-353 and
# drivers enabled in Linux. Upon boot mount memory chip as JFFS2 file system
# and perform a little write, unmount, remount test.

include $(CONF)/sys-preload-trch-bm-min-hpps-128M-ub-nodcd-booti-busybox/Makefile
include $(CONF)/lib-hpps-smc-sram-nor-jffs2/Makefile
