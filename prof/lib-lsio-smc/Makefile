# Enable the single SMC-353 controller in LSIO

$(call push-prof)
# includes
PROF_CONF:=$(CONF)/$(call pop-prof)

$(PROF_BLD)/qemu/hpsc.cpp.dts: private CFLAGS+=-DCONFIG_LSIO_SMC=1
