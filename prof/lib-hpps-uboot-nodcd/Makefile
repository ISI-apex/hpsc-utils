# Apply the workaround (hack) for the hang in U-boot upon DCache disable, which
# happens in Zebu.

$(call push-prof)
# includes
PROF_CONF:=$(CONF)/$(call pop-prof)

$(PROF_BLD)/hpps/u-boot: \
	private MAKE_ARGS+=CFLAGS_cache_v8.o+=-DWORKAROUND_NO_DISABLE_DCACHE
