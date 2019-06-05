#
# Class responsible for driving the build process of installSynApps
#
# Author: Jakub Wlodek
#


import os
import subprocess
import installSynApps.DataModel.install_config as IC


class BuildDriver:
    """
    Class responsible for driving the autobuilding of EPICS, synApps, and areaDetector

    Attributes
    ----------
    install_config : InstallConfiguration
        currently loaded install configuration

    Methods
    -------
    acquire_dependencies(dependency_script_path : str)
        function that calls script for acquiring dependency libraries and build environment
    build_base()
        function that calls make on EPICS base
    build_support()
        function that calls make release and then make on EPICS support
    build_ad()
        function that call make on ADSupport, then ADCore, then all AD modules
    build_all()
        function that calls all build functions sequentially
    """


    def __init__(self, install_config):
        """ Constructor for BuildDriver """

        self.install_config = install_config


    def acquire_dependecies(self, dependency_script_path, with_gui = False):
        """ Method that runs dependency install shell script """

        if os.path.exists(dependency_script_path) and os.path.isfile(dependency_script_path):
            subprocess.call(['sudo', dependency_script_path], shell=True)


    def build_base(self):
        """ Function that compiles epics base """

        out = subprocess.call(["make", "-C", self.install_config.base_path, "-sj"])
        return out


    def build_support(self):
        """ Function that compiles EPICS Support """

        out = subprocess.call(["make", "-C", self.install_config.support_path, "release"])
        if out != 0:
            return out
        out = subprocess.call(["make", "-C", self.install_config.support_path, "-sj"])
        return out


    def build_ad(self):
        """
        Function that compiles ADSupport, then ADCore, then ADModules.

        Returns
        -------
        int
            -1 if error, 0 if finished
        List of InstallModule
            list of AD InstallModules that failed to compile
        """

        failed_builds = []
        out_support = subprocess.call(["make", "-C", self.install_config.ad_path + "/ADSupport", "-sj"])
        if out_support != 0:
            return out_support, [] 

        out_core = subprocess.call(["make", "-C", self.install_config.ad_path + "/ADCore", "-sj"])
        if out_core != 0:
            return out_core, []

        for module in self.install_config.get_module_list():
            if module.rel_path.startswith("$(AREA_DETECTOR)") and module.build == "YES":
                if module.name != "ADCORE" and module.name != "ADSUPPORT":
                    out_mod = subprocess.call(["make", "-C", module.abs_path, "-sj"])
                    if out_mod != 0:
                        failed_builds.append(module)
                        
        return 0, failed_builds


    def build_all(self):
        """
        Main function that runs remaining ones sequentially

        Returns
        -------
        int
            -1 if error, 0 if success
        str
            message explaining error
        List of modules
            List of modules that failed to compile
        """

        ret = self.build_base()
        if ret < 0:
            return -1, "Error building EPICS base", []
        ret = self.build_support()
        if ret < 0:
            return -1, "Error building EPICS support", []
        ret, failed = self.build_ad()
        if len(failed) > 0:
            return -1, "Error building AD modules", failed
        elif ret < 0:
            return -1, "Error building ADSupport and ADCore", []
        else:
            return 0, "", []
        