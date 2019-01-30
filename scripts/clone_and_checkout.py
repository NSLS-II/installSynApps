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

# Function that gets list of git remote URLS and resource URLs from 
def read_url_file():
    git_remote_urls = []
    wget_urls = []
    url_file = open("../configure/URL_CONFIG", "r+")
    git_remote_start = False
    wget_remote_start = False
    line = url_file.readline()
    while line:
        if "http" in line and git_remote_start == True:
            git_remote_urls.append(line.strip())
        elif "http" in line and wget_remote_start == True:
            wget_urls.append(line.strip())
        if "GIT" in line:
            git_remote_start = True
        elif "WGET" in line:
            git_remote_start = False
            wget_remote_start = True
        line = url_file.readline()
    
    url_file.close()
    return git_remote_urls, wget_urls


# Function that reads the releases config file for 
def read_releases_file():
    module_release_list = []
    release_file = open("../configure/RELEASE_CONFIG", "r+")
    
    line = release_file.readline()
    while line:
        if not line.startswith("#") and "=" in line:
            line = line.strip()
            module_release_pair = line.split('=')
            module_release_list.append(module_release_pair)
        line = release_file.readline()

    release_file.close()
    return module_release_list

# Function that gives associated file paths for each module
def read_path_file(module_release_list):
    module_path_list = []
    path_file = open("../configure/PATH_CONFIG", "r+")

    install_path = ""
    support_path = ""

    line = path_file.readline()
    while line:
        if not line.startswith("#") and len(line) > 1:
            line = line.strip()
            path = line.split('=')[1]
            if "INSTALL" in line and "$(INSTALL)" not in line:
                line = line.strip()
                install_path = line.split('=')[1]
                print(install_path)
            elif "$(INSTALL)" in path:
                dirname = "base"
                path = install_path + path.split(')')[1]
                if "SUPPORT" in line:
                    support_path = path
                    dirname = "support"
                module_path_list.append([dirname, path])
            else:
                for pair in module_release_list:
                    if pair[0] in line:
                        if "$(SUPPORT) in path":
                            path = support_path + path.split(')')[1]
                            module_path_list.append([pair[0], path])
        line = path_file.readline()
    
    path_file.close()
    return module_path_list, install_path


def clone_and_checkout(install_path, module_release_list, module_path_list, git_remote_urls, wget_urls):
    if os.path.isfile(install_path):
        print("ERROR, install path must not be a file.")
    elif not os.path.exists(install_path):
        print("Install path did not exist, creating one now")
        os.mkdir(install_path)
    for module in module_path_list:
        if module[0] == "support":
            os.mkdir(module[1])
        else:
            mod_release = ""
            git_name = ""
            for release in module_release_list:
                if module[0] == release[0]:
                    mod_release = release[1]
                    git_name = release[0]
                elif module[0] == "base" and release[0] == "epics-base":
                    mod_release = release[1]
                    git_name = release[0]
            cloned = False
            counter = 0
            while cloned == False and counter < len(git_remote_urls):
                #subprocess.call(["export", "GIT_TERMINAL_PROMPT=0"])
                out = subprocess.call(["git", "clone", git_remote_urls[counter] + git_name, module[1]])
                if(out == 0):
                    subprocess.call(["git", "checkout", "-q", mod_release])
                    cloned = True
                counter = counter + 1
            if cloned == False:
                for url in wget_urls:
                    if module[0] == "seq":
                        subprocess.call(["wget", url + "seq-"+release[1]+".tar.gz", module[1]])
                        subprocess.call(["tar", "-xvzf", "seq-"+release[1]+".tar.gz", module[1]])
                    elif module[0] == "allenBradley":
                        subprocess.call(["wget", url+"allenBradley-"+release[1]+".tar.gz", module[1]])
                        subprocess.call(["tar", "-xvzf", "allenBradley-"+release[1]+".tar.gz", module[1]])


def run_clone_checkout():
    git_remote_urls, wget_urls = read_url_file()
    module_release_list = read_releases_file()
    module_path_list, install_location = read_path_file(module_release_list)
    clone_and_checkout(install_location, module_release_list, module_path_list, git_remote_urls, wget_urls)


run_clone_checkout()