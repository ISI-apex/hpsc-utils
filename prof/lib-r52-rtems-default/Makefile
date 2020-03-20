# Configure for default RTEMS configuration (all HW drivers enabled, tests run
# on boot).

$(call push-prof)
# includes
PROF_CONF:=$(CONF)/$(call pop-prof)

$(PROF_BLD)/qemu/hpsc.cpp.dts: private CFLAGS+=$(patsubst %,-D%=1,\
		CONFIG_LSIO_MAILBOX \
		CONFIG_RTPS_DMA \
		CONFIG_RTPS_R52_WDTS \
		CONFIG_RTPS_R52_RTI_TIMERS \
		CONFIG_RTPS_SMMU \
		CONFIG_RTPS_SPI \
		CONFIG_HPPS_MAILBOX_1 \
	)

# Simple File System with some test data for RTEMS
$(PROF_BLD)/rtps/r52/test.sfs.ini: $(PROF_CONF)/rtps/r52/test.sfs.ini \
                               | $(PROF_BLD)/rtps/r52/
$(PROF_BLD)/rtps/r52/test.sfs.mem.map: $(PROF_CONF)/rtps/r52/test.sfs.mem.map | $(PROF_BLD)/rtps/r52/
PROF_ARTS += $(PROF_BLD)/rtps/r52/test.sfs.mem.map

# RTEMS test checks file content for this pattern
$(PROF_BLD)/rtps/r52/test-data.txt: $(PROF_CONF)/rtps/r52/test-data.txt
	$(COPY) $< $@

$(PROF_BLD)/preload.mem.map: $(PROF_CONF)/preload.mem.map
