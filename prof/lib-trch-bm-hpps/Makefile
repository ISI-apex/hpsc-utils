# Tell TRCH BM App to boot the HPPS A53 subsystem

$(call push-prof)

include $(CONF)/lib-hpps-a53/Makefile

PROF_CONF:=$(CONF)/$(call pop-prof)

$(PROF_BLD)/trch/syscfg.ini: $(PROF_CONF)/trch/syscfg.ini
