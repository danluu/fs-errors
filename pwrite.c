#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

int main(int argc, char *argv[]) {
  if (argc != 2) {
    printf("Expected 1 argument (filename), found %d\n", argc-1);
    return 1;
  }

  char buf[1024] = {0};

  int fd = open(argv[1], O_WRONLY);
  if (fd < 0) {
    printf("open fail %s\n", strerror(errno));
    return fd;
  }

  ssize_t rcode = pwrite(fd, &buf, 100, 0);
  if (rcode < 0) {
    printf("write fail. errno: %s\n", strerror(errno));
    return rcode;
  } else {
    return 0;
  }
}
