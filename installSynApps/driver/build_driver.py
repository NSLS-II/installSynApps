"""Module responsible for driving the build process of installSynApps

Includes functions for building modules, updating releases, setting maximum core counts,
acquiring and checking dependencies.
"""

# Standard libs
import os
from subprocess import Popen, PIPE, STDOUT
import subprocess
from sys import platform
import sys

# Logger import
import installSynApps.io.logger as LOG


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
        self.non_build_packages = ["SUPPORT", "CONFIGURE", "UTILS", "DOCUMENTATION", "AREA_DETECTOR"]
        self.critical_modules = ["EPICS_BASE", "ASYN", "SNCSEQ"]


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


    def check_dependencies_in_path(self):
        """Function meant to check if required packages are located in the system path.

        Returns
        -------
        bool
            True if success, False if error
        str
            Empty string if success, otherwise name of mssing dependency
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

        LOG.debug('Grabbing dependencies via script {}'.format(dependency_script_path))
        if os.path.exists(dependency_script_path) and os.path.isfile(dependency_script_path):
            if dependency_script_path.endswith('.bat'):
                exec = dependency_script_path
            else:
                exec = 'bash {}'.format(dependency_script_path)
            LOG.print_command(exec)
            proc = Popen(exec.split(' '))
            proc.wait()
            ret = proc.returncode
            if ret != 0:
                LOG.write('Dependency script exited with non-zero exit code: {}'.format(ret))



    def make_support_releases_consistent(self):
        """Function that makes support module release files consistent

        Returns
        -------
        int
            return code of make release command call
        """

        LOG.write('Running make release to keep releases consistent.')
        command = 'make -C {} release'.format(self.install_config.support_path)
        LOG.print_command(command)
        proc = Popen(command.split(' '))
        proc.wait()
        ret = proc.returncode
        if ret != 0:
            LOG.write('make release exited with non-zero exit code: {}'.format(ret))
        return ret


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
            exec = module.custom_build_script_path
        else:
            exec = 'bash {}'.format(module.custom_build_script_path)
        LOG.print_command(exec)
        proc = Popen(exec.split(' '))
        proc.wait()
        ret = proc.returncode
        os.chdir(current)
        return ret


    def build_module(self, module_name):
        """Function that executes build of single module

        First, checks if all dependencies built, if not, does that first.
        Then checks for custom build script. If one is found, runs that from
        module root directory.
        Otherwise, runs make followed by specified make flag in module root
        directory.

        Parameters
        ----------
        module_name : str
            The name of the module being built

        Returns
        -------
        int
            The return code of the build process, 0 if module is not buildable (ex. UTILS)
        """

        if module_name in self.non_build_packages:
            return 0

        LOG.write('Building module {}'.format(module_name))
        module = self.install_config.get_module_by_name(module_name)
        if len(module.dependencies) > 0:
            for dep in module.dependencies:
                if dep not in self.built:
                    self.build_module(dep)
        if module.custom_build_script_path is not None:
            LOG.write('Detected custom build script located at {}'.format(module.custom_build_script_path))
            ret = self.build_via_custom_script(module)
            if ret == 0:
                self.built.append(module_name)
                LOG.write('Built module {} via custom script'.format(module_name))
            else:
                LOG.write('Custom script for module {} exited with error code {}.'.format(module_name, ret))
        else:
            command = "make -C {} {}".format(module.abs_path, self.make_flag)
            LOG.print_command(command)
            proc = Popen(command.split(' '))
            proc.wait()
            ret = proc.returncode
            if ret == 0:
                self.built.append(module_name)
                LOG.write('Built module {}'.format(module_name))
            else:
                LOG.write('Failed to build module {}'.format(module_name))
        return ret


    def build_all(self):
        """Main function that runs full build sequentially

        Returns
        -------
        int
            0 if success, number failed modules otherwise
        list of str
            List of module names that failed to compile
        """

        failed = []
        for module in self.install_config.get_module_list():
            if module.build == "YES":
                out = self.build_module(module.name)
                if out != 0:
                    failed.append(module.name)
                    if module.name in self.critical_modules:
                        break

                # After we build base we should make the support releases consistent
                if module.name == 'EPICS_BASE':
                    out = self.make_support_releases_consistent()
                    if out != 0:
                        LOG.write('Failed to make releases consistent...')
                        break

        return len(failed), failed
