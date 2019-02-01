#
# Python script that builds EPICS base and EPICS synApps, excluding areaDetector
#
# Author: Jakub Wlodek
#

import read_install_config
import update_release_file
import subprocess
import os

def compile_base(path_to_base):
    out = subprocess.call(["make", "-C",  path_to_base, "-sj"])
    if out == 0:
        print("Built EPICS base")
        return 0
    else:
        print("ERROR compiling EPICS BASE")
        return -1


def compile_support(path_to_support):
    out = subprocess.call(["make", "-C", path_to_support, "release"])
    if out != 0:
        print("ERROR making release")
        return -1
    else:
        out = subprocess.call(["make", "-C", path_to_support, "-sj"])
        if out != 0:
            print("ERROR compiling SUPPORT")
            return -1
        else:
            print("Compiled SUPPORT")
            return 0


def compile_ad(path_to_ad, module_list):
    subprocess.call(["cd", path_to_ad+"/configure/"])
    subprocess.call(["python3", "adConfigSetup/scripts/nsls2ADConfigSetup.py", "-r"])

    subprocess.call(["make", "-C", path_to_ad + "/ADSupport", "-sj"])
    subprocess.call(["make", "-C", path_to_ad + "/ADCore", "-sj"])

    for elem in os.listdir(path_to_ad):
        if os.path.isdir(path_to_ad+ "/" + elem) and elem != "configure":
            for module in module_list:
                if module[2].split('/')[-1] == elem and elem != "ADCore" and elem != "ADSupport":
                    subprocess.call(["make", "-C", module[2], "-sj"])


def build_EPICS():
    module_list, install_location = read_install_config.read_install_config_file()
    path_to_base = ""
    path_to_support = ""
    path_to_ad = ""

    for module in module_list:
        if module[0] == "EPICS_BASE":
            path_to_base = module[2]
        elif module[0] == "SUPPORT":
            path_to_support = module[2]
        elif module[0] == "AREA_DETECTOR":
            path_to_ad = module[2]
    
    if path_to_base == "" or path_to_support == "":
        print("ERROR, inorrect paths")
        return -1
    
    compiled = compile_base(path_to_base)

    update_release_file.update_release_file()

    if compiled < 0:
        return -1
    
    compiled = compile_support(path_to_support)

    if compiled < 0:
        return -1

    compiled = compile_ad(path_to_ad, module_list)

    if compiled < 0:
        return -1

    return 0
    
build_EPICS()