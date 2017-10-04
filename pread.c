#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#define SIZE 7999

int main(int argc, char *argv[]) {
  int error_seen = 0;

  if (argc != 2) {
    printf("Expected 1 argument, found %d\n", argc-1);
    return 1;
  }

  // char buf[SIZE];
  char c;

  int fd = open(argv[1], O_RDONLY);
  if (fd < 0) {
    printf("open fail %s\n", strerror(errno));
    return fd;
  }

  for (int i = 0; i < SIZE; ++i) {
    ssize_t rcode = pread(fd, &c, 1, i);
    char expect = (i % 16) + 'a';
    if (rcode < 0 || expect != c) {
      error_seen = 1;
      printf("%d,%c,%c\n", i, expect, c);
    }
  }

  // buf[SIZE-1] = '\0';

  // printf("%s", buf);
  if (error_seen) {
    // TODO: move errno extraction up.
    printf("read fail %s\n", strerror(errno));
    return -1;
  } else {
    return 0;
  }
}
