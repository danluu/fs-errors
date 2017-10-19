#include <errno.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <sys/mman.h>
#include <sys/types.h>
#include <fcntl.h>

#define SIZE 7999

int main(int argc, char *argv[])
{
  const char *memblock;
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

  char c;
  for(uint64_t i = 0; i < SIZE; i++)
  {
    c = memblock[i]; // Make sure to compile with -O0
    /*printf("%c", memblock[i]);*/
  }
  printf("\n");
  return 0;
}
