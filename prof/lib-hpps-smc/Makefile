# Enable the single SMC-353 controller in HPPS

$(call push-prof)
# includes
PROF_CONF:=$(CONF)/$(call pop-prof)

$(PROF_BLD)/hpps/linux.cpp.dts: private CFLAGS+=-DCONFIG_SMC=1
$(PROF_BLD)/qemu/hpsc.cpp.dts: private CFLAGS+=-DCONFIG_HPPS_SMC=1

# Enable debug output. Letting this be default, but if too verbose,
# can split off into a separate profile.
$(PROF_BLD)/hpps/linux: private MAKE_ARGS=CFLAGS_pl35x-smc.o+=-DDEBUG
