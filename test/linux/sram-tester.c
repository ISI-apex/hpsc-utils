#include <getopt.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/mman.h>

/* This SRAM test will print and possibly modify the contents of SRAM.  In both
 * cases, SRAM will be mapped into memory using mmap and later unmapped using
 * munmap. */

#define num2str(x) str(x)
#define str(x) #x

/* CHECK THE DEVICE TREE TO SEE IF HPPS SRAM ADDRESS HAS CHANGED */
#define HPPS_SRAM0_ADDR 0x600000000
#define NUM_INTS_PER_LINE 30
#define DEFAULT_SIZE 100

/* ERROR CODES */
#define FILE_WRITE_ERROR 1
#define FILE_MMAP_ERROR 2
#define FILE_UNMMAP_ERROR 3

static void print_params(int num_ints, int is_modify) {
    if (is_modify) {
        printf("The first %d integers in SRAM will be modified, then printed.\n", num_ints);
    }
    else {
        printf("The first %d integers in SRAM will be printed.\n", num_ints);
    }
}

static void print_array(int *arr, int num_ints) {
    int i;

    for (i = 0; i < num_ints; i++) {
        printf("%d,", arr[i]);
        if ((i+1) % NUM_INTS_PER_LINE == 0) printf("\n");
    }
    printf("\n");
}

/* Modify the contents of arr by incrementing each element */
static void modify_array(int *arr, int num_ints, int increment) {
    int i;

    for (i = 0; i < num_ints; i++) {
        arr[i] = arr[i]+increment;
    }
}

/*  If we are modifying SRAM, then arr will be updated to contain
 *  the new contents of SRAM.  Otherwise, print the SRAM contents */
static int access_sram(int num_ints, int is_modify, int increment) {
    int fd;
    int file_size;
    int *map;  /* mmapped array of ints */

   /* Open a file for writing.
    *  - Creating the file if it doesn't exist.
    *  - Truncating it to 0 size if it already exists. (not really needed)
    *
    * Note: "O_WRONLY" mode is not sufficient when mmaping.
    */
    fd = open("/dev/mem", O_RDWR);
    if (fd == -1) {
        return FILE_WRITE_ERROR;
    }

    file_size = num_ints * sizeof(int);
    map = mmap(NULL, file_size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, HPPS_SRAM0_ADDR);
    if (map == MAP_FAILED) {
        close(fd);
	return FILE_MMAP_ERROR;
    }

    if (is_modify) {
	/* Modify the array to see if the changes are visible later. */
        modify_array(map, num_ints, increment);
    }

    printf("Latest SRAM contents:\n");
    print_array(map, num_ints);

    /* Now free the mmapped memory */
    if (munmap(map, file_size) == -1) {
	return FILE_UNMMAP_ERROR;
    }

    /* Un-mmaping doesn't close the file, so we do that now. */
    close(fd);
    return 0;
}

static void usage(const char *pname, int code) {
    fprintf(code ? stderr : stdout,
            "Usage: %s [-s SIZE] [-i N] [-h]\n"
            "  -s, --size=SIZE      The array size (in ints) to modify/print\n"
            "                       The default value is " num2str(DEFAULT_SIZE) "\n"
            "  -i, --increment=N    Increment the first SIZE ints in the array by N\n"
            "                       N must be an integer, but may be zero or negative\n"
            "                       Off by default\n"
            "  -h, --help           Print this message and exit\n",
            pname);
    exit(code);
}

static const char short_options[] = "s:i:h";
static const struct option long_options[] = {
    {"size",       required_argument,  NULL,   's'},
    {"increment",  required_argument,  NULL,   'i'},
    {"help",       no_argument,        NULL,   'h'},
    {0, 0, 0, 0}
};

int main(int argc, char *argv[]) {
    int c;

    // set parameter default values
    int is_modify = 0;
    int increment;
    int num_ints = DEFAULT_SIZE;
    int ret = 0;

    // parse options
    while ((c = getopt_long(argc, argv, short_options, long_options, NULL)) != -1) {
	switch(c) {
        case 's':
            num_ints = atoi(optarg);
            break;
        case 'i':
            is_modify = 1;
	    increment = atoi(optarg);
            break;
        case 'h':
            usage(argv[0], 0);
            break;
        default:
            usage(argv[0], EINVAL);
            break;
        }
    }
    if (num_ints <= 0) {
        usage(argv[0], EINVAL);
    }

    print_params(num_ints, is_modify);
    ret = access_sram(num_ints, is_modify, increment);
    return ret;
}
