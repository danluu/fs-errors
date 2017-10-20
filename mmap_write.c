#include <errno.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <sys/mman.h>
#include <sys/types.h>
#include <fcntl.h>

#define SIZE 445

int main(int argc, char *argv[])
{
  char *memblock;
  int fd;

  if (argc != 2) {
    printf("Expected 1 argument (filename), found %d\n", argc-1);
    return 1;
  }

  fd = open(argv[1], O_RDONLY);
  if (fd < 0) {
    printf("open fail %s\n", strerror(errno));
    return fd;
  }

  memblock = mmap(NULL, SIZE, PROT_WRITE, MAP_PRIVATE, fd, 0);
  if (memblock == MAP_FAILED) {
    perror("mmap");
    return 2;
  }

  memblock[0] = '\0';
  // Without use of this call there is no guarantee that changes are
  // written back before munmap(2) is called  
  if (msync(memblock, 1, MS_SYNC)) {
    perror("msync");
    return 3;
  }

  if (munmap(memblock, SIZE)) {
    perror("munmap");
    return 4;
  }
  return 0;
}
