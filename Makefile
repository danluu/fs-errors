mmap_read: mmap_read.c
	gcc -o mmap_read mmap_read.c -O0 -I.

pread: pread.c
	gcc -o pread pread.c -O0 -I.

pwrite: pwrite.c
	gcc -o pwrite pwrite.c -O0 -I.

all: pread pwrite mmap_read
