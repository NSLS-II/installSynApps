#
# Class responsible for driving updates to config files
#
# Author: Jakub Wlodek
#


import os
import re
import shutil
import installSynApps.DataModel.install_config as IC
import installSynApps.IO.config_injector as CI
import installSynApps.IO.logger as LOG


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
    add_to_release_blacklist : List of str
        list of modules that should be commented in support/configure/RELEASE
    
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
    add_support_macros()
        Function that appends any paths to the support/configure/RELEASE file that were not in it originally
    comment_non_build_macros()
        Function that comments out any paths in the support/configure/RELEASE that are clone only and not build
    run_update_config()
        Top level function that runs all required config update functions
    """


    def __init__(self, path_to_configure, install_config):
        """ Constructor for UpdateConfigDriver """

        self.install_config = install_config
        self.path_to_configure = path_to_configure
        self.config_injector = CI.ConfigInjector(self.install_config)
        self.fix_release_list = ["DEVIOCSTATS"]
        self.add_to_release_blacklist = ["AREA_DETECTOR", "ADCORE", "ADSUPPORT", "CONFIGURE", "DOCUMENTATION", "UTILS", "QUADEM"]
        self.dependency_ignore_list = ["TEMPLATE_TOP", "PCRE", "SUPPORT", "INSTALL_LOCATION_APP", "CAPFAST_TEMPLATES", ]


    def check_module_dependencies(self, module):
        """Function that checks inter-module dependencies
        
        Grabs dependencies form the configure/RELEASE file. Modules that are under
        areaDetector get ADSupport and ADCore added as dependencies as well.

        Parameters
        ----------
        module : InstallModule
            install module for which to check dependencies
        """

        release_path = os.path.join(module.abs_path, os.path.join('configure', 'RELEASE'))
        if os.path.exists(release_path):
            release_file = open(release_path, 'r')
            lines = release_file.readlines()
            release_file.close()
            for line in lines:
                if not line.startswith('#') and '=' in line:
                    line = line.strip()
                    line = re.sub(' +', '', line)
                    dep = line.split('=')[0]
                    if dep not in module.dependencies and dep not in self.dependency_ignore_list and dep != module.name:
                        module.dependencies.append(dep)
                        if dep == 'AREA_DETECTOR' or (module.rel_path.startswith('$(AREA_DETECTOR)') and module.name != 'ADSUPPORT' and module.name != 'ADCORE'):
                            module.dependencies.append('ADSUPPORT')
                            module.dependencies.append('ADCORE')



    def perform_injection_updates(self):
        """ Function that calls the ConfigInjector functions for appending config files """

        injector_files = self.install_config.injector_files
        for injector in injector_files:
            self.config_injector.inject_to_file(injector)
        
    
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

        macro_list.extend(self.install_config.build_flags)
        return macro_list


    def update_ad_macros(self):
        """Updates the macros in the AD configuration files
        """

        if self.install_config.ad_path is not None:
            LOG.debug('Updating macros in the areaDetetor/configure directory')
            self.update_macros(os.path.join(self.install_config.ad_path, "configure"), True, False)


    def update_support_macros(self):
        """Updates the macros in the Support configuration files
        """

        self.update_macros(os.path.join(self.install_config.support_path, "configure/RELEASE"), False, False, single_file=True)
        for module in self.install_config.get_module_list():
            if module.name == "QUADEM" and module.build == "YES":
                self.update_macros(os.path.join(module.abs_path, "configure/RELEASE"), True, False, single_file=True)


    def update_support_build_macros(self):
        """Function that applies build flags to support module configure directories.
        """

        for module in self.install_config.get_module_list():
            self.update_macros(os.path.join(module.abs_path, 'configure'), False, True, build_flags_only=True)


    def update_macros(self, target_path, include_ad, force_uncomment, single_file=False, build_flags_only=False):
        """
        Function that calls config injector to update all macros in target dir
        
        Parameters
        ----------
        target_path : str
            Path to directory that contains config files to be updated
        """

        install_macro_list = self.get_macros_from_install_config()
        if build_flags_only:
            install_macro_list = self.install_config.build_flags
        
        if not single_file:
            self.config_injector.update_macros_dir(install_macro_list, target_path, force_override_comments=force_uncomment)
        else:
            self.config_injector.update_macros_file(install_macro_list, os.path.dirname(target_path), os.path.basename(target_path), comment_unsupported=True, with_ad=include_ad, force=force_uncomment)


    def fix_target_release(self, target_module_name):
        """Used to replace a target module's release file
        
        Parameters
        ----------
        target_module_name : str
            Name matching module.name field of target module
        """

        for module in self.install_config.get_module_list():
            if module.name == target_module_name:
                replace_release_path = os.path.join("resources/fixedRELEASEFiles/", module.name + "_RELEASE")
                if os.path.exists(replace_release_path) and os.path.isfile(replace_release_path):
                    release_path = os.path.join(module.abs_path, "configure/RELEASE")
                    if not os.path.exists(release_path):
                        return
                    release_path_old = release_path + "_OLD"
                    os.rename(release_path, release_path_old)
                    shutil.copyfile(replace_release_path, release_path)


    def add_missing_support_macros(self):
        """Function that appends any paths to the support/configure/RELEASE file that were not in it originally
        """

        to_append_commented = []
        to_append = []
        for module in self.install_config.get_module_list():
            if module.clone == "YES":
                was_found = False
                rel_file = open(os.path.join(self.install_config.support_path, "configure/RELEASE"), "r")
                line = rel_file.readline()
                while line:
                    if line.startswith(module.name + "="):
                        was_found = True
                    line = rel_file.readline()
                if not was_found and not module.name in self.add_to_release_blacklist and not module.name.startswith("AD"):
                    if module.build == "YES":
                        to_append.append([module.name, module.rel_path])
                    else:
                        to_append_commented.append([module.name, module.rel_path])
                rel_file.close()
        app_file = open(self.install_config.support_path + "/configure/RELEASE", "a")
        for mod in to_append:
            LOG.debug('Adding {} path to support/configure/RELEASE'.format(mod[0]))
            app_file.write("{}={}\n".format(mod[0], mod[1]))
        for mod in to_append_commented:
            LOG.debug('Adding commented {} path to support/configure/RELEASE'.format(mod[0]))
            app_file.write("#{}={}\n".format(mod[0], mod[1]))
        app_file.close()


    def comment_non_build_macros(self):
        """Function that comments out any paths in the support/configure/RELEASE that are clone only and not build.
        """

        rel_file_path = os.path.join(self.install_config.support_path, "configure/RELEASE")
        rel_file_path_temp = os.path.join(self.install_config.support_path, "configure/RELEASE_TEMP")
        os.rename(rel_file_path, rel_file_path_temp)
        rel_file_old = open(rel_file_path_temp, "r")
        rel_file_new = open(rel_file_path, "w")

        line = rel_file_old.readline()
        while line:
            if line.startswith('#'):
                rel_file_new.write(line)
            else:
                for module in self.install_config.get_module_list():
                    if line.startswith(module.name + "=") and module.build == "NO":
                        rel_file_new.write('#')
                rel_file_new.write(line)
            line = rel_file_old.readline()
        rel_file_new.close()
        rel_file_old.close()
        os.remove(rel_file_path_temp)
            


    def run_update_config(self):
        """Top level driver function that updates all config files as necessary
        """

        for target in self.fix_release_list:
            self.fix_target_release(target)
        self.update_ad_macros()
        self.update_support_macros()
        self.update_support_build_macros()
        self.add_missing_support_macros()
        self.comment_non_build_macros()
        self.perform_injection_updates()


    def perform_dependency_valid_check(self):
        dep_errors = []
        LOG.write('The following dependencies have been identified for each auto-build module:')
        for module in self.install_config.get_module_list():
            if module.build == "YES" and module.name != 'SUPPORT':
                ret = 0
                self.check_module_dependencies(module)
                if len(module.dependencies) > 0:
                    LOG.write('{:<16} - {}'.format(module.name, module.dependencies))
                for dep in module.dependencies:
                    dep_mod = self.install_config.get_module_by_name(dep)
                    if dep_mod is None:
                        ret = -1 
                        dep_errors.append('Dependency {} for module {} not in install config.'.format(dep, module.name))
                    elif dep_mod.build == 'NO':
                        ret = -1 
                        dep_errors.append('Dependency {} for module {} not being built.'.format(dep_mod.name, module.name))
                if ret < 0:
                    module.build = "NO"

        return dep_errors


    def check_dependency_order_valid(self):
        for module in self.install_config.get_module_list():
            if len(module.dependencies) > 0:
                for dep in module.dependencies:
                    if self.install_config.get_module_build_index(module.name) < self.install_config.get_module_build_index(dep):
                        return True, module.name, dep
        return False, None, None

    def perform_fix_out_of_order_dependencies(self):
        invalid, current, dep = self.check_dependency_order_valid()
        while invalid:
            self.install_config.swap_module_positions(current, dep)
            LOG.write('Swapping build order of {} and {}'.format(current, dep))
            invalid, current, dep = self.check_dependency_order_valid()