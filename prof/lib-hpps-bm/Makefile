# Load a bare-metal app (built image must be provided manually; no source code
# available) into HPPS DRAM by HW emulator (fast).

$(call push-prof)
# includes
PROF_CONF:=$(CONF)/$(call pop-prof)

$(PROF_BLD)/preload-boot.preload.mem.map: $(PROF_CONF)/preload-boot.preload.mem.map
$(PROF_BLD)/qemu/env.sh: $(PROF_CONF)/qemu/env.sh
