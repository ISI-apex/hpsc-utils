#!/bin/bash

# Note: Before running the following script, please make sure to:
#
# 1.  Run the "build-hpsc-yocto.sh" script with the "bitbake core-image-minimal"
#     option in order to generate many of the needed QEMU files.
#
# 2.  Run the "build-hpsc-baremetal.sh" script (with the proper toolchain
#     path) to create the baremetal firmware files "trch.elf" and "rtps.elf".

# Output files from the Yocto build
WORKING_DIR=${PWD}/HEAD
YOCTO_DEPLOY_DIR=${WORKING_DIR}/poky/build/tmp/deploy/images/hpsc-chiplet
HPPS_FW=${YOCTO_DEPLOY_DIR}/arm-trusted-firmware.bin
HPPS_BL=${YOCTO_DEPLOY_DIR}/u-boot.bin
HPPS_DT=${YOCTO_DEPLOY_DIR}/hpsc.dtb
HPPS_KERN_BIN=${YOCTO_DEPLOY_DIR}/Image.gz
HPPS_KERN=${YOCTO_DEPLOY_DIR}/uImage # generated by this script
HPPS_RAMDISK=${YOCTO_DEPLOY_DIR}/core-image-minimal-hpsc-chiplet.cpio.gz.u-boot

# Output files from the hpsc-baremetal build
BAREMETAL_DIR=${WORKING_DIR}/hpsc-baremetal
TRCH_APP=${BAREMETAL_DIR}/trch/bld/trch.elf
RTPS_APP=${BAREMETAL_DIR}/rtps/bld/rtps.elf

# Output files from the hpsc-R52-uboot build
RTPS_BL_DIR=${WORKING_DIR}/u-boot-r52
RTPS_BL=${RTPS_BL_DIR}/u-boot.bin

# Output files from the qemu/qemu-devicetree builds
QEMU_DIR=${WORKING_DIR}/qemu/BUILD/aarch64-softmmu
QEMU_DT_FILE=${WORKING_DIR}/qemu-devicetrees/LATEST/SINGLE_ARCH/hpsc-arch.dtb

# External storage (NAND, SRAM) devices
# how to use:
#    -drive file=$HPPS_NAND_IMAGE,if=pflash,format=raw,index=3 \
#    -drive file=$HPPS_SRAM_FILE,if=pflash,format=raw,index=2 \
#    -drive file=$TRCH_SRAM_FILE,if=pflash,format=raw,index=0 \

HPPS_NAND_IMAGE=${YOCTO_DEPLOY_DIR}/rootfs_nand.bin
HPPS_SRAM_FILE=${YOCTO_DEPLOY_DIR}/hpps_sram.bin
TRCH_SRAM_FILE=${YOCTO_DEPLOY_DIR}/trch_sram.bin

# Chiplet-wide boot configuration communicatd to TRCH
TRCH_BOOT_MODE_ADDR=0x000ff000 # in TRCH SRAM
TRCH_BOOT_MODE_SRAM=0x00000001 # load RTPS/HPPS images from SRAM
TRCH_BOOT_MODE_DRAM=0x00000002 # assume RTPS/HPPS images already in DRAM

# Controlling boot mode of RTPS (Split or lock-step)
RTPS_BOOT_MODE_ADDR=0x000ff004 # in TRCH SRAM
RTPS_BOOT_SPLIT=0x00000000
RTPS_BOOT_LOCKSTEP=0x00000001
RTPS_BOOT_SMP=0x00000002

# Controlling boot mode of HPPS (ramdisk or rootfs in NAND)
# how to use:
#    -device loader,addr=$BOOT_MODE_ADDR,data=$BOOT_MODE,data-len=4,cpu-num=3 \

HPPS_BOOT_MODE_ADDR=0x9f000000    # memory location to store boot mode code for HPPS U-boot
HPPS_BOOT_MODE_DRAM=0x00000000    # HPPS rootfs in RAM
HPPS_BOOT_MODE_NAND=0x0000f000    # HPPS rootfs in NAND (MTD device)

