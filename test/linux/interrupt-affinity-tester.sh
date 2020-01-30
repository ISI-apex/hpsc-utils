#!/bin/bash
#
# In this test, the DMA controller interrupt is assigned to each
# HPPS CPU in order to test interrupt affinity.  The 'dmatest' kernel
# module must be loaded or built-in for these tests to pass.
#

DMESG_BUF_LEN=50 # about 10x what we should need, but room for other messages

# returns the first listed DMA channel
function get_first_dma_channel() {
    local all_dma_channels=$(ls /sys/class/dma/ | tr -s " ")
    all_dma_channels_arr=($all_dma_channels)
    echo ${all_dma_channels_arr[0]}
}

# returns name of DMA controller for specified channel
function get_dma_controller_for_channel() {
    local chan=$1

    local file_info_segments=$(ls -l /sys/class/dma/${chan} | tr "/" "\n")
    for segment in $file_info_segments
    do
	if [[ $segment == *"dma-controller"* ]]; then
	    echo $segment
	    return 0
	fi
    done
    return 1
}

# returns the second irq number for specified DMA controller
function get_irq_from_dma_controller() {
    local dma_controller=$1
    local interrupt_info=$(grep ${dma_controller} /proc/interrupts | tr -s " ")
    IFS=$'\n'
    # split into array
    interrupt_info_arr=($interrupt_info)
    # grab last element of array
    irq_line=${interrupt_info_arr[ (( ${#interrupt_info_arr[@]} - 1 )) ]}
    irq_num=$(echo ${irq_line} | cut -d ":" -f 1 | tr -d '[:space:]')
    echo $irq_num
}

# returns the number of interrupts for the specified irq_num and cpu_num (from /proc/interrupts)
function get_num_interrupts()
{
    local irq_num=$1
    local cpu_num=$2
    local num_interrupts=$(cat /proc/interrupts | grep "${irq_num}:" | tr -s " " | cut -d " " -f $((cpu_num + 3)) )
    echo $num_interrupts
}

function check_dma_failures()
{
    # summary contains the string "N failures" for some value N
    local summary=$1
    local last=""
    for s in $summary; do
        if [ "$s" == "failures" ]; then
            [ "$last" == "0" ] && return || return 1
        fi
        last=$s
    done
    return 1 # no summary line (empty string)?
}

function do_dma_on_specified_channel()
{
    local chan=$1

    # ensure proper dmatest functionality by setting important parameters
    echo 16384 > /sys/module/dmatest/parameters/test_buf_size
    echo 1 > /sys/module/dmatest/parameters/threads_per_chan
    echo 1 > /sys/module/dmatest/parameters/iterations
    echo 3000 > /sys/module/dmatest/parameters/timeout
    echo "$chan" > /sys/module/dmatest/parameters/channel
    local dmesg_a=$(dmesg | tail -n $DMESG_BUF_LEN)

    # start the test (returns immediately)
    echo 1 > /sys/module/dmatest/parameters/run

    # get only new lines in dmesg - ignore lines unrelated to dmatest and those
    # that fell out of buffer range (from earlier tests)
    local dmesg_b=$(dmesg | tail -n $DMESG_BUF_LEN)
    local dmesg_new=$(diff <(echo "$dmesg_a") <(echo "$dmesg_b") -U 0 |
                      grep "dmatest" | grep -E "^\+\[" | cut -c2-)
    if ! check_dma_failures "$(echo "$dmesg_new" | grep "summary")"; then
        echo "dmatest failed for channel: $chan" >&2
        echo "$dmesg_new" >&2
        exit 2
    fi
}

function interrupt_affinity_test()
{
    local cpu_num=$1
    local irq_num=$2
    local dma_chan=$3

    cpu_bitmask=(01 02 04 08 10 20 40 80)
    
    old_interrupt_cnt=$(get_num_interrupts $irq_num $cpu_num)
    echo ${cpu_bitmask[$cpu_num]} > /proc/irq/${irq_num}/smp_affinity
    do_dma_on_specified_channel ${dma_chan}
    new_interrupt_cnt=$(get_num_interrupts ${irq_num} $cpu_num)
    num_new_interrupts=$((new_interrupt_cnt - old_interrupt_cnt))
    
    # verify that only one new interrupt occurred
    if (("$num_new_interrupts" != 1)); then
	echo "Interrupt affinity test failed for CPU ${cpu_num}" >&2
	exit 3
    fi
}

function usage() {
    printf "Usage: $0 [-c cpu_num] [-h]\n"
    printf "    -c cpu_num: the HPPS core number (from 0-7) for which to test interrupt affinity (default: 0)\n"
    printf "    -h: show this message and exit\n"
}

cpu_num=0
dma_channel=$(get_first_dma_channel)
dma_controller=$(get_dma_controller_for_channel ${dma_channel})
irq_num=$(get_irq_from_dma_controller ${dma_controller})

while getopts "c:h?" o; do
    case "$o" in
	c) cpu_num=${OPTARG};;
	h) usage
	   exit 0;;
	*) echo "Unknown option"
	   usage >&2
	   exit 1;;
    esac
done

printf "cpu_num=${cpu_num}\n"

# save the current smp_affinity file
orig_bitmask=$(cat /proc/irq/${irq_num}/smp_affinity)

# assign the dma controller interrupt to the chosen HPPS CPU
interrupt_affinity_test ${cpu_num} ${irq_num} ${dma_channel}

# restore the saved smp_affinity file
echo ${orig_bitmask} > /proc/irq/${irq_num}/smp_affinity
