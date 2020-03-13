#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/mman.h>

#define FILEPATH "/tmp/mmapped.bin"
#define NUMINTS  (1024)
#define FILESIZE (NUMINTS * sizeof(int))
#define SRAM_ADDR 0x600000000
#define READ_ONLY 1

int main()
{
    int i;
    int fd;
    int *map;  /* mmapped array of int's */
    off_t addr;
    int prot = PROT_READ | (!(READ_ONLY) ? PROT_WRITE : 0);
#if !READ_ONLY
    int buf[NUMINTS];
    int error;
#endif /* !READ_ONLY */

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
#if !READ_ONLY
        buf[i] = map[i];
#endif /* !READ_ONLY */
    }
    printf("\n");

#if !READ_ONLY
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
#endif /* !READ_ONLY */

    if (munmap(map, FILESIZE) == -1) {
      perror("Error un-mmapping the file");
      /* Decide here whether to close(fd) and exit() or not. Depends... */
    }
    close(fd);

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
    return 0;
}