HPPS_FW_ADDR=0x80000000
HPPS_BL_ADDR=0x88000000
HPPS_KERN_ADDR=0x81080000
HPPS_KERN_LOAD_ADDR=0x80080000
HPPS_DT_ADDR=0x84000000
HPPS_RAMDISK_ADDR=0x90000000
# HPPS_RAMDISK_LOAD_ADDR      # where BL extracts the ramdisk, set by u-boot image header

# RTPS
RTPS_BL_ADDR=0x60000000       # load address for R52 u-boot
RTPS_APP_ADDR=0x68000000      # address of baremetal app ELF file
# RTPS_APP_LOAD_ADDR          # where BL loads the ELF sections, set in the ELF header

# TRCH
# TRCH_APP_LOAD_ADDR          # where ELF sections are loaded, set in the ELF header
HPSC_HOST_UTILS_DIR=${WORKING_DIR}/hpsc-utils/host
SRAM_IMAGE_UTILS=${HPSC_HOST_UTILS_DIR}/sram-image-utils
SRAM_SIZE=0x4000000           # 64MB

# create non-volatile offchip sram image
function create_nvsram_image()
{
    set -e
    echo create_sram_image...
    # Create SRAM image to store boot images
    "${SRAM_IMAGE_UTILS}" create "${TRCH_SRAM_FILE}" ${SRAM_SIZE}
    "${SRAM_IMAGE_UTILS}" add "${TRCH_SRAM_FILE}" "${RTPS_BL}"      "rtps-bl" ${RTPS_BL_ADDR}
    "${SRAM_IMAGE_UTILS}" add "${TRCH_SRAM_FILE}" "${RTPS_APP}"     "rtps-os" ${RTPS_APP_ADDR}
    "${SRAM_IMAGE_UTILS}" add "${TRCH_SRAM_FILE}" "${HPPS_BL}"      "hpps-bl" ${HPPS_BL_ADDR}
    "${SRAM_IMAGE_UTILS}" add "${TRCH_SRAM_FILE}" "${HPPS_FW}"      "hpps-fw" ${HPPS_FW_ADDR}
    "${SRAM_IMAGE_UTILS}" add "${TRCH_SRAM_FILE}" "${HPPS_DT}"      "hpps-dt" ${HPPS_DT_ADDR}
    "${SRAM_IMAGE_UTILS}" add "${TRCH_SRAM_FILE}" "${HPPS_KERN}"    "hpps-os" ${HPPS_KERN_ADDR}
    "${SRAM_IMAGE_UTILS}" show "${TRCH_SRAM_FILE}" 
    set +e
}

function usage()
{
    echo "Usage: $0 [-c < run | gdb | consoles | nand_create >] [-f < dram | nand >] [-b < dram | nvram >] [ -h ] " 1>&2
    echo "               -c run: command - start emulation (default)" 1>&2
    echo "               -c gdb: command - start emulation with gdb" 1>&2
    echo "               -c consoles: command - setup consoles of the subsystems at the host" 1>&2
    echo "               -c nand_create: command - create nand image with rootfs in it" 1>&2
    echo "               -c sram_create: command - create sram image" 1>&2
    echo "               -b dram: boot images in dram (default)" 1>&2
    echo "               -b nvram: boot images in offchip non-volatile ram" 1>&2
    echo "               -f dram: HPPS rootfile system in ram, volatile (default)" 1>&2
    echo "               -f nand: HPPS rootfile system in nand image, non-volatile" 1>&2
    echo "               -h : show this message" 1>&2
    exit 1
}

# Labels are created by Qemu with the convention "serialN"
SCREEN_SESSIONS=(hpsc-trch hpsc-rtps-r52 hpsc-hpps)
SERIAL_PORTS=(serial0 serial1 serial2)
SERIAL_PORT_ARGS=()
for port in "${SERIAL_PORTS[@]}"
do
    SERIAL_PORT_ARGS+=(-serial pty)
done

QMP_PORT=4433

