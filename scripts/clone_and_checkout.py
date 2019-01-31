#
# Script that will clone and checkout all epics base and modules
#
# Author: Jakub Wlodek
# Created on: 28-Jan-2019
# Copyright (c): Brookhaven National Laboratory
#

import os
import re
import argparse
import subprocess
import shutil


# Function that expands given paths via macros
def expand_module_path(path, current_modules, install_dir):
    if "$(INSTALL)" in path:
        return install_dir + path.split(')')[1]
    elif "$(SUPPORT)" in path:
        for module in current_modules:
            if module[0] == "SUPPORT":
                return module[2] + path.split(')')[1]
    elif "$(AREA_DETECTOR)" in path:
        for module in current_modules:
            if module[0] == "AREA_DETECTOR":
                return module[2] + path.split(')')[1]
    else:
        return path


# Function that gets a module from a certain module line
def module_from_line(line, current_modules, install_dir, current_url, url_type):
    line = re.sub(' +', ' ', line)
    module = line.split(' ')
    module[2] = expand_module_path(module[2], current_modules, install_dir)
    if "$(VERSION)" in module[3]:
        module[3] = module[3].split('$')[0]+ module[1] + module[3].split(')')[1]
    module.append(current_url)
    module.append(url_type)
    #print(module)
    return module


# Function that reads the information in the config file for cloning
def read_install_config_file():
    install_config = open("../configure/INSTALL_CONFIG", "r")
    current_url = ""
    url_type = ""
    install_location = ""
    current_modules = []
    line = install_config.readline()
    while line:
        if not line.startswith("#") and len(line) > 1:
            line = line.strip()
            if "INSTALL" in line and "$(INSTALL)" not in line:
                install_location = line.split('=')[1]
            elif "GIT_URL" in line:
                current_url = line.split('=')[1]
                url_type = "GIT_URL"
            elif "WGET_URL" in line:
                current_url = line.split('=')[1]
                url_type = "WGET_URL"
            else:
                module = module_from_line(line, current_modules, install_location, current_url, url_type)
                current_modules.append(module)
        line = install_config.readline()
    install_config.close()
    return current_modules, install_location


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


module_list, install_location = read_install_config_file()
check_install_location(install_location)
clone_and_checkout(module_list)
area_detector_cleanup(module_list)
print("Finished clone and checkout process")