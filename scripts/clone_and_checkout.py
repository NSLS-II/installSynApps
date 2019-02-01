#
# Script that will clone and checkout all epics base and modules
#
# Author: Jakub Wlodek
# Created on: 28-Jan-2019
# Copyright (c): Brookhaven National Laboratory
#

import os
import argparse
import subprocess
import shutil

import read_install_config



# Function that ensures that the install location is present and valid
def check_install_location(install_location):
    if os.path.isfile(install_location):
        print("ERROR, specified install location is a file")
        exit()
    elif not os.path.exists(install_location):
        os.mkdir(install_location)


# Function that clones and checksout each module based on entered data
def clone_and_checkout(module_list, with_tags = True):
    for module in module_list:
        if module[4] == "NO":
            print("Ignoring " + module[0])
        else:
            if module[6] == "GIT_URL" and with_tags:
                print("Cloning " + module[3] + " and checking out " + module[1])
                out = subprocess.call(["git", "clone", module[5] + module[3] , module[2]])
                if out == 0:
                    subprocess.call(["git", "-C", module[2], "checkout", "-q", module[1]])
            elif module[6] == "GIT_URL" and not with_tags:
                print("Cloning " + module[3] +" and checking out master")
                out = subprocess.call(["git", "clone", module[5] + module[3] , module[2]])
                if out == 0:
                    subprocess.call(["git", "-C", module[2], "checkout", "master"])
            else:
                out = subprocess.call(["wget", "-P", module[2], module[5] + module[3]])
                if out == 0:
                    subprocess.call(["tar", "-xvzf", module[2] + "/" + module[3], "-C", module[2], "--strip-components=1"])


def update_submodules(module_list):
    for module in module_list:
        if module[0] == "STREAM":
            subprocess.call(["git", "-C", module[2] + "/StreamDevice", "submodule", "init"])
            subprocess.call(["git", "-C", module[2] + "/StreamDevice", "submodule", "update"])


# Function that removes unwanted area detector modules for easier cleanup
def area_detector_cleanup(module_list):
    ad_path = ""
    for module in module_list:
        if module[0] == "AREA_DETECTOR":
            ad_path = module[2]
    for path in os.listdir(ad_path):
        if os.path.isdir(ad_path+"/"+path) and path != "configure" and path != "documentation":
            buildPath = False
            for module in module_list:
                if module[3] == path:
                    buildPath = True
            if buildPath == False:
                shutil.rmtree(ad_path + "/" + path)


module_list, install_location = read_install_config.read_install_config_file()
check_install_location(install_location)
clone_and_checkout(module_list)
update_submodules(module_list)
area_detector_cleanup(module_list)
print("Finished clone and checkout process")