function setup_screen()
{
    local SESSION=$1

    if [ $(screen -list "$SESSION" | grep -c "$SESSION") -gt 1 ]
    then
        # In case the user somehow ended up with more than one screen process,
        # kill them all and create a fresh one.
        echo "Found multiple screen sessions matching '$SESSION', killing..."
        screen -list "$SESSION" | grep "$SESSION" | \
            sed -n "s/\([0-9]\+\).$SESSION\s\+.*/\1/p" | xargs kill
    fi

    # There seem to be some compatibility issues between Linux distros w.r.t.
    # exit codes and behavior when using -r and -q with -ls for detecting if a
    # user is attached to a session, so we won't bother trying to wait for them.
    screen -q -list "$SESSION"
    # it's at least consistent that no matching screen sessions gives $? < 10
    if [ $? -lt 10 ]
    then
        echo "Creating screen session with console: $SESSION"
        screen -d -m -S "$SESSION"
    fi
}

function attach_consoles()
{
    echo "Waiting for Qemu to open QMP port and to query for PTY paths..."
    #while test $(lsof -ti :$QMP_PORT | wc -l) -eq 0
    while true
    do
        PTYS=$(./qmp.py -q localhost $QMP_PORT query-chardev ${SERIAL_PORTS[*]} 2>/dev/null)
        if [ -z "$PTYS" ]
        then
            #echo "Waiting for Qemu to open QMP port..."
            sleep 1
            ATTEMPTS+=" 1 "
            if [ $(echo "$ATTEMPTS" | wc -w) -eq 10 ]
            then
                echo "ERROR: failed to get PTY paths from Qemu via QMP port: giving up."
                echo "Here is what happened when we tried to get the PTY paths:"
                ./qmp.py -q localhost $QMP_PORT query-chardev ${SERIAL_PORTS[*]}
                exit # give up to not accumulate waiting processes
            fi
        else
            break
        fi
    done

    read -r -a PTYS_ARR <<< "$PTYS"
    for ((i = 0; i < ${#PTYS_ARR[@]}; i++))
    do
        # Need to start a new single-use $pty_sess screen session outside of the
        # persistent $sess one, then attach to $pty_sess from within $sess.
        # This is needed if $sess was previously attached, then detached (but
        # not terminated) after QEMU exited.
        local pty=${PTYS_ARR[$i]}
        local sess=${SCREEN_SESSIONS[$i]}
        local pty_sess="hpsc-pts$(basename "$pty")"
        echo "Adding console $pty to screen session $sess"
        screen -d -m -S "$pty_sess" "$pty"
        # TODO: Make this work without using "stuff" command
        screen -S "$sess" -X stuff "^C screen -m -r $pty_sess\r"
        echo "Attach to screen session from another window with:"
        echo "  screen -r $sess"
    done

    echo "Commanding Qemu to reset the machine..."
    ./qmp.py localhost $QMP_PORT cont
}


# default values
CMDS=()
BOOT_IMAGE_OPTION="dram"
HPPS_ROOTFS_OPTION="dram"

# parse options
while getopts "h?b:c:f:" o; do
    case "${o}" in
        c)
            if [[ "${OPTARG}" =~ ^run|gdb|consoles|nand_create|sram_create$ ]]
            then
                CMDS+=("${OPTARG}")
            else
                echo "Error: no such command - ${OPTARG}"
                usage
            fi
            ;;
        b)
            if [ "${OPTARG}" == "dram" ] || [ "${OPTARG}" == "nvram" ]
            then
                BOOT_IMAGE_OPTION="${OPTARG}"
            else
                echo "Error: no such boot image option - ${OPTARG}"
                usage
            fi
            ;;
        f)
            if [ "${OPTARG}" == "dram" ] || [ "${OPTARG}" == "nand" ]
            then
                HPPS_ROOTFS_OPTION="${OPTARG}"
            else
                echo "Error: no such HPPS rootfile system option - ${OPTARG}"
                usage
            fi
            ;;
        h)
            usage
            ;;
        *)
            echo "Wrong option" 1>&2
            usage
            ;;
    esac
done
shift $((OPTIND-1))

