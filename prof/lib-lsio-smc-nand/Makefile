# Enable the single SMC-353 controller in LSIO and connect
# a NAND flash memory chip to bank 0 of the NAND interface.

$(call push-prof)

include $(CONF)/lib-lsio-smc/Makefile

PROF_CONF:=$(CONF)/$(call pop-prof)

$(PROF_BLD)/qemu/hpsc.cpp.dts: private CFLAGS+=-DCONFIG_LSIO_SMC_NAND=1
$(PROF_BLD)/mem.ini: $(PROF_CONF)/mem.ini
