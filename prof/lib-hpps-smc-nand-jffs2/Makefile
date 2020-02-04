# Connect NAND flash memory chip to SMC-353 and enable JFFS2 in HPPS Linux.
# Uppon boot, mount the memory chip.

$(call push-prof)
include $(CONF)/lib-hpps-smc-nand/Makefile
include $(CONF)/lib-hpps-linux-jffs2/Makefile
PROF_CONF:=$(CONF)/$(call pop-prof)

$(PROF_BLD)/hpps/initramfs.fs: $(PROF_CONF)/hpps/initramfs.dir.sh \
	$(PROF_CONF)/hpps/initramfs.dir
