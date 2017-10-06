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
    printf("Expected 1 argument (filename), found %d\n", argc-1);
    return 1;
  }

  // char buf[SIZE];
  char c;

  int fd = open(argv[1], O_RDONLY);
  if (fd < 0) {
    printf("open fail %s\n", strerror(errno));
    return fd;
  }

  int saved_errno;
  ssize_t saved_rcode;
  for (int i = 0; i < SIZE; ++i) {
    ssize_t rcode = pread(fd, &c, 1, i);
    // char expect = (i % 16) + 'a';
    if (rcode < 0) {
      error_seen = 1;
      saved_errno = errno;
      saved_rcode = rcode;
      // printf("%d,%zd,%c,%c\n", i, rcode, expect, c);
    }
    // if (expect != c) {
    //   error_seen = 1;
    // }
  }

  // TODO: consider tracking more than one error.
  if (error_seen) {
    printf("read fail. errno: %s\n", strerror(saved_errno));
    return saved_rcode;
  } else {
    return 0;
  }
}
