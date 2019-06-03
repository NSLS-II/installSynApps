#
# Class responsible for driving the build process of installSynApps
#
# Author: Jakub Wlodek
#

import os
import subprocess
import DataModel.install_config as IC


class BuildDriver:


    def __init__(self, install_config):
        self.install_config = install_config
    

    def build_base(self):
        out = subprocess.call(["make", -C, self.install_config.base_path, "-sj"])
        return out


    def build_support(self):
        out = subprocess.call(["make", -C, self.install_config.support_path, "release"])
        if out != 0:
            return out
        out = subprocess.call(["make", -C, self.install_config.support_path, "-sj"])
        return out


    def build_ad(self):
        
        failed_builds = []
        out_support = subprocess.call(["make", "-C", self.install_config.ad_path + "/ADSupport", "-sj"])
        if out_support != 0:
            return out_support

        out_core = subprocess.call(["make", "-C", self.install_config.ad_path + "/ADCore", "-sj"])
        if out_core != 0:
            return out_core

        for module in self.install_config.get_module_list():
            if module.rel_path.startswith("$(AREA_DETECTOR)") and module.build == "YES":
                if module.name != "ADCORE" and module.name != "ADSUPPORT":
                    out_mod = subprocess.call(["make", "-C", module.abs_path, "-sj"])
                    if out_mod != 0:
                        failed_builds.append(module)
                        
        return failed_builds