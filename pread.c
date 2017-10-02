#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

int main() {
  char* filename = "test.txt";
  char buf[1024];

  int fd = open(filename, O_RDONLY);
  if (fd < 0) {
    printf("open fail %s\n", strerror(errno));
    return fd;
  }

  ssize_t rcode = pread(fd, &buf, 100, 0);
  if (rcode < 0) {
    printf("read fail %s\n", strerror(errno));
    return rcode;
  } else {
    return 0;
  }
}
