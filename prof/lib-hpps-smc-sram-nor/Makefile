# In Qemu machine configuration, enable HPPS SMC-353 controller, connect
# a NOR Flash memory chip to bank 0 of the HPPS SMC-353 SRAM interface,
# enable MTD drivers in Linux.

$(call push-prof)

include $(CONF)/lib-hpps-smc/Makefile
include $(CONF)/lib-hpps-linux-mtd/Makefile

PROF_CONF:=$(CONF)/$(call pop-prof)

$(PROF_BLD)/mem.ini: $(PROF_CONF)/mem.ini

$(PROF_BLD)/qemu/hpsc.cpp.dts: private CFLAGS+=-DCONFIG_HPPS_SMC_SRAM__NOR=1
$(PROF_BLD)/hpps/linux.cpp.dts: private CFLAGS+=-DCONFIG_SMC_SRAM__NOR=1
$(PROF_BLD)/hpps/linux.config: $(PROF_CONF)/hpps/linux.config
