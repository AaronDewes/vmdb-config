#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2021 Aaron Dewes
#
# SPDX-License-Identifier: GPL-3.0-or-later

from array import ArrayType
import yaml
import argparse
from os import path
script_path = path.realpath(path.dirname(__file__))

parser = argparse.ArgumentParser(description='Create config file for vmdb2.')
parser.add_argument(
    "script", help="The bootstrap script to run inside the chroot")
parser.add_argument("-t", "--target", type=str, required=True,
                    default='rpi',
                    help="The target to build for. Currently supported are 'rpi' (Raspberry Pi 4 only) and 'amd64-bios'")
parser.add_argument("-o", "--output", type=str, required=True,
                    default='result.yml',
                    help="Where to store the resulting config file for vmdb2")

args = parser.parse_args()


def readFile(file: str):
    return open(file, "r").read()


def optimizeSteps(steps: ArrayType):
    returnVal = []
    for step in steps:
        step["unless"] = "rootfs_unpacked"
        returnVal.append(step)
    return returnVal


cleanup_target = yaml.safe_load(
    readFile(path.join(script_path, "targets", "generic", "cleanup.yml")))
prepare_target = yaml.safe_load(
    readFile(path.join(script_path, "targets", "generic", "prepare.yml")))
try:
    hw_target = yaml.safe_load(readFile(
        path.join(script_path, "targets", "hw", "{}.yml".format(args.target))))
except:
    print("Error: Target not supported")
    exit(1)

try:
    readFile(path.realpath(args.script))
except:
    print("Error: Couldn't find bootstrap script")
    exit(1)

computed_result: dict = {}
final_steps: ArrayType = hw_target["create_img"]
final_steps.append({"unpack-rootfs": "/"})
final_steps.extend(optimizeSteps(prepare_target["steps"]))
final_steps.extend(optimizeSteps(hw_target["pre_cache"]))
final_steps.append({"cache-rootfs": "/", "unless": "rootfs_unpacked"})
final_steps.extend(optimizeSteps(hw_target["post_cache"]))
final_steps.extend(optimizeSteps([{"copy-file": "/bootstrap.sh", "src": path.realpath(
    args.script)}, {"chroot": "/", "shell": "/bootstrap.sh"}]))
final_steps.extend(cleanup_target["steps"])

computed_result["steps"] = final_steps

result = yaml.dump(computed_result)

f = open(args.output, "w")
f.write(result)
f.close()
print("Configuration generated successfully!")