if [ ${#CMDS[@]} -eq 0 ]
then
    CMDS+=("run")
fi

RUN=0
echo "CMDS: ${CMDS[*]}"
for CMD in "${CMDS[@]}"
do
    echo CMD: $CMD
    case "$CMD" in
       run)
            for session in "${SCREEN_SESSIONS[@]}"
            do
                setup_screen $session
            done
            attach_consoles &
            RUN=1
            ;;
       gdb)
            # setup/attach_consoles are called when gdb runs this script with "consoles"
            # cmd from the hook to the "run" command defined below:
            # NOTE: have to go through an actual file because -ex doesn't work since no way
            ## to give a multiline command (incl. multiple -ex), and bash-created file -x
            # <(echo -e ...) doesn't work either (issue only with gdb).
           GDB_CMD_FILE=$(mktemp)
           cat >/"$GDB_CMD_FILE" <<EOF
define hook-run
shell $0 -c consoles -c sram_create
end
EOF
            GDB_ARGS=(gdb -x "$GDB_CMD_FILE" --args)
            RUN=1
            ;;
        consoles)
            echo "run setup_screen"
            for session in "${SCREEN_SESSIONS[@]}"
            do
                setup_screen $session
            done
            echo "run attach_consoles"
            attach_consoles &
            ;;
       sram_create)
            create_nvsram_image
            ;;
       nand_create)
            for session in "${SCREEN_SESSIONS[@]}"
            do
                setup_screen $session
            done
            attach_consoles &
            ;;
    esac
done

if [ "$RUN" -eq 0 ]
then
    exit
fi

#
# Compose qemu commands according to the command options.
# Build the command as an array of strings. Quote anything with a path variable
# or that uses commas as part of a string instance. Building as a string and
# using eval on it is error-prone, e.g., if spaces are introduced to parameters.
#
# See QEMU User Guide in HPSC release for explanation of the command line arguments
# Note: order of -device args may matter, must load ATF last, because loader also sets PC
# Note: If you want to see instructions and exceptions at a large performance cost, then add
# "in_asm,int" to the list of categories in -d.

mkimage -C gzip -A arm64 -d "${HPPS_KERN_BIN}" -a ${HPPS_KERN_LOAD_ADDR} "${HPPS_KERN}"

BASE_COMMAND=("${GDB_ARGS[@]}" "${QEMU_DIR}/qemu-system-aarch64"
    -machine "arm-generic-fdt"
    -nographic
    -monitor stdio
    -qmp "telnet::$QMP_PORT,server,nowait"
    -S -s -D "/tmp/qemu.log" -d "fdt,guest_errors,unimp,cpu_reset"
    -hw-dtb "${QEMU_DT_FILE}"
    "${SERIAL_PORT_ARGS[@]}"
    -net "nic,vlan=0" -net "user,vlan=0,hostfwd=tcp:127.0.0.1:2345-10.0.2.15:2345,hostfwd=tcp:127.0.0.1:10022-10.0.2.15:22")

# Storing TRCH code in NV mem is not yet supported, so it is loaded
# directly into TRCH SRAM by Qemu's ELF loader on machine startup
TRCH_APP_LOAD=(-device "loader,file=${TRCH_APP},cpu-num=0")

# The following two are used only for developer-friendly boot mode in which
# Qemu loads the images directly into DRAM upon startup of the machine (not
# possible on real HW).
BOOT_IMGS_LOAD=(
-device "loader,addr=${RTPS_BL_ADDR},file=${RTPS_BL},force-raw,cpu-num=1"
-device "loader,addr=${RTPS_APP_ADDR},file=${RTPS_APP},force-raw,cpu-num=1"
-device "loader,addr=${HPPS_BL_ADDR},file=${HPPS_BL},force-raw,cpu-num=3"
-device "loader,addr=${HPPS_FW_ADDR},file=${HPPS_FW},force-raw,cpu-num=3"
-device "loader,addr=${HPPS_DT_ADDR},file=${HPPS_DT},force-raw,cpu-num=3"
-device "loader,addr=${HPPS_KERN_ADDR},file=${HPPS_KERN},force-raw,cpu-num=3"
)
HPPS_RAMDISK_LOAD=(-device "loader,addr=${HPPS_RAMDISK_ADDR},file=${HPPS_RAMDISK},force-raw,cpu-num=3")

