#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/mman.h>

#define NUMINTS  (1024)
#define FILESIZE (NUMINTS * sizeof(int))
#define SRAM_ADDR 0x600000000

// TODO: These were used for NOR Flash testing on HAPS, but they
// are out of range at least for the current Qemu NOR model configuration
// (512MB?); also need to put this under cli arguments.
// #define READ_MIDDLE
// #define READ_END

int main(int argc, char **argv)
{
    int i;
    int fd;
    int *map;  /* mmapped array of int's */
    off_t addr;
    int prot;
    int buf[NUMINTS];
    int error;
    int do_writes;

    if (argc != 2) {
	fprintf(stderr, "error: invalid arguments\n");
	fprintf(stderr, "usage: [do_writes]\n");
	fprintf(stderr, "    where do_writes is 0 (read-only test) or 1\n");
	exit(1);
    }
    do_writes = atoi(argv[1]);
    prot = PROT_READ | (do_writes ? PROT_WRITE : 0);

    /* Open a file for writing.
     *  - Creating the file if it doesn't exist.
     *  - Truncating it to 0 size if it already exists. (not really needed)
     *
     * Note: "O_WRONLY" mode is not sufficient when mmaping.
     */
    fd = open("/dev/mem", O_RDWR);
    if (fd == -1) {
	perror("Error opening file for writing");
	exit(EXIT_FAILURE);
    }
    printf("open /dev/mem is fine\n");

    addr = SRAM_ADDR;
    map = mmap(NULL, FILESIZE, prot, MAP_SHARED, fd, addr);
    if (map == MAP_FAILED) {
	close(fd);
	perror("Error mmapping the file");
	exit(EXIT_FAILURE);
    }
    printf("after mmap\n");
   
    /* Now write int's to the file as if it were memory (an array of ints).
     */
 
    printf(" First read from  SRAM content @%lx\n", addr);
    for (i = 0; i < NUMINTS; ++i) {
        if (i % 64 == 0) printf("\n");
	printf("0x%X, ", map[i]);
        buf[i] = map[i];
    }
    printf("\n");

    if (do_writes) {
	printf("Now writting back ...\n");
	for (i = 0; i < NUMINTS; ++i) {
	    map[i] = map[i]+1;
	}

	printf("after memcpy\n");
	printf(" ----- New SRAM content -----");
	for (i = error = 0; i < NUMINTS; ++i) {
	    if (i % 64 == 0) printf("\n");
	    printf("0x%X, ", map[i]);
	    if (buf[i] + 1 != map[i]) error++;
	}
	printf("\n");

	if (error)
	    printf("FAIL: there are %d errors\n", error);
	else
	    printf("SUCCESS\n");
    }

    if (munmap(map, FILESIZE) == -1) {
      perror("Error un-mmapping the file");
      /* Decide here whether to close(fd) and exit() or not. Depends... */
    }
    close(fd);

#ifdef READ_MIDDLE
    fd = open("/dev/mem", O_RDWR);
    if (fd == -1) {
	perror("Error opening file for writing");
	exit(EXIT_FAILURE);
    }
    printf("second open /dev/mem is fine\n");


    addr = SRAM_ADDR + 0x1FFF000;
    map = mmap(NULL, FILESIZE, prot, MAP_SHARED, fd, addr);
    if (map == MAP_FAILED) {
	close(fd);
	perror("Error mmapping the file");
	exit(EXIT_FAILURE);
    }
    printf("after second mmap\n");

    printf(" Second read from SRAM content @%lx\n", addr);
    for (i = 0; i < NUMINTS; ++i) {
        if (i % 64 == 0) printf("\n");
        printf("0x%X, ", map[i]);
    }
    printf("\n");
    if (munmap(map, FILESIZE) == -1) {
	perror("Error un-mmapping the file");
	/* Decide here whether to close(fd) and exit() or not. Depends... */
    }
    close (fd);
#endif /* READ_MIDDLE */

#ifdef READ_END
    fd = open("/dev/mem", O_RDWR);
    if (fd == -1) {
	perror("Error opening file for writing");
	exit(EXIT_FAILURE);
    }
    printf("Third open /dev/mem is fine\n");

    addr = SRAM_ADDR + 0x1FFFF000;
    map = mmap(NULL, FILESIZE, prot, MAP_SHARED, fd, addr);
    if (map == MAP_FAILED) {
	close(fd);
	perror("Error mmapping the file");
	exit(EXIT_FAILURE);
    }
    printf("after third mmap\n");

    printf(" Third read from SRAM content @%lx\n", addr);
    for (i = 0; i < NUMINTS; ++i) {
        if (i % 64 == 0) printf("\n");
	printf("0x%X, ", map[i]);
    }
    printf("\n");

    if (munmap(map, FILESIZE) == -1) {
	perror("Error un-mmapping the file");
    }

    close(fd);
#endif /* READ_END */
    return 0;
}
