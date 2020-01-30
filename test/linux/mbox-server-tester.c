#define _GNU_SOURCE

#include <errno.h>
#include <fcntl.h>
#include <getopt.h>
#include <sched.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "libmbox/mbox.h"
#include "mailbox-map.h"
#include "mbox-utils.h"

#define PATH_SIZE 128

#define RTPS_PATH_IN "/dev/mbox/1/mbox4"
#define RTPS_PATH_OUT "/dev/mbox/1/mbox3"


enum mbox_notif notif_type = MBOX_NOTIF_NONE;
int timeout_ms = -1;

static const char short_options[] = "n:t:c:h";
static const struct option long_options[] = {
    {"not-type",    required_argument,  NULL,   'n'},
    {"timeout",     required_argument,  NULL,   't'},
    {"cpu",         required_argument,  NULL,   'c'},
    {"help",        no_argument,        NULL,   'h'},
    {0, 0, 0, 0}
};


static void usage(const char *pname, int code)
{
    fprintf(code ? stderr : stdout,
            "Usage: %s [-n TYPE] [-t N] [-c CPU] [-h]\n"
            "  -n, --not-type=TYPE  Notification type, one of: none, select, poll, epoll\n"
            "                       The default value is \"none\"\n"
            "  -t, --timeout=N      Timeout for reads, in milliseconds\n"
            "                       The default value is -1 (infinite timeout)\n"
            "                       Specify a positive value, or 0 for no timeout\n"
            "  -c, --cpu=CPU        Pin process to CPU\n"
            "                       The default value is -1, for no pinning\n"
            "  -h, --help           Print this message and exit\n",
            pname);
    exit(code);
}

int main(int argc, char** argv)
{
    struct mbox mbox_in;
    struct mbox mbox_out;

    int cpu = -1;

    int c;	
    while ((c = getopt_long(argc, argv, short_options, long_options, NULL)) != -1) {
        switch (c) {
        case 'n':
            if (!strcmp(optarg, "none")) {
                notif_type = MBOX_NOTIF_NONE;
            } else if (!strcmp(optarg, "select")) {
                notif_type = MBOX_NOTIF_SELECT;
            } else if (!strcmp(optarg, "poll")) {
                notif_type = MBOX_NOTIF_POLL;
            } else if (!strcmp(optarg, "epoll")) {
                notif_type = MBOX_NOTIF_EPOLL;
            } else {
                fprintf(stderr, "Unknown notification type: %s\n", optarg);
                usage(argv[0], EINVAL);
            }
            break;
        case 't':
            timeout_ms = atoi(optarg);
            break;
        case 'c':
            cpu = atoi(optarg);
            break;
        case 'h':
            usage(argv[0], 0);
            break;
        default:
            usage(argv[0], EINVAL);
            break;
        }
    }

    if (cpu >= 0) {
        // pin to core
        cpu_set_t cpumask;
        CPU_ZERO(&cpumask);
        CPU_SET(cpu, &cpumask);
        sched_setaffinity(0 /* i.e. self */, sizeof(cpu_set_t), &cpumask);
    }

    mbox_open_or_die(&mbox_in, RTPS_PATH_IN, notif_type, timeout_ms, O_RDONLY);
    mbox_open_or_die(&mbox_out, RTPS_PATH_OUT, notif_type, timeout_ms, O_RDWR);

    int rc = mboxtester_read(&mbox_in);

    if (rc < 0) {
        perror("mboxtester_read: link: mbox_in");
        rc = errno;
        goto cleanup;
    }

    printf("%s\n",mbox_in.data.bytes);

    memcpy(mbox_out.data.bytes, mbox_in.data.bytes, //copy over the PING payload onto the PONG
               sizeof(mbox_out.data.bytes));

    mbox_out.data.bytes[0] = CMD_PONG;

    rc = mboxtester_write_ack(&mbox_out);

    if (rc < 0) {
        perror("mboxtester_write_ack: link: mbox_out");
        rc = errno;
        goto cleanup;
    }

cleanup:
    mbox_close(&mbox_in);
    mbox_close(&mbox_out);
    return rc;
}

