# fs-errors

~~~
make pread
sudo python3 main.py images/ext4.img.gz deafbf8b0e316d82adad16b42975f24d
~~~

This repo contains tooling for injecting errors into filesystems using device-mapper.

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

TODO(Wesley) more details

## Notes

Procedure to get error offset:

Each filesystem contains `test.txt`. `test.txt` contains Lorem ipsum text (see images/text.txt).

In the case of the -largefile images, `test.txt` contains the letters of the alphabet repeated enough to make 8K of text. See `images/large_test.txt`.

To find the error offset for a new filesystem, you can open the file up in a hex editor, find the byte offset, and divide the byte offset by 512.
