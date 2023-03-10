"""Class responsible for driving updates to config files

For a better understanding of how the update_config_driver works, it may be worthwhile
to run an installSynApps client with debug message printing enabled.
"""

import os
import re
import shutil
import installSynApps
import installSynApps.data_model.install_config as IC
import installSynApps.io.config_injector as CI
import installSynApps.io.logger as LOG


class UpdateConfigDriver:
    """Class that is used to drive the updating of configuration files

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
    dependency_ignore_list
        list of macros in RELEASE files that are not EPICS module dependencies
    """


    def __init__(self, path_to_configure, install_config):
        """Constructor for UpdateConfigDriver
        """

        self.install_config = install_config
        self.path_to_configure = path_to_configure
        self.config_injector = CI.ConfigInjector(self.install_config)
        self.add_to_release_blacklist = ["CONFIGURE", "DOCUMENTATION", "UTILS"]
        self.dependency_ignore_list = [ "TEMPLATE_TOP", "PCRE", 
                                        "SUPPORT", "INSTALL_LOCATION_APP", 
                                        "CAPFAST_TEMPLATES", "MAKE_TEST_IOC_APP",
                                        "BUILD_IOCS"]


    def perform_injection_updates(self):
        """Function that calls the ConfigInjector functions for appending config files.
        """

        injector_files = self.install_config.injector_files
        for injector in injector_files:
            self.config_injector.inject_to_file(injector)


    def get_macros_from_install_config(self):
        """Retrieves a list of name-path pairs from install config modules.

        The name-path pairs are used for updating areaDetector configuration files.

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
        """Updates the macros in the AD configuration files.
        """

        if self.install_config.ad_path is not None:
            self.update_macros(installSynApps.join_path(self.install_config.ad_path, "configure"), True, False)


    def update_support_macros(self):
        """Updates the macros in the support configuration files.
        """

        support_config = installSynApps.join_path(self.install_config.support_path, "configure")
        self.update_macros(support_config, False, False)

        # Some modules don't correctly have their RELEASE files updated by make release. Fix that here
        for module in self.install_config.get_module_list():
            if module.clone == 'YES' and module.build == 'YES':
                rel = installSynApps.join_path(module.abs_path, 'configure', 'RELEASE')
                if os.path.exists(rel):
                    LOG.write('Updating RELEASE file for {}...'.format(module.name))
                    self.update_macros(rel, True, True, single_file=True, auto_add_deps=True)


    def update_support_build_macros(self):
        """Function that applies build flags to support module configure directories.
        """

        for module in self.install_config.get_module_list():
            self.update_macros(installSynApps.join_path(module.abs_path, 'configure'), False, True, build_flags_only=True)


    def update_macros(self, target_path, include_ad, force_uncomment, single_file=False, build_flags_only=False, auto_add_deps=False):
        """Function that calls config injector to update all macros in target directory.

        This function is used on 3 occasions. 
        * To update areaDetector/configure/* files. This is done with indclude_ad and force_uncomment as True, and build_flags_only as false
        * To update the support/configure/RELEASE file. This is done with include_ad=False, force_uncomment=True, single_file=True
        * To update module/configure directories. In this case, build_flags_only=True and force_uncomment=True
        
        Parameters
        ----------
        target_path : str
            Path to directory that contains config files to be updated
        include_ad : bool
            Specifies whether or not to also update macros that fall under areaDetector (ADCORE, ADSUPPORT etc.)
        force_uncomment : bool
            If macro is found but commented, if this flag is set the comment is removed
        single_file=False : bool
            Apply update macros to a single file
        build_flags_only=False : bool
            In this case, only update the build flag macros specified in config, not module paths (use make release instead)
        auto_add_deps=False : bool
            When set to true, if a macro value is being added with another macro in it, the dependant macro is automatically added
        """

        install_macro_list = self.get_macros_from_install_config()
        if build_flags_only:
            install_macro_list = self.install_config.build_flags
        
        if not single_file:
            self.config_injector.update_macros_dir(install_macro_list, target_path, force_override_comments=force_uncomment)
        else:
            self.config_injector.update_macros_file(install_macro_list, 
                                                    os.path.dirname(target_path), 
                                                    os.path.basename(target_path), 
                                                    comment_unsupported=True, 
                                                    with_ad=include_ad, 
                                                    force=force_uncomment,
                                                    auto_add_deps=auto_add_deps)


    def add_missing_support_macros(self):
        """Function that appends any paths to the support/configure/RELEASE file that were not in it originally
        """

        to_append_commented = []
        to_append = []
        for module in self.install_config.get_module_list():
            if module.clone == "YES":
                was_found = False
                rel_file = open(installSynApps.join_path(self.install_config.support_path, "configure/RELEASE"), "r")
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

        rel_file_path = installSynApps.join_path(self.install_config.support_path, "configure", "RELEASE")
        rel_file_path_temp = installSynApps.join_path(self.install_config.support_path, "configure", "RELEASE_TEMP")
        os.rename(rel_file_path, rel_file_path_temp)
        rel_file_old = open(rel_file_path_temp, "r")
        rel_file_new = open(rel_file_path, "w")

        for line in rel_file_old.readlines():
            if line.startswith('#') or line.startswith('-'):
                rel_file_new.write(line)
            elif '=' in line: 
                name = line.split('=')[0]
                if name in self.install_config.module_map.keys() and self.install_config.get_module_by_name(name).build == 'YES':
                    pass
                else:
                    rel_file_new.write('#')
                    LOG.debug('Commenting out non-build module {} in support/configure/RELEASE'.format(name))
                rel_file_new.write(line)
        rel_file_new.close()
        rel_file_old.close()
        os.remove(rel_file_path_temp)


    def run_update_config(self, with_injection=True):
        """Top level driver function that updates all config files as necessary
        """

        self.update_ad_macros()
        self.update_support_macros()
        self.update_support_build_macros()
        self.add_missing_support_macros()
        self.comment_non_build_macros()
        if with_injection:
            self.perform_injection_updates()


    def check_module_dependencies(self, module):
        """Function that checks inter-module dependencies
        
        Grabs dependencies form the configure/RELEASE file. Modules that are under
        areaDetector get ADSupport and ADCore added as dependencies as well.

        Parameters
        ----------
        module : InstallModule
            install module for which to check dependencies
        """

        release_path = installSynApps.join_path(module.abs_path, installSynApps.join_path('configure', 'RELEASE'))
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


    def perform_dependency_valid_check(self):
        """Function that searches each modules configure/RELEASE file for dependencies.

        If a dependency is found, it is checked against loaded install config to make sure it 
        is scheduled to be built. Each module's dependencies attribute is populated

        Returns
        -------
        list of str
            A list of dependencies for modules that are not set to build.
        """

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
        """Function that checks if the order of module building is valid.

        Checks whether each module is being built after all of its dependencies.

        Returns
        -------
        bool
            True if valid, False if invalid
        str
            Name of module built before dependency, or None if none found
        str
            Name of dependency being built after module, or None if none found
        """

        for module in self.install_config.get_module_list():
            if len(module.dependencies) > 0:
                for dep in module.dependencies:
                    if self.install_config.get_module_build_index(module.name) < self.install_config.get_module_build_index(dep):
                        return False, module.name, dep
        return True, None, None


    def perform_fix_out_of_order_dependencies(self):
        """Function that repeatedly checks if dependency order is valid, until no issues found.

        Runs check_dependency_order_valid in a loop, until we get a 'True' response. If we get
        'False' swap the module and it's dependency and rerun
        """

        valid, current, dep = self.check_dependency_order_valid()
        while not valid:
            self.install_config.swap_module_positions(current, dep)
            LOG.write('Swapping build order of {} and {}'.format(current, dep))
            valid, current, dep = self.check_dependency_order_valid()
