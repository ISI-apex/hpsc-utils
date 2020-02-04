# Like sys-preload-trch-bm-min-hpps-128M-ub-nodcd-booti-busybox, but
# with HPPS SMC-353 memory controller hardware model enabled with a
# generic NV RAM memory chip connected to each bank of the SRAM
# interface and a NAND Flash memory chip connected to bank 0 of the NAND
# interface in Qemu and drivers enabled in Linux. Upon boot mount as
# a JFFS2 filesystem.

include $(CONF)/sys-preload-trch-bm-min-hpps-128M-ub-nodcd-booti-busybox/Makefile
include $(CONF)/lib-hpps-smc-sram-nvram/Makefile
include $(CONF)/lib-hpps-smc-nand-jffs2/Makefile
