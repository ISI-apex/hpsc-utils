# Like sys-preload-trch-bm-min-hpps-128M-ub-nodcd-booti-busybox, but
# with HPPS SMC-353 memory controller hardware model enabled with a
# generic NV RAM memory chip connected to each bank of the SRAM
# interface in Qemu and SMC-353 and drivers enabled in Linux. Include
# binary for NVRAM test into initramfs.

include $(CONF)/sys-preload-trch-bm-min-hpps-128M-ub-nodcd-booti-busybox/Makefile
include $(CONF)/lib-hpps-smc-sram-nvram/Makefile
