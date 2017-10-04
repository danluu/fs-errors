#!/usr/bin/python

import argparse
import hashlib
import shutil
import subprocess
import tempfile
import time
import os

def exec_command(command, exit_on_error=True):
    print(command)
    command_result = subprocess.run(command,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
    if command_result.returncode != 0 and exit_on_error:
        print("Error running {}".format(command))
        print(command_result.stderr)
        exit(1)

    return command_result

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

    gzip_command = "gunzip -f {}".format(gzip_path).split()
    exec_command(gzip_command)

    verify_md5sum(tmp_image_path, filesystem_md5sum)
    return tmp_image_path


# make loopback device
def make_loopback_device(tmp_image_path):
    losetup_command_1 = "losetup -f".split()
    losetup_result = exec_command(losetup_command_1)

    loopback_name = losetup_result.stdout.strip().decode('utf-8')

    # Possible TOCTOU issue here but it's basically impossible to avoid while using
    # the losetup command line tool

    losetup_command_2 = ["losetup",
                         loopback_name,
                         tmp_image_path]
    exec_command(losetup_command_2)

    return loopback_name

# Find device size (in sectors)
def get_device_size(loopback_name):
    device_size_result = exec_command(["blockdev",
                                       "--getsize",
                                       loopback_name])

    device_size = int(device_size_result.stdout.strip())
    return device_size


# Calculate dmsetup table
def get_dmsetup_table(device_size, loop_name, error_block):
    dm_table = """\
    0 {error_start} linear {loop_name} 0
    {error_start} {error_size} error
    {linear_start} {linear_end_size} linear {loop_name} {linear_start}""".format(
        error_start=error_block[0],
        loop_name=loop_name,
        error_size=error_block[1],
        linear_start=sum(error_block),
        linear_end_size=device_size-sum(error_block))

    print(dm_table)
    return dm_table

# Run dmsetup
def run_dmsetup(dm_table):
    dm_volume_name = "fserror_test_{}".format(time.time())
    # TODO: should work with exec_command.
    dm_command = ["dmsetup",
                  "create",
                  dm_volume_name]
    print(dm_command)
    dm_subprocess = subprocess.Popen(dm_command,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     stdin=subprocess.PIPE)
    dm_command_output = dm_subprocess.communicate(str.encode(dm_table))

    if dm_subprocess.returncode != 0:
        print("Error setting up device-mapper volume")
        print(dm_command_output[1])
        exit(1)

    return dm_volume_name

# Mount dm-mapped device
def mount_dm_device(dm_volume_name):
    mountpoint = "/mnt/{}/".format(dm_volume_name)
    os.makedirs(mountpoint, exist_ok=True)

    exec_command(["mount",
                  "/dev/mapper/{}".format(dm_volume_name),
                  mountpoint])

    return mountpoint

def exec_test(mountpoint, image_path):
    test_file = mountpoint + "test.txt"
    # Run test programs
    # TODO: make sure binary is built.
    test_result = exec_command(["./pread",
                                "{}".format(test_file)],
                               False)
    # TODO: use csv library
    # TODO: put result into output file.
    print("{},{},{},{}".format(image_path,
                               test_result.returncode,
                               test_result.stdout.decode('utf-8').strip(),
                               test_result.stderr.decode('utf-8').strip()))

def main():
    image_path, filesystem_md5sum = get_args()
    error_block = (2392, 1) #TODO(Wesley) multi-section errors

    tmp_image_path = make_tmpfile(image_path, filesystem_md5sum)
    loopback_name = make_loopback_device(tmp_image_path)
    device_size = get_device_size(loopback_name)
    dm_table = get_dmsetup_table(device_size, loopback_name, error_block)
    dm_volume_name = run_dmsetup(dm_table)
    mountpoint = mount_dm_device(dm_volume_name)
    exec_test(mountpoint, image_path)

    # TODO: unmount, remove, etc., when an error occurs and the script terminates early.
    exec_command(["umount", mountpoint])
    exec_command(["dmsetup", "remove", dm_volume_name])
    exec_command(["losetup", "-d", loopback_name])
    os.remove(tmp_image_path)

main()
