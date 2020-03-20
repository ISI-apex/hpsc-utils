# Enable Watchdog Timers in HPPS (in HPPS Linux and TRCH SSW BM App)

$(call push-prof)
# includes
PROF_CONF:=$(CONF)/$(call pop-prof)

$(PROF_BLD)/hpps/linux.config: $(PROF_CONF)/hpps/linux.config
$(PROF_BLD)/trch/bm.config.mk: $(PROF_CONF)/trch/bm.config.mk
$(PROF_BLD)/hpps/linux.cpp.dts: private CFLAGS+=-DCONFIG_WDTS=1
$(PROF_BLD)/qemu/hpsc.cpp.dts: private CFLAGS+=-DCONFIG_HPPS_WDTS=1
