# Configure TRCH Bare-Metal App with the default config (most functionality
# enabled).

$(call push-prof)
include $(CONF)/lib-lsio-smc-sram-nvram/Makefile
include $(CONF)/lib-lsio-smc-nand/Makefile
PROF_CONF:=$(CONF)/$(call pop-prof)

# The BM app default config is tracked in the TRCH BM repo, what we need to do
# here is to enable the hardware that is being used by the default config.  We
# do need interrupt controllers from all subsystems since we want to use
# hardware blocks that are connected to those subsystems. In other words, the
# default (full) config of TRCH BM SSW app only makes sense when the machine
# has all subsystems and most hardware. To boot with a smaller subset of the
# hardware enabled, you have to boot TRCH with a smaller feature set (see
# lib-trch-bm-min profile).
$(PROF_BLD)/qemu/hpsc.cpp.dts: private CFLAGS+=$(patsubst %,-D%=1,\
		CONFIG_TRCH_WDTS \
		CONFIG_RTPS_R52 \
		CONFIG_RTPS_R52_WDTS \
		CONFIG_RTPS_A53 \
		CONFIG_RTPS_A53_WDTS \
		CONFIG_HPPS_A53 \
		CONFIG_HPPS_WDTS \
		CONFIG_TRCH_DMA \
		CONFIG_LSIO_MAILBOX \
		CONFIG_HPPS_MAILBOX_0 \
		CONFIG_HPPS_MAILBOX_1 \
		CONFIG_HPPS_DDR_HI \
	)
