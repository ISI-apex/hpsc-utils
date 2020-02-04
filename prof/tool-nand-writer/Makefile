# Write a tar.gz archive into image of NV mem at HPPS SMC353 NAND port

$(call push-prof)

include $(CONF)/platform/Makefile
include $(CONF)/lib-preload-trch-bm/Makefile
include $(CONF)/lib-trch-bm-preload-boot/Makefile
include $(CONF)/lib-trch-bm-min/Makefile
include $(CONF)/lib-trch-bm-hpps/Makefile
include $(CONF)/lib-hpps-busybox/Makefile
include $(CONF)/lib-hpps-ddr-high/Makefile
include $(CONF)/lib-hpps-linux-gpmem/Makefile
include $(CONF)/lib-hpps-smc-nand/Makefile

PROF_CONF:=$(CONF)/$(call pop-prof)

$(PROF_BLD)/qemu/env.sh: $(PROF_CONF)/qemu/env.sh

$(PROF_BLD)/trch/bm.config.mk: $(PROF_CONF)/trch/bm.config.mk

$(PROF_BLD)/hpps/initramfs.fs: $(PROF_CONF)/hpps/initramfs.dir
$(call dir-tree-rule,$(PROF_CONF)/hpps/initramfs.dir)
