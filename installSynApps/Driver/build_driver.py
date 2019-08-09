"""
Class responsible for driving the build process of installSynApps
"""

__author__   = 'Jakub Wlodek'

import os
import subprocess
from sys import platform
import installSynApps.DataModel.install_config as IC


class BuildDriver:
    """
    Class responsible for driving the autobuilding of EPICS, synApps, and areaDetector

    Attributes
    ----------
    install_config : InstallConfiguration
        currently loaded install configuration
    threads : str
        number of threads to use
    one_thread : bool
        toggle to use single thread
    make_flag : str
        make flag to use for compilation (-s, -sj, -sjNUM_THREADS)

    Methods
    -------
    create_make_flags()
        Function that creates the flags used by make depending on the thread config passed in
    check_dependencies_in_path()
        Function meant to check if required packages are located in the system path
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
    build_ad_support()
        Function that builds only ad support
    build_ad_core()
        Function that builds only ad core
    build_ad_module()
        Function that builds an individual ad module
    """


    def __init__(self, install_config, threads, one_thread=False):
        """ Constructor for BuildDriver """

        self.install_config = install_config
        self.threads = threads
        self.one_thread = one_thread
        self.make_flag = '-sj'
        self.create_make_flags()


    def create_make_flags(self):
        """ Function that creates the flags used by make depending on the thread config passed in. """

        if self.one_thread:
            self.make_flag = '-s'
        elif self.threads == 0:
            self.make_flag = '-sj'
        else:
            self.make_flag = '-sj{}'.format(self.threads)


    def check_dependencies_in_path(self):
        """
        Function meant to check if required packages are located in the system path.

        Returns
        -------
        bool, str
            True and empty string if success, False and name of missing package if error
        """

        status = True
        message = ''
        current = 'make'
        FNULL = open(os.devnull, 'w')
        try:
            subprocess.call(['make', '--version'], stdout=FNULL, stderr=FNULL)
            current = 'wget'
            subprocess.call(['wget', '--version'], stdout=FNULL, stderr=FNULL)
            current = 'git'
            subprocess.call(['git', '--version'], stdout=FNULL, stderr=FNULL)
            current = 'tar'
            subprocess.call(['tar', '--version'], stdout=FNULL, stderr=FNULL)
            current = 'perl'
            subprocess.call(['perl', '--version'], stdout=FNULL, stderr=FNULL)
        except FileNotFoundError:
            status = False
            message = current

        FNULL.close()
        return status, message


    def acquire_dependecies(self, dependency_script_path, with_gui = False):
        """ Method that runs dependency install shell script """

        if os.path.exists(dependency_script_path) and os.path.isfile(dependency_script_path):
            subprocess.call(dependency_script_path, shell=True)


    def build_base(self):
        """ Function that compiles epics base """

        out = subprocess.call(["make", "-C", self.install_config.base_path, self.make_flag])
        return out


    def build_support(self):
        """ Function that compiles EPICS Support """

        out = subprocess.call(["make", "-C", self.install_config.support_path, "release"])
        if out != 0:
            return out
        out = subprocess.call(["make", "-C", self.install_config.support_path, self.make_flag])
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
        out_support = subprocess.call(["make", "-C", self.install_config.ad_path + "/ADSupport", self.make_flag])
        if out_support != 0:
            return out_support, [] 

        out_core = subprocess.call(["make", "-C", self.install_config.ad_path + "/ADCore", self.make_flag])
        if out_core != 0:
            return out_core, []

        for module in self.install_config.get_module_list():
            if module.rel_path.startswith("$(AREA_DETECTOR)") and module.build == "YES" and module.custom_build_script_path is None:
                if module.name != "ADCORE" and module.name != "ADSUPPORT":
                    out_mod = subprocess.call(["make", "-C", module.abs_path, self.make_flag])
                    if out_mod != 0:
                        failed_builds.append(module)
            elif module.custom_build_script_path is not None:
                current = os.getcwd()
                os.chdir(module.abs_path)
                if platform == 'win32':
                    out_mod = subprocess.call([module.custom_build_script_path])
                else:
                    out_mod = subprocess.call(['bash', module.custom_build_script_path])
                os.chdir(current)
                if out_mod != 0:
                    failed_builds.append(module)

        return 0, failed_builds


    def build_ad_support(self):
        """ Function that builds ad support """

        for module in self.install_config.get_module_list():
            if module.name == 'ADSUPPORT':
                out = subprocess.call(["make", "-C", module.abs_path , self.make_flag])
                return out
        return -1


    def build_ad_core(self):
        """ Function that builds ad core """

        for module in self.install_config.get_module_list():
            if module.name == 'ADCORE':
                out = subprocess.call(["make", "-C", module.abs_path , self.make_flag])
                return out
        return -1


    def build_ad_module(self, module):
        """ Function that builds only ad modules """

        if module.rel_path.startswith("$(AREA_DETECTOR)") and module.name != 'ADCORE' and module.name != 'ADSUPPORT' and module.custom_build_script_path is None:
            out = subprocess.call(["make", "-C", module.abs_path , self.make_flag])
            return out, True
        elif module.custom_build_script_path is not None:
            current = os.getcwd()
            os.chdir(module.abs_path)
            if platform == 'win32':
                out_mod = subprocess.call([module.custom_build_script_path])
            else:
                out_mod = subprocess.call(['bash', module.custom_build_script_path])
            os.chdir(current)
            return out_mod, True
        else:
            return 0, False


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
