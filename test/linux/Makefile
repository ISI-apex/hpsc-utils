export RANLIB ?= ranlib
export STRIP ?= strip

export CFLAGS += \
	-Wall -Wextra -Wformat -Wformat-security \
	-O1 -g \
	-fstack-protector-strong \
	-static \

TOPTARGETS := all clean

SUBDIRS := libmbox

BINS = \
	mboxtester \
	mbox-multiple-core-tester \
	shm-standalone-tester \
	shm-tester \
	sram-tester \
	wdtester \
	rtit-tester \
	offchip-sram-tester \
	mbox-server-tester \

SCRIPTS = \
	dma-tester.sh \
	interrupt-affinity-tester.sh \
	rtit-tester.sh \
	wdt-kicker.sh \

.PHONY: $(TOPTARGETS) $(SUBDIRS)

all: $(SUBDIRS) $(BINS)

$(SUBDIRS):
	$(MAKE) -C $@ $(MAKECMDGOALS)

libmbox/libmbox.a:
	$(MAKE) -C $(@D) $(@F)

LDFLAGS_libmbox = -Llibmbox -lmbox
OBJS_mbox = mbox-utils.o

mbox-multiple-core-tester.elf mbox-server-tester.elf mboxtester.elf: %.elf : %.o $(OBJS_mbox) libmbox/libmbox.a
	$(CROSS_COMPILE)$(CC) $(CFLAGS) -o $@ $< $(OBJS_mbox) $(LDFLAGS) $(LDFLAGS_libmbox)

%.o: %.c
	$(CROSS_COMPILE)$(CC) $(CFLAGS) -c -o $@ $< $(LDFLAGS)

%.elf: %.c
	$(CROSS_COMPILE)$(CC) $(CFLAGS) -o $@ $(OBJS) $< $(LDFLAGS)

# %: %.elf doesn't match for some reason
define strip-rule
$(1): $(1).elf
	cp $$< $$@
	$(CROSS_COMPILE)$(STRIP) $$@
endef
$(foreach b,$(BINS),$(eval $(call strip-rule,$(b))))

clean: $(SUBDIRS)
	rm -rf *.o *.elf *.out $(BINS)

install: $(BINS)
	mkdir -p $(DEST)
	install $(BINS) $(SCRIPTS) $(DEST)
