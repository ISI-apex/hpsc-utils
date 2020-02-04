# In Qemu machine configuration, enable HPPS SMC-353 controller, connect
# a generic NVRAM memory chip to each bank of the HPPS SMC-353 SRAM
# interface.

$(call push-prof)

include $(CONF)/lib-hpps-smc/Makefile
include $(CONF)/lib-hpps-linux-tests/Makefile

PROF_CONF:=$(CONF)/$(call pop-prof)

$(PROF_BLD)/qemu/hpsc.cpp.dts: private CFLAGS+=-DCONFIG_HPPS_SMC_SRAM__NVRAM=1
$(PROF_BLD)/hpps/linux.cpp.dts: private CFLAGS+=-DCONFIG_SMC_SRAM__NVRAM=1

$(PROF_BLD)/mem.ini: $(PROF_CONF)/mem.ini
$(PROF_BLD)/qemu/mem.ini: $(PROF_CONF)/qemu/mem.ini

$(PROF_BLD)/hpps/linux-tests.paths: $(PROF_CONF)/hpps/linux-tests.paths
$(PROF_BLD)/hpps/initramfs.fs: $(PROF_CONF)/hpps/initramfs.dir
