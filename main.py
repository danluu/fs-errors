#!/usr/bin/python

import hashlib, shutil, tempfile, subprocess, os, time, argparse

parser = argparse.ArgumentParser(description="Mount filesystem using dmsetup and run test programs.")
parser.add_argument("image_file")
parser.add_argument("md5sum")

args = parser.parse_args()

filesystem_image = args.image_file
filesystem_md5sum = args.md5sum
error_block = (2389,1) #TODO(Wesley) multi-section errors

# Check for root

if os.geteuid() != 0:
    print("You must be root to use this script")
    exit(1)

# Verify md5sum

if hashlib.md5(open(filesystem_image, 'rb').read()).hexdigest() != filesystem_md5sum:
    print("md5sum for filesystem image does not match")
    exit(1)

# Make copy of file
# This is done so that if any of the operations on the file done in this script
# are destructive they will not destroy the original file.

filesystem_file = tempfile.mkstemp()[1]
shutil.copyfile(filesystem_image, filesystem_file)

# make loopback device

losetup_result = subprocess.run("losetup -f".split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
if losetup_result.returncode != 0:
    print("Error finding unused loopback file:")
    print(losetup_result.stderr)
    exit(1)

loopback_name = losetup_result.stdout.strip()

# Possible TOCTOU issue here but it's basically impossible to avoid while using
# the losetup command line tool

losetup_result = subprocess.run(["losetup", loopback_name, filesystem_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

if losetup_result.returncode != 0:
    print("Error finding setting up loopback file:")
    print(losetup_result.stderr)
    exit(1)

# Find device size (in sectors)

device_size_result = subprocess.run(["blockdev", "--getsize", loopback_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

if device_size_result.returncode != 0:
    print("Error getting size of block device")
    print(device_size_result.stderr)

device_size = int(device_size_result.stdout.strip())

# Calculate dmsetup table

dm_table = """\
0 {error_start} linear /dev/loop0 0
{error_start} {error_size} error
{linear_start} {linear_end_size} linear /dev/loop0 {linear_start}""".format(
        error_start=error_block[0],
        error_size=error_block[1],
        linear_start=sum(error_block),
        linear_end_size=device_size-sum(error_block))

# Run dmsetup

dm_volume_name = "fserror_test_{}".format(time.time())
dm_command = subprocess.Popen(["dmsetup", "create", dm_volume_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
dm_command_output = dm_command.communicate(str.encode(dm_table))

if dm_command.returncode != 0:
    print("Error setting up device-mapper volume")
    print(dm_command_output[1])
    exit(1)

# Mount dm-mapped device

mountpoint = "/mnt/{}/".format(dm_volume_name)
os.makedirs(mountpoint, exist_ok=True)

mount_result = subprocess.run(["mount", "/dev/mapper/{}".format(dm_volume_name), mountpoint], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

if mount_result.returncode != 0:
    print("Error mounting volume")
    print(mount_result.stderr)
    exit(1)

test_file = mountpoint + "test.txt"
# Run test programs
# TODO: make sure binary is built.
test_result = subprocess.run(["./pread", "{}".format(test_file)])
print(test_result)

subprocess.run(["umount", mountpoint], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
subprocess.run(["dmsetup", "remove", dm_volume_name])
subprocess.run(["losetup", "-d", loopback_name])
os.remove(filesystem_file)
