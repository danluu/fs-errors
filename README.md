# fs-errors

This repo contains tooling for injecting errors into filesystems using device-mapper.

To run:
~~~
sudo python3 main.py
~~~

## Making files

~~~
dd if=/dev/zero of=filesystem.img bs=1M count=1
mkfs.<filesystem_name> filesystem.img
~~~

## Installation

~~~
sudo apt install dmsetup
~~~

Requires btrfs and exfat drivers to be installed.

## Notes to self

Procedure to get error offset:

Each filesystem contains `test.txt`. `test.txt` contains Lorem ipsum text (see images/text.txt).

In the case of the -largefile images, `test.txt` contains the letters of the alphabet repeated enough to make 8K of text. See `images/large_test.txt`.

To find the error offset for a new filesystem, you can open the file up in a hex editor, find the byte offset, and divide the byte offset by 512.

This error injection mechanism seems similar or possibly equivalent to the mechanism used in the IRON file systems paper.

md5sum correctly returns an error code of 1 if the file is corrupt in btrfs (and prints md5sum: /mnt/test/test.txt: Input/output error).
