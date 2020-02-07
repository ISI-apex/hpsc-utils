# Enable debug output in in U-boot upon DCache disable, which
# happens in Zebu.

$(call push-prof)
# includes
PROF_CONF:=$(CONF)/$(call pop-prof)

$(PROF_BLD)/hpps/u-boot: private MAKE_ARGS+=CFLAGS_board_f.o+=-DDEBUG