# Non-volatile memory (modeled by persistent files on the host machine)
HPPS_NAND_DRIVE=(-drive "file=$HPPS_NAND_IMAGE,if=pflash,format=raw,index=3")
HPPS_SRAM_DRIVE=(-drive "file=$HPPS_SRAM_FILE,if=pflash,format=raw,index=2")
TRCH_SRAM_DRIVE=(-drive "file=$TRCH_SRAM_FILE,if=pflash,format=raw,index=0")


COMMAND=("${BASE_COMMAND[@]}")

if [ "${CMD}" == "nand_create" ]
then
   BOOT_IMAGE_OPTION="dram"
   HPPS_ROOTFS_OPTION="dram"
   OPT_COMMAND=("${HPPS_NAND_DRIVE[@]}")
fi
COMMAND+=("${OPT_COMMAND[@]}")

if [ "${BOOT_IMAGE_OPTION}" == "dram" ]    # Boot images are loaded onto DRAM by Qemu
then
    OPT_COMMAND=("${BOOT_IMGS_LOAD[@]}")
    TRCH_BOOT_MODE="${TRCH_BOOT_MODE_DRAM}"
elif [ "${BOOT_IMAGE_OPTION}" == "nvram" ]  # Boot images are stored in an NVRAM and loaded onto DRAM by TRCH
then
    create_nvsram_image
    OPT_COMMAND=("${TRCH_SRAM_DRIVE[@]}")
    TRCH_BOOT_MODE="${TRCH_BOOT_MODE_SRAM}"
fi
COMMAND+=("${OPT_COMMAND[@]}")

if [ "${HPPS_ROOTFS_OPTION}" == "dram" ]    # HPPS rootfs is loaded onto DRAM by Qemu, volatile
then
    OPT_COMMAND=("${HPPS_RAMDISK_LOAD[@]}")
    HPPS_BOOT_MODE=${HPPS_BOOT_MODE_DRAM}
elif [ "${HPPS_ROOTFS_OPTION}" == "nand" ]    # HPPS rootfs is stored in an Nand, non-volatile
then
    OPT_COMMAND=("${HPPS_NAND_DRIVE[@]}")
    HPPS_BOOT_MODE=${HPPS_BOOT_MODE_NAND}
fi
COMMAND+=("${OPT_COMMAND[@]}")

# Not selectable by a command line argument yet
RTPS_BOOT_MODE="${RTPS_BOOT_LOCKSTEP}"

# Storing boot configuration files for TRCH and for RTPS/HPPS bootloaders on NV
# mem is not yet supported, so boot config flags are set by Qemu in designated
# DRAM locations on machine startup, and read by TRCH or RTPS/HPPS bootloaders.
# Note: RTPS boot mode is communicated to TRCH, hence cpu-num is 0
BOOT_CFG_LOAD=(
-device "loader,addr=${TRCH_BOOT_MODE_ADDR},data=${TRCH_BOOT_MODE},data-len=4,cpu-num=0"
-device "loader,addr=${RTPS_BOOT_MODE_ADDR},data=${RTPS_BOOT_MODE},data-len=4,cpu-num=0"
-device "loader,addr=${HPPS_BOOT_MODE_ADDR},data=${HPPS_BOOT_MODE},data-len=4,cpu-num=3"
)
COMMAND+=("${BOOT_CFG_LOAD[@]}")

COMMAND+=("${TRCH_APP_LOAD[@]}")

if [ "${CMD}" == "run" ]
then
    echo "Final Command (one arg per line):"
    for arg in ${COMMAND[*]}
    do
        echo $arg
    done
    echo

    echo "Final Command:"
    echo "${COMMAND[*]}"
    echo
fi

function finish {
    if [ -n "$GDB_CMD_FILE" ]
    then
        rm "$GDB_CMD_FILE"
    fi
}
trap finish EXIT

# Make it so!
"${COMMAND[@]}"
