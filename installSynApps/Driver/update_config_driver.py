#
# Class responsible for driving updates to config files
#
# Author: Jakub Wlodek
#

import os
import shutil
import DataModel.install_config as IC
import IO.config_injector as CI

class UpdateConfigDriver:
    """
    Class that is used to drive the updating of configuration files

    Attributes
    ----------
    install_config : InstallConfiguration
        Currently loaded install configuration
    path_to_configure : str
        path to the configure dir of installSynApps
    config_injector : ConfigInjector
        helper object used to inject into config files and update macro values
    fix_release_list : List of str
        list of modules that need to have their RELEASE file replaced
    
    Methods
    -------
    perform_injection_updates()
        Function that calls the ConfigInjector functions for appending config files
    get_macros_from_install_config()
        Retrieves a list of name-path pairs from install config modules
    update_ad_macros()
        Updates the macros in the AD configuration files
    update_support_macros()
        Updates the macros in the Support configuration files
    update_macros(target_path : str)
        Function that calls Config injector to update all macros in target dir
    fix_target_release(target_module_name : str)
        Function that replaces the RELEASE file of a target module with a corrected one
    run_update_config()
        Top level function that runs all required config update functions
    """

    def __init__(self, path_to_configure, install_config):
        """ Constructor for UpdateConfigDriver """

        self.install_config = install_config
        self.path_to_configure = path_to_configure
        self.config_injector = CI.ConfigInjector(path_to_configure, self.install_config)
        self.fix_release_list = ["DEVIOCSTATS"]

    def perform_injection_updates(self):
        """ Function that calls the ConfigInjector functions for appending config files """

        injector_files = self.config_injector.get_injector_files()
        for file_path in injector_files:
            self.config_injector.inject_to_file(file_path)
        
    
    def get_macros_from_install_config(self):
        """ 
        Retrieves a list of name-path pairs from install config modules

        Returns
        -------
        macro_list : List of [str, str]
            List of name-path pairs
        """

        macro_list = []

        for module in self.install_config.get_module_list():
            if module.clone == "YES":
                if module.name == "EPICS_BASE" or module.name == "SUPPORT":
                    macro_list.append([module.name, module.abs_path])
                else:
                    macro_list.append([module.name, module.rel_path])

        return macro_list


    def update_ad_macros(self):
        """ Updates the macros in the AD configuration files """

        self.update_macros(self.install_config.ad_path + "/configure")


    def update_support_macros(self):
        """ Updates the macros in the Support configuration files """

        self.update_macros(self.install_config.support_path + "/configure")


    def update_macros(self, target_path):
        """
        Function that calls Config injector to update all macros in target dir
        
        Parameters
        ----------
        target_path : str
            Path to directory that contains config files to be updated
        """

        install_macro_list = self.get_macros_from_install_config()
        macro_replace_files = self.config_injector.get_macro_replace_files()
        for file_path in macro_replace_files:
            self.config_injector.get_macro_replace_from_file(install_macro_list, file_path)
        
        self.config_injector.update_macros(install_macro_list, target_path)


    def fix_target_release(self, target_module_name):
        """
        Used to replace a target module's release file
        
        Parameters
        ----------
        target_module_name : str
            Name matching module.name field of target module
        """

        for module in self.install_config.get_module_list():
            if module.name == target_module_name:
                replace_release_path = self.path_to_configure + "/fixedRELEASEFiles/" + module.name + "_RELEASE"
                if os.path.exists(replace_release_path) and os.path.isfile(replace_release_path):
                    release_path = module.abs_path + "/configure/RELEASE"
                    release_path_old = release_path + "_OLD"
                    os.rename(release_path, release_path_old)
                    shutil.copyfile(replace_release_path, release_path)


    def run_update_config(self):
        """ Top level driver function that updates all config files as necessary """

        self.perform_injection_updates()
        for target in self.fix_release_list:
            self.fix_target_release(target)
        self.update_ad_macros()
        self.update_support_macros()
