#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <linux/watchdog.h>

static volatile int running = 1;

static void shandle(int sig) {
    switch (sig) {
        case SIGTERM:
        case SIGINT:
            running = 0;
        default:
            break;
    }
}

static void print_ioctl_int(int fd, int request, const char* name)
{
    int val;
    if (ioctl(fd, request, &val))
        fprintf(stderr, "  %s: %s\n", name, strerror(errno));
    else
        printf("  %s: %d\n", name, val);
}

static void print_ioctls(int fd)
{
    printf("ioctls:\n");
    // read int-type ioctls (see linux/watchdog.h)
    print_ioctl_int(fd, WDIOC_GETSTATUS, "WDIOC_GETSTATUS");
    print_ioctl_int(fd, WDIOC_GETBOOTSTATUS, "WDIOC_GETBOOTSTATUS");
    print_ioctl_int(fd, WDIOC_GETTEMP, "WDIOC_GETTEMP");
    print_ioctl_int(fd, WDIOC_KEEPALIVE, "WDIOC_KEEPALIVE");
    print_ioctl_int(fd, WDIOC_GETTIMEOUT, "WDIOC_GETTIMEOUT");
    print_ioctl_int(fd, WDIOC_GETPRETIMEOUT, "WDIOC_GETPRETIMEOUT");
    print_ioctl_int(fd, WDIOC_GETTIMELEFT, "WDIOC_GETTIMELEFT");
}

int main(int argc, char** argv) {
    int fd;
    int do_write;
    const char* fname;
    if (argc < 3) {
        fprintf(stderr, "Usage: %s <device_file> <do_writes>\n", argv[0]);
        return EINVAL;
    }
    fname = argv[1];
    do_write = atoi(argv[2]);
    signal(SIGINT, shandle);
    if ((fd = open(fname, O_WRONLY | O_CLOEXEC)) < 0) {
        perror(fname);
        return errno;
    }
    print_ioctls(fd);
    while (running) {
        if (do_write) {
            printf("Kicking watchdog: yes\n");
            fflush(stdout);
            if (write(fd, "\0", 1) < 0) {
                perror("write");
            }
        } else {
            printf("Kicking watchdog: no\n");
            fflush(stdout);
        }
        sleep(2);
    }
    printf("Stopping\n");
    fflush(stdout);
    if (write(fd, "V", 1) < 0) {
        perror("write: failed to stop");
        return errno;
    }
    if (close(fd) == -1) {
        perror("close");
        return errno;
    }
    return 0;
}
