# In Qemu machine configuration, enable HPPS SMC-353 controller, connect
# the default NAND memory chip to bank 0 of the NAND interface of HPPS
# SMC-353, enable MTD drivers in Linux.

$(call push-prof)

include $(CONF)/lib-hpps-smc/Makefile
include $(CONF)/lib-hpps-linux-mtd/Makefile

PROF_CONF:=$(CONF)/$(call pop-prof)

$(PROF_BLD)/mem.ini: $(PROF_CONF)/mem.ini
$(PROF_BLD)/qemu/mem.ini: $(PROF_CONF)/qemu/mem.ini

$(PROF_BLD)/qemu/hpsc.cpp.dts: private CFLAGS+=-DCONFIG_HPPS_SMC_NAND=1
$(PROF_BLD)/hpps/linux.cpp.dts: private CFLAGS+=-DCONFIG_SMC_NAND=1
