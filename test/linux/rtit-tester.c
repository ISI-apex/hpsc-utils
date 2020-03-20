#include <stdio.h>
#include <errno.h>
#include <string.h>
#include <stdint.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>

#define TIMEOUT_DELTA_MS 1000

static void usage(const char *prog)
{
    fprintf(stderr, "%s /dev/rti_timer[0-7] [interval_ms]\n", prog);
    fprintf(stderr, "\tNOTE: program must be pinned to a CPU (run via 'taskset')\n");
}

int main(int argc, char **argv)
{
    if (!(argc == 2 || argc == 3)) {
        fprintf(stderr, "error: invalid arguments\n");
        usage(argv[0]);
        return 1;
    }
    const char *devpath = argv[1];
    unsigned interval_ms = argc == 3 ? atol(argv[2]) : 3000;
    int fd = open(devpath, O_RDWR | O_NONBLOCK);
    if (!fd) {
        fprintf(stderr, "error: failed to open '%s': %s\n",
                devpath, strerror(errno));
        return 2;
    }
    uint64_t interval_ns = interval_ms * 1000000;
    printf("interval <- %u ms\n", interval_ms);
    int rc = write(fd, &interval_ns, sizeof(interval_ns));
    if (rc != sizeof(interval_ns)) {
        fprintf(stderr, "error: failed to set interval: %s: %s\n",
                devpath, strerror(errno));
        return 3;
    }

    struct timeval timeout = {
        .tv_sec = interval_ms / 1000 + TIMEOUT_DELTA_MS / 1000,
        .tv_usec = (interval_ms % 1000 + TIMEOUT_DELTA_MS % 1000) * 1000
    };

    int events = 0;
    fd_set fds;
    FD_ZERO(&fds);
    FD_SET(fd, &fds);
    do {
        printf("waiting %u ms for event with select()...\n", interval_ms);
        struct timeval to = timeout;
        int rc = select(fd + 1, &fds, NULL, NULL, &to);
        if (rc < 0) {
            fprintf(stderr, "error: select failed: %s\n", strerror(errno));
            return 4;
        }
        if (rc == 0) {
            fprintf(stderr, "error: wait timed out after %lu ms\n",
                    timeout.tv_sec * 1000 + timeout.tv_usec / 1000);
            return 5;
        }
        printf("event: %u\n", events);
    } while (events++ < 3);

    rc = close(fd);
    if (rc) {
        fprintf(stderr, "error: close failed: %s\n", strerror(errno));
        return 6;
    }

    printf("test completed successfully\n");
    return 0;
}
