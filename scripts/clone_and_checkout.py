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


def expand_module_path(path, current_modules, install_dir):
    if "$(INSTALL)" in path:
        return install_dir + path.split(')')
    elif "$(SUPPORT)" in path:
        for module in current_modules:
            if module[0] == "SUPPORT":
                return module[2] + path.split(')')
    elif "$(AREA_DETECTOR)" in path:
        for module in current_modules:
            if module[0] == "AREA_DETECTOR":
                return module[2] + path.split(')')
    else:
        return path

# Function that gets a module from a certain module line
def module_from_line(line, current_modules, install_dir, current_url, url_type):
    module = line.split('\t')
    print(module)
    module[2] = expand_module_path(module[2], current_modules, install_dir)
    module.append(current_url)
    module.append(url_type)
    return module


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
