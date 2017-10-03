#!/usr/bin/python

import argparse
import hashlib
import shutil
import subprocess
import tempfile
import time
import os

def get_args():
    # Check for root
    if os.geteuid() != 0:
        print("You must be root to use this script")
        exit(1)


    parser = argparse.ArgumentParser(description=
                                     "Mount filesystem using dmsetup and run test programs.")
    parser.add_argument("image_file")
    parser.add_argument("md5sum")

    args = parser.parse_args()
    return args.image_file, args.md5sum

# Verify md5sum
def verify_md5sum(image_path, filesystem_md5sum):
    if hashlib.md5(open(image_path, 'rb').read()).hexdigest() != filesystem_md5sum:
        print("md5sum for filesystem image does not match")
        exit(1)

# Make copy of file
# This is done so that if any of the operations on the file done in this script
# are destructive they will not destroy the original file.
def make_tmpfile(image_path, filesystem_md5sum):
    tmp_image_path = tempfile.mkstemp()[1]
    gzip_path = tmp_image_path + ".gz"
    shutil.copyfile(image_path, gzip_path)

    gzip_result = subprocess.run("gunzip -f {}".format(gzip_path).split())

    # TODO: check for error.

    verify_md5sum(tmp_image_path, filesystem_md5sum)
    return tmp_image_path


# make loopback device
def make_loopback_device(tmp_image_path):
    losetup_result = subprocess.run("losetup -f".split(),
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)

    if losetup_result.returncode != 0:
        print("Error finding unused loopback file:")
        print(losetup_result.stderr)
        exit(1)

    loopback_name = losetup_result.stdout.strip()

    # Possible TOCTOU issue here but it's basically impossible to avoid while using
    # the losetup command line tool

    losetup_result = subprocess.run(["losetup",
                                     loopback_name,
                                     tmp_image_path],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)

    if losetup_result.returncode != 0:
        print("Error setting up loopback file:")
        print(losetup_result.stderr)
        exit(1)

    return loopback_name

# Find device size (in sectors)
def get_device_size(loopback_name):
    device_size_result = subprocess.run(["blockdev",
                                         "--getsize",
                                         loopback_name],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)

    if device_size_result.returncode != 0:
        print("Error getting size of block device")
        print(device_size_result.stderr)

    device_size = int(device_size_result.stdout.strip())
    return device_size


# Calculate dmsetup table
def get_dmsetup_table(device_size, error_block):
    dm_table = """\
    0 {error_start} linear /dev/loop0 0
    {error_start} {error_size} error
    {linear_start} {linear_end_size} linear /dev/loop0 {linear_start}""".format(
        error_start=error_block[0],
        error_size=error_block[1],
        linear_start=sum(error_block),
        linear_end_size=device_size-sum(error_block))

    return dm_table

# Run dmsetup
def run_dmsetup(dm_table):
    dm_volume_name = "fserror_test_{}".format(time.time())
    dm_command = subprocess.Popen(["dmsetup",
                                   "create",
                                   dm_volume_name],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  stdin=subprocess.PIPE)
    dm_command_output = dm_command.communicate(str.encode(dm_table))

    if dm_command.returncode != 0:
        print("Error setting up device-mapper volume")
        print(dm_command_output[1])
        exit(1)

    return dm_volume_name

# Mount dm-mapped device
def mount_dm_device(dm_volume_name):
    mountpoint = "/mnt/{}/".format(dm_volume_name)
    os.makedirs(mountpoint, exist_ok=True)

    mount_result = subprocess.run(["mount",
                                   "/dev/mapper/{}".format(dm_volume_name),
                                   mountpoint],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)

    if mount_result.returncode != 0:
        print("Error mounting volume")
        print(mount_result.stderr)
        exit(1)

    return mountpoint

def exec_test(mountpoint, image_path):
    test_file = mountpoint + "test.txt"
    # Run test programs
    # TODO: make sure binary is built.
    test_result = subprocess.run(["./pread",
                                  "{}".format(test_file)],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
    # TODO: use csv library
    # TODO: put result into output file.
    print("{},{},{},{}".format(image_path,
                               test_result.returncode,
                               test_result.stdout.decode('utf-8').strip(),
                               test_result.stderr.decode('utf-8').strip()))

def main():
    image_path, filesystem_md5sum = get_args()
    error_block = (2389, 1) #TODO(Wesley) multi-section errors

    tmp_image_path = make_tmpfile(image_path, filesystem_md5sum)
    loopback_name = make_loopback_device(tmp_image_path)
    device_size = get_device_size(loopback_name)
    dm_table = get_dmsetup_table(device_size, error_block)
    dm_volume_name = run_dmsetup(dm_table)
    mountpoint = mount_dm_device(dm_volume_name)
    exec_test(mountpoint, image_path)

    # TODO: unmount, remove, etc., when an error occurs and the script terminates early.
    subprocess.run(["umount", mountpoint], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.run(["dmsetup", "remove", dm_volume_name])
    subprocess.run(["losetup", "-d", loopback_name])
    os.remove(tmp_image_path)

main()
