# [LIB] Add a specified subset of userspace tests to initramfs image for
# HPPS Linux. Including profile must provide list of paths in
# hpps/linux-tests.paths

$(call push-prof)
# includes
PROF_CONF:=$(CONF)/$(call pop-prof)

# merge base
$(PROF_BLD)/hpps/linux-tests.paths:


$(PROF_BLD)/hpps/linux-tests/install.fr.dir: TEST_INSTALL_PATH=opt/hpsc-utils
$(PROF_BLD)/hpps/linux-tests.fr.dir: \
	$(PROF_BLD)/hpps/linux-tests/install.fr.dir \
	$(PROF_BLD)/hpps/linux-tests.paths \
	| $(PROF_BLD)/hpps/linux-tests.fr.dir/
	fakeroot -i $<.fr -s $@.fr \
		rsync -aq --files-from=$(PROF_BLD)/hpps/linux-tests.paths $</ $@/

$(PROF_BLD)/hpps/initramfs.fs: $(PROF_BLD)/hpps/linux-tests.fr.dir
$(call dir-tree-rule,$(PROF_CONF)/hpps/initramfs.dir)
