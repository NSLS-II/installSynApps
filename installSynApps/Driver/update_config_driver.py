#
# Class responsible for driving updates to config files
#
# Author: Jakub Wlodek
#

import os
import DataModel.install_config as IC
import IO.config_injector as CI

class UpdateConfigDriver:

    def __init__(self, path_to_configure, install_config):

        self.install_config = install_config
        self.path_to_configure = path_to_configure
        self.config_injector = CI.ConfigInjector(path_to_configure, self.install_config)
        self.fix_release_list = ["DEVIOCSTATS"]

    def perform_injection_updates(self):
        injector_files = self.config_injector.get_injector_files()
        for file_path in injector_files:
            self.config_injector.inject_to_file(file_path)
        
    
    def get_macros_from_install_config(self):
        macro_list = []

        for module in self.install_config.get_module_list():
            if module.clone == "YES":
                if module.name == "EPICS_BASE" or module.name == "SUPPORT":
                    macro_list.append([module.name, module.abs_path])
                else:
                    macro_list.append([module.name, module.rel_path])

        return macro_list


    def update_ad_macros(self):
        self.update_macros(self.install_config.ad_path + "/configure")


    def update_support_macros(self):
        self.update_macros(self.install_config.support_path + "/configure")


    def update_macros(self, target_path):
        install_macro_list = self.get_macros_from_install_config()
        macro_replace_files = self.config_injector.get_macro_replace_files()
        for file_path in macro_replace_files:
            self.config_injector.get_macro_replace_from_file(install_macro_list, file_path)
        
        self.config_injector.update_macros(install_macro_list, target_path)


    def fix_target_release(self, target_module_name):
        for module in self.install_config.get_module_list():
            if module.name == target_module_name:
                replace_release_path = self.path_to_configure + "/fixedRELEASEFiles/" + module.name + "_RELEASE"
                if os.path.exists(replace_release_path) and os.path.isfile(replace_release_path):
                    release_path = module.abs_path + "/configure/RELEASE"
                    release_path_old = release_path + "_OLD"
                    os.rename(release_path, release_path_old)
                    temp = open(replace_release_path, "r")
                    new_file = open(release_path, "w")
                    line = temp.readline()
                    while line:
                        new_file.write(line)
                        line = temp.readline()
                    new_file.close()
                    temp.close()


    def run_update_config(self):
        self.perform_injection_updates()
        for target in self.fix_release_list:
            self.fix_target_release(target)
        self.update_ad_macros()
        self.update_support_macros()
