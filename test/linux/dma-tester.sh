#!/bin/bash
#
# Test DMAs using 'dmatest' kernel module.
# The kernel module must be loaded or built-in for these tests to pass.
#

# returns 1 if the parameter is invalid, else returns 0
function parameter_is_invalid() {
    local parameter=$1
    local value=$2

    local msg=$( (echo $value > $parameter) 2>&1 )
    for s in $msg; do
        # check for write error
        if [ "$s" == "write" ]; then
            return 1
        fi
    done
    return 0
}

# checks the DMA's dmesg summary output which contains the string
# "N failures" for some value of N.  This will exit if N > 0 or if
# there is no summary line.  Otherwise, will return 0.
function dma_failures_occurred() {
    # summary contains the string "N failures" for some value N
    local summary=$1
    local last=""
    for s in $summary; do
        if [ "$s" == "failures" ]; then
            if [ "$last" == "0" ]; then
                return 0
            else
                # fail if there are more than 0 failures in the summary line
                exit 6
            fi
        fi
        last=$s
    done
    
    # fail if there is no summary line (perhaps empty string?)
    exit 5
}

function dma_test() {
    local chan=$1

    echo $chan > /sys/module/dmatest/parameters/channel
    local dmesg_a=$(dmesg | tail -n $DMESG_BUF_LEN)

    # start the test (returns immediately)
    echo 1 > /sys/module/dmatest/parameters/run

    # get only new lines in dmesg - ignore lines unrelated to dmatest and those
    # that fell out of buffer range (from earlier tests)
    local dmesg_b=$(dmesg | tail -n $DMESG_BUF_LEN)
    local dmesg_new=$(diff <(echo "$dmesg_a") <(echo "$dmesg_b") -U 0 |
                      grep "dmatest" | grep -E "^\+\[" | cut -c2-)
    dma_failures_occurred "$(echo "$dmesg_new" | grep "summary")"
}

function usage() {
    printf "Usage: $0 [-b TEST_BUF_SIZE] [-T THREADS_PER_CHAN] [-i ITERATIONS] [-t TIMEOUT] [-c CHANNEL] [-h]\n"
    printf "    -b TEST_BUF_SIZE: size in bytes of the memcpy test buffer for running dmatest (default: 16384)\n"
    printf "    -T THREADS_PER_CHAN: number of threads to start per channel for running dmatest (default: 1)\n"
    printf "    -i ITERATIONS: iterations before stopping dmatest (default: 1)\n"
    printf "    -t TIMEOUT: transfer timeout in msec for dmatest (default: 3000)\n"
    printf "    -c CHANNEL: bus ID of the channel for running dmatest (default: all available)\n"
    printf "    -h: show this message and exit\n"
}

DMESG_BUF_LEN=50 # about 10x what we should need, but room for other messages
DEFAULT_TEST_BUF_SIZE=16384 # in Bytes
DEFAULT_THREADS_PER_CHAN=1
DEFAULT_ITERATIONS=1
DEFAULT_TIMEOUT=3000 # in ms

while getopts "b:T:i:t:c:h?" o; do
    case "$o" in
        b) TEST_BUF_SIZE=${OPTARG};;
        T) THREADS_PER_CHAN=${OPTARG};;
        i) ITERATIONS=${OPTARG};;
        t) TIMEOUT=${OPTARG};;
        c) CHANNEL=${OPTARG};;
        h) usage
           exit 0;;
        *) echo "Unknown option"
           usage >&2
           exit 1;;
    esac
done

# set default value for TEST_BUF_SIZE
if [[ -z "${TEST_BUF_SIZE}" ]]; then
    TEST_BUF_SIZE=${DEFAULT_TEST_BUF_SIZE}
fi

# set default value for THREADS_PER_CHAN
if [[ -z "${THREADS_PER_CHAN}" ]]; then
    THREADS_PER_CHAN=${DEFAULT_THREADS_PER_CHAN}
fi

# set default value for ITERATIONS
if [[ -z "${ITERATIONS}" ]]; then
    ITERATIONS=${DEFAULT_ITERATIONS}
fi

# set default value for TIMEOUT
if [[ -z "${TIMEOUT}" ]]; then
    TIMEOUT=${DEFAULT_TIMEOUT}
fi

printf "\ntest_buf_size=${TEST_BUF_SIZE}, threads_per_chan=${THREADS_PER_CHAN}, iterations=${ITERATIONS}, timeout=${TIMEOUT}\n"

# check dmatest parameters- should fail immediately if dmatest isn't available
param=(/sys/module/dmatest/parameters/test_buf_size \
       /sys/module/dmatest/parameters/threads_per_chan \
       /sys/module/dmatest/parameters/iterations \
       /sys/module/dmatest/parameters/timeout)
val=(${TEST_BUF_SIZE} ${THREADS_PER_CHAN} ${ITERATIONS} ${TIMEOUT})

# check each parameter value, exit if any are invalid
for i in {0..3}
do
    parameter_is_invalid ${param[$i]} ${val[$i]}
    retval=$?
    if [ "$retval" -eq "1" ]; then
	exit $(($i + 1))
    fi
done

# Perform the DMA test.  Note: the default value for CHANNEL is
# to try all available channels
if [[ -z "${CHANNEL}" ]]; then
    for c in /sys/class/dma/*; do
        channel="$(basename "${c}")"
        echo "    channel=${channel}"
        dma_test ${channel}
    done
else
    echo "    channel=${CHANNEL}"
    dma_test ${CHANNEL}
fi

exit 0
