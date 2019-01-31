#
# Python script that builds EPICS base and EPICS synApps, excluding areaDetector
#
# Author: Jakub Wlodek
#

import read_install_config
import subprocess

def compile_base(path_to_base):
    out = subprocess.call(["make", "-C",  path_to_base, "-sj"])
    if out == 0:
        print("Built EPICS base")