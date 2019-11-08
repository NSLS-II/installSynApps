"""
Module responsible for driving the build process of installSynApps
"""

__author__   = 'Jakub Wlodek'

import os
import subprocess
from sys import platform
import installSynApps.DataModel.install_config as IC


class BuildDriver:
    """Class responsible for driving the autobuilding of EPICS, synApps, and areaDetector

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
    built : list of str
        list of modules built successfully

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
        """Constructor for BuildDriver
        """

        self.install_config = install_config
        self.threads = threads
        self.one_thread = one_thread
        self.make_flag = '-sj'
        self.create_make_flags()
        self.built = []


    def create_make_flags(self):
        """Function that creates the flags used by make.
        
        This flag will either be -s, -sj, or -sjNUM_THREADS
        """

        if self.one_thread:
            self.make_flag = '-s'
        elif self.threads == 0:
            self.make_flag = '-sj'
        else:
            self.make_flag = '-sj{}'.format(self.threads)


    def check_dependencies_in_path(self, allow_partial=False):
        """Function meant to check if required packages are located in the system path.

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
            current = 'perl'
            subprocess.call(['perl', '--version'], stdout=FNULL, stderr=FNULL)
            current = 'wget'
            subprocess.call(['wget', '--version'], stdout=FNULL, stderr=FNULL)
            current = 'git'
            subprocess.call(['git', '--version'], stdout=FNULL, stderr=FNULL)
            current = 'tar'
            subprocess.call(['tar', '--version'], stdout=FNULL, stderr=FNULL)
        except FileNotFoundError:
            if not allow_partial:
                status = False
            message = current

        FNULL.close()
        return status, message


    def acquire_dependecies(self, dependency_script_path):
        """Method that runs dependency install shell/batch script

        Parameters
        ----------
        dependency_script_path : str
            path to dependency shell/batch script
        """

        if os.path.exists(dependency_script_path) and os.path.isfile(dependency_script_path):
            if dependency_script_path.endswith('.bat'):
                subprocess.call([dependency_script_path])
            else:
                subprocess.call(['bash', dependency_script_path])


    def build_base(self, print_commands=False):
        """Function that compiles epics base
        
        Parameters
        ----------

        print_commands=False : bool
            flag that prints command being run.

        Returns
        -------
        int
            return code of make call
        """

        if print_commands:
            print('make -C {} {}'.format(self.install_config.base_path, self.make_flag))
        out = subprocess.call(["make", "-C", self.install_config.base_path, self.make_flag])
        if out == 0:
            self.built.append('EPICS_BASE')
        return out


    def build_support(self, print_commands=False):
        """Function that compiles EPICS Support
        
        Parameters
        ----------

        print_commands=False : bool
            flag that prints command being run.

        Returns
        -------
        int
            return code of make call
        """

        out = self.make_support_releases_consistent()
        if out != 0:
            return out
        if print_commands:
            print('make -C {} {}'.format(self.install_config.support_path, self.make_flag))
        out = subprocess.call(["make", "-C", self.install_config.support_path, self.make_flag])
        return out


    def build_ad(self, print_commands=False):
        """Function that compiles ADSupport, then ADCore, then ADModules.

        If a module has a custom build script detected

        Parameters
        ----------
        print_commands=False : bool
            flag that prints command being run.

        Returns
        -------
        int
            -1 if error, 0 if finished
        List of InstallModule
            list of AD InstallModules that failed to compile
        """

        failed_builds = []
        if print_commands:
            print('make -C {} {}'.format(self.install_config.ad_path + "/ADSupport", self.make_flag))
        out_support = subprocess.call(["make", "-C", self.install_config.ad_path + "/ADSupport", self.make_flag])
        if out_support != 0:
            return out_support, [] 

        if print_commands:
            print('make -C {} {}'.format(self.install_config.ad_path + "/ADCore", self.make_flag))
        out_core = subprocess.call(["make", "-C", self.install_config.ad_path + "/ADCore", self.make_flag])
        if out_core != 0:
            return out_core, []

        for module in self.install_config.get_module_list():
            if module.rel_path.startswith("$(AREA_DETECTOR)") and module.build == "YES":
                if module.custom_build_script_path is not None:
                    self.build_via_custom_script(module)
                elif module.name != "ADCORE" and module.name != "ADSUPPORT":
                    if print_commands:
                        print('make -C {} {}'.format(module.abs_path, self.make_flag))
                    out_mod = subprocess.call(["make", "-C", module.abs_path, self.make_flag])
                    if out_mod != 0:
                        failed_builds.append(module)

        return 0, failed_builds


    def build_ad_support(self, print_commands=False):
        """ Function that builds ad support """

        for module in self.install_config.get_module_list():
            if module.name == 'ADSUPPORT':
                if print_commands:
                    print('make -C {} {}'.format(module.abs_path, self.make_flag))
                out = subprocess.call(["make", "-C", module.abs_path , self.make_flag])
                if out == 0:
                    self.built.append('ADSUPPORT')
                return out
        return -1


    def build_ad_core(self, print_commands=False):
        """ Function that builds ad core """

        for module in self.install_config.get_module_list():
            if module.name == 'ADCORE':
                if print_commands:
                    print('make -C {} {}'.format(module.abs_path, self.make_flag))
                out = subprocess.call(["make", "-C", module.abs_path , self.make_flag])
                if out == 0:
                    self.built.append('ADCORE')
                return out
        return -1


    def make_support_releases_consistent(self, print_commands=False):
        """ Function that makes support module release files consistent """

        if print_commands:
            print('make -C {} release'.format(self.install_config.support_path))
        out = subprocess.call(["make", "-C", self.install_config.support_path, "release"])
        return out


    def build_support_module(self, module, print_commands=False):
        """ Function that builds only support modules """

        non_build_packages = ["SUPPORT", "CONFIGURE", "UTILS", "DOCUMENTATION", "AREA_DETECTOR", "QUADEM"]
        if module.rel_path.startswith("$(SUPPORT)") and module.name not in non_build_packages:
            if len(module.dependencies) > 0:
                for dependency in module.dependencies:
                    if dependency not in self.built:
                        self.build_support_module(self.install_config.get_module_by_name(dependency), print_commands=print_commands)
            if print_commands:
                print('make -C {} {}'.format(module.abs_path, self.make_flag))
            out = subprocess.call(["make", "-C", module.abs_path, self.make_flag])
            if out == 0:
                self.built.append(module.name)
            return out, True
        return 0, False


    def build_ad_module(self, module, print_commands=False):
        """Function that builds only ad modules
        
        Parameters
        ----------
        print_commands=False : bool
            flag that prints command being run.

        """

        if (module.rel_path.startswith("$(AREA_DETECTOR)") and module.name != 'ADCORE' and module.name != 'ADSUPPORT') or module.name == 'QUADEM':
            if print_commands:
                print('make -C {} {}'.format(module.abs_path, self.make_flag))
            out = subprocess.call(["make", "-C", module.abs_path , self.make_flag])
            return out, True
        else:
            return 0, False


    def build_via_custom_script(self, module):
        """Function that builds a module using its custom build script
        
        Parameters
        ----------
        module : InstallModule
            module to build with custom build script

        Returns
        -------
        int
            exit code of custom build script
        """

        current = os.getcwd()
        os.chdir(module.abs_path)
        if platform == 'win32':
            out_mod = subprocess.call([module.custom_build_script_path])
        else:
            out_mod = subprocess.call(['bash', module.custom_build_script_path])
        os.chdir(current)
        return out_mod


    def build_all(self, show_commands = False):
        """Main function that runs full build sequentially

        Parameters
        ----------
        show_commands=False : bool
            toggle for printing out commands being run

        Returns
        -------
        int
            -1 if error, 0 if success
        str
            message explaining error
        List of modules
            List of modules that failed to compile
        """

        ret = self.build_base(print_commands=show_commands)
        if ret != 0:
            return -1, "Error building EPICS base", []
        ret = self.build_support(print_commands=show_commands)
        if ret != 0:
            return -1, "Error building EPICS support", []
        ret, failed = self.build_ad(print_commands=show_commands)
        if len(failed) > 0:
            # failing to build individual ad module is not a critical error, so return 0
            return 0, "Error building AD modules", failed
        elif ret != 0:
            return -1, "Error building ADSupport and ADCore", []
        else:
            return 0, "", []
