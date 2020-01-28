# Preload TRCH SSW Bare-Metal App binary (configured with minimal feature set)
# into TRCH SRAM, and ATF+U-boot+Linux binaries (configured for non-SMP boot
# -- single core) into HPPS DRAM by HW emulator (fast). Apply the workaround
# for the slow execution in Zebu (by adding SEV instruction in ATF), for
# disabling dual-issue mode in Cortex-A53, and for the hang in U-boot in Dcache
# disable (do not disable), and enable debug output in U-boot. Boot TRCH into
# TRCH SSW Bare-Metal App, boot HPPS into Busybox on Linux via U-boot+ATF.

include $(CONF)/platform/Makefile
include $(CONF)/lib-preload-trch-bm/Makefile
include $(CONF)/lib-trch-bm-min/Makefile
include $(CONF)/lib-trch-bm-preload-boot/Makefile
include $(CONF)/lib-hpps-busybox/Makefile
include $(CONF)/lib-hpps-atf-sev/Makefile
include $(CONF)/lib-hpps-atf-si/Makefile
include $(CONF)/lib-hpps-uboot-nodcd/Makefile
include $(CONF)/lib-hpps-uboot-dbg/Makefile
include $(CONF)/lib-hpps-linux-booti/Makefile
include $(CONF)/lib-hpps-ddr-lo-128M/Makefile
