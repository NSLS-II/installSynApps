#
# Python script that builds EPICS base and EPICS synApps, excluding areaDetector
#
# Author: Jakub Wlodek
#

import read_install_config
import update_release_file
import subprocess
import os


failed_builds = []

def compile_base(path_to_base):
    print("Compiling epics base located at "+path_to_base+"\n")
    out = subprocess.call(["make", "-C",  path_to_base, "-sj"])
    if out == 0:
        print("Built EPICS base")
        return 0
    else:
        print("ERROR compiling EPICS BASE")
        return -1


def compile_support(path_to_support):
    print("Calling make release for support modules\n")
    out = subprocess.call(["make", "-C", path_to_support, "release"])
    if out != 0:
        print("ERROR making release")
        return -1
    else:
        print("Compiling support located at "+path_to_support+"\n")
        out = subprocess.call(["make", "-C", path_to_support, "-sj"])
        if out != 0:
            print("ERROR compiling SUPPORT")
            return -1
        else:
            print("Compiled SUPPORT")
            return 0


def compile_ad(path_to_ad, module_list):
    #subprocess.call(["cd", path_to_ad+"/configure/"])
    #subprocess.call(["python3", "adConfigSetup/scripts/nsls2ADConfigSetup.py", "-r"])
    print("Compiling ADSupport\n")
    out = subprocess.call(["make", "-C", path_to_ad + "/ADSupport", "-sj"])
    if out != 0:
        print("Failed to compile ADSupport\n")
        return -1

    print("Compiling ADCore\n")
    out_core = subprocess.call(["make", "-C", path_to_ad + "/ADCore", "-sj"])
    if out_core != 0:
        print("Failed to compile ADCore\n")
        return -1

    for module in module_list:
        if os.path.isdir(path_to_ad+"/"+module[2].split('/')[-1]) and module[0] != "CONFIGURE" and module[0] != "DOCUMENTATION":
            if module[2].split('/')[-1] != "ADCore" and module[2].split('/')[-1] != "ADSupport" and module[5] == "YES":
                print("Compiling AD Module "+module[0]+"\n")
                out = subprocess.call(["make", "-C", module[2], "-sj"])
                if out != 0:
                    failed_builds.append(module)
    return 0
    


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

    for module in failed_builds:
        print("There was an error when building {}\n".format(module[0]))

    return 0
    
build_EPICS()