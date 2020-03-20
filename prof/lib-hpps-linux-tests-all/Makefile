# Include all linux tests into root filesystem

$(call push-prof)

include $(CONF)/lib-hpps-linux-tests/Makefile

PROF_CONF:=$(CONF)/$(call pop-prof)

$(PROF_BLD)/hpps/linux-tests.paths: $(PROF_CONF)/hpps/linux-tests.paths
#$(PROF_BLD)/hpps/initramfs.fs: $(PROF_CONF)/hpps/initramfs.dir
