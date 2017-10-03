#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#define SIZE 1024

int main(int argc, char *argv[]) {
  if (argc != 2) {
    printf("Expected 1 argument, found %d\n", argc-1);
    return 1;
  }

  char buf[SIZE];

  int fd = open(argv[1], O_RDONLY);
  if (fd < 0) {
    printf("open fail %s\n", strerror(errno));
    return fd;
  }

  ssize_t rcode = pread(fd, &buf, SIZE, 0);
  buf[SIZE-1] = '\0';

  printf("%s", buf);
  if (rcode < 0) {
    printf("read fail %s\n", strerror(errno));
    return rcode;
  } else {
    return 0;
  }
}
