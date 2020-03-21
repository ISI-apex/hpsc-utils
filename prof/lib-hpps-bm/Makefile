# Load a bare-metal app (profiles that include this profile
# provide the image) into HPPS DRAM by HW emulator (fast).

$(call push-prof)
# includes
PROF_CONF:=$(CONF)/$(call pop-prof)

$(PROF_BLD)/preload-boot.preload.mem.map: $(PROF_CONF)/preload-boot.preload.mem.map
$(PROF_BLD)/qemu/env.sh: $(PROF_CONF)/qemu/env.sh
