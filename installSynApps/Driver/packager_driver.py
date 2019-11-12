"""Class responsible for packaging compiled binaries based on install config
"""

__author__      = "Jakub Wlodek"

# imports
import os
import shutil
from sys import platform
import datetime
import time
import subprocess

# External package used to identify linux distribution version. Note that this adds external
# dependancy, but it is required because the platform.linuxdistro() function is being deprecated
WITH_DISTRO=True
try:
    import distro
except ImportError:
    # user does not have distro installed, so generic name will be used.
    WITH_DISTRO=False


# Only depends on install config
import installSynApps.DataModel.install_config as IC
import installSynApps.IO.logger as LOG


class Packager:
    """Class responsible for packaging compiled binaries based on install config

    Attributes
    ----------
    install_config : InstallConfiguration
        The currently loaded install configuration
    output_location : str
        The target output location of the bundle
    institution : str
        The name of the institution associated with the bundle (ie. NSLS2)
    found_distro : bool 
        A flag that tells the packager if the distro module is available
    arch : str
        architecture of bundle. Used for locating binaries in file structure and for naming
    OS : str
        used for naming on linux. Allows for using different bundles for different linux distributions
    start_time : time
        a timestamp for the start of the tarring process
    required_in_package : list of str
        list of modules that will be packaged no matter what

    Methods
    -------
    start_timer()
        starts the tar timer
    stop_timer()
        stops the timer and returns the elapsed time
    grab_folder(src : str, dest : str)
        helper function that copies a specified dir if it exists
    grab_base(top : str, readme_fp : FILE*)
        grabs all required base directories
    grab_module(top : str, module : InstallModule, readme_fp : FILE*)
        Function that grabs all of the required folders from each individual module.
    create_tarball(filename : str, flat_format : bool)
        top level generator that creates tarball in DEPLOTMENTS/tarball
    create_bundle_name()
        Helper function for creating output filename
    create_bundle_cleanup_tool()
        Simple function that spawns basic scripts used to remove unused bundles.
    create_package():
        function that should be called to use packager. Generates a unique package name, creates tarball, and measures time
    """

    def __init__(self, install_config, output_location='DEPLOYMENTS', force_arch=None):
        """Constructor for Packager Driver
        """

        self.install_config     = install_config
        self.output_location    = output_location

        self.institution = "NSLS2"

        if force_arch is not None:
            self.arch = force_arch
            self.OS = force_arch
        elif platform.startswith('linux'):
            if WITH_DISTRO:
                self.found_distro = True
                v = distro.linux_distribution(full_distribution_name=False)
                if len(v[0]) > 0 and len(v[1]) > 0:
                    self.OS = '{}_{}'.format(v[0], v[1])
                else:
                    self.OS = 'linux-x86_64'
            else:
                self.found_distro = False
                self.OS = 'linux-x86_64'
            self.arch = 'linux-x86_64'
        elif platform == 'win32':
            # when we are using windows, we don't care if distro is installed, so just assume it is true
            self.found_distro = True
            self.arch = 'windows-x64-static'
            self.OS = self.arch
        self.start_time = 0
        self.required_in_pacakge = ['EPICS_BASE', 'ASYN', 'BUSY', 'ADCORE', 'ADSUPPORT', 'CALC', 'SNCSEQ', 'SSCAN', 'DEVIOCSTATS', 'AUTOSAVE']


    def start_timer(self):
        """Helper function that starts the timer
        """

        self.start_time = time.time()


    def stop_timer(self):
        """Helper function that stops the timer

        Returns
        -------
        elapsed_time : double
            time since start_timer() was called in seconds
        """

        end_time = time.time()
        return end_time - self.start_time


    def grab_folder(self, src, dest):
        """Helper function that copies folder if it exists

        Parameters
        ----------
        src : str
            folder to copy
        dest : str
            result location
        """

        if os.path.exists(src) and not os.path.exists(dest):
            shutil.copytree(src, dest)


    def grab_base(self, top, readme_fp):
        """Function that copies all of the required folders from EPICS_BASE

        Parameters
        ----------
        top : str
            resulting location - __temp__
        readme_fp : FILE*
            output readme file
        """

        base_path = self.install_config.base_path
        self.grab_folder(base_path + '/bin/' + self.arch,   top + '/base/bin/' + self.arch)
        self.grab_folder(base_path + '/lib/' + self.arch,   top + '/base/lib/' + self.arch)
        self.grab_folder(base_path + '/lib/perl',           top + '/base/lib/perl')
        self.grab_folder(base_path + '/configure',          top + '/base/configure')
        self.grab_folder(base_path + '/include',            top + '/base/include')
        self.grab_folder(base_path + '/startup',            top + '/base/startup')
        try:
            current_loc = os.getcwd()
            LOG.print_command('cd {}'.format(base_path))
            os.chdir(base_path)
            LOG.print_command('git describe --tags')
            out = subprocess.check_output(['git', 'describe', '--tags'])
            LOG.debug('Checked version for EPICS base.')
            LOG.print_command('cd {}'.format(current_loc))
            os.chdir(current_loc)
            LOG.debug('Detected version git tag {} for EPICS_BASE'.format(out.decode("utf-8").strip()))
            readme_fp.write('base : {}'.format(out.decode("utf-8")))
        except subprocess.CalledProcessError:
            pass


    def grab_module(self, top, module, readme_fp):
        """Function that grabs all of the required folders from each individual module.

        Parameters
        ----------
        top : str
            resulting location - __temp__
        module_name : str
            folder name for the module
        module_location : str
            path to dir of location of module
        readme_fp : FILE*
            output readme file
        is_ad_module : bool
            default false. if true search for iocs directory as well.
        """

        module_name = os.path.basename(module.abs_path)

        target_folder = module.abs_path
        if not os.path.exists(target_folder):
            LOG.debug('Module {} not found, skipping...'.format(module.name))
            return

        LOG.debug('Grabbing files for module {}.'.format(module.name))
        self.grab_folder(target_folder + '/opi',                top + '/' + module_name + '/opi')
        self.grab_folder(target_folder + '/db',                 top + '/' + module_name + '/db')
        self.grab_folder(target_folder + '/dbd',                top + '/' + module_name + '/dbd')
        self.grab_folder(target_folder + '/include',            top + '/' + module_name + '/include')
        self.grab_folder(target_folder + '/bin/' + self.arch,   top + '/' + module_name + '/bin/' + self.arch)
        self.grab_folder(target_folder + '/lib/' + self.arch,   top + '/' + module_name + '/lib/' + self.arch)
        self.grab_folder(target_folder + '/configure',          top + '/' + module_name + '/configure')
        self.grab_folder(target_folder + '/iocBoot',            top + '/' + module_name + '/iocBoot')
        self.grab_folder(target_folder + '/modules',            top + '/' + module_name + '/modules')
        self.grab_folder(target_folder + '/ADViewers/ImageJ',   top + '/' + module_name + '/ADViewers/ImageJ')
        for dir in os.listdir(target_folder):
            if 'App' in dir and not dir.startswith('test'):
                self.grab_folder(target_folder + '/' + dir + '/Db', top + '/' + module_name +'/' + dir + '/Db')
                self.grab_folder(target_folder + '/' + dir + '/op', top + '/' + module_name +'/' + dir + '/op')
        if os.path.exists(target_folder + '/iocs'):
            for dir in os.listdir(target_folder + '/iocs'):
                ioc_folder = '/iocs/' + dir
                if 'IOC' in dir:
                    LOG.debug('Grabbing IOC files for module {} ioc: {}'.format(module.name, dir))
                    self.grab_folder(target_folder + ioc_folder + '/bin/' + self.arch,  top + '/' + module_name + ioc_folder + '/bin/' + self.arch)
                    self.grab_folder(target_folder + ioc_folder + '/lib/' + self.arch,  top + '/' + module_name + ioc_folder + '/lib/' + self.arch)
                    self.grab_folder(target_folder + ioc_folder + '/dbd',               top + '/' + module_name + ioc_folder + '/dbd')
                    self.grab_folder(target_folder + ioc_folder + '/iocBoot',           top + '/' + module_name + ioc_folder + '/iocBoot')

        try:
            if module.url_type == 'GIT_URL':
                current_loc = os.getcwd()
                LOG.print_command('cd {}'.format(module.abs_path))
                os.chdir(module.abs_path)
                LOG.print_command('git describe --tags')
                out = subprocess.check_output(['git', 'describe', '--tags'])
                LOG.print_command('cd {}'.format(current_loc))
                os.chdir(current_loc)
                LOG.debug('Detected git tag/version: {} for module {}'.format(out.decode("utf-8").strip(), module.name))
                readme_fp.write('{} : {}'.format(module_name, out.decode("utf-8")))
            else:
                LOG.debug('Detected version {} for module {}'.format(module.version, module.name))
                readme_fp.write('{} : {}'.format(module_name, module.version))
        except subprocess.CalledProcessError:
            pass


    def create_tarball(self, filename, flat_format):
        """Function responsible for creating the tarball given a filename.

        Parameters
        ----------
        filename : str
            name for output tarball and readme file
        flat_format=True : bool
            flag to toggle generating flat vs. non-flat binaries
        
        Returns
        -------
        out : int
            0 if success <0 if failure
        """

        if os.path.exists('__temp__'):
            shutil.rmtree('__temp__')
        os.mkdir('__temp__')
        readme_fp = open(self.output_location + '/README_{}.txt'.format(filename), 'w')
        readme_fp.write('{}\n\n'.format(filename))
        readme_fp.write('Versions used in this deployment:\n')
        readme_fp.write('[folder name] : [git tag]\n\n')

        self.grab_base(     '__temp__', readme_fp)

        support_top = '__temp__'
        if not flat_format:
            LOG.write('Non-flat output binary structure selected.')
            support_top = os.path.join('__temp__', 'support')
            os.mkdir(support_top)

        ad_top = os.path.join(support_top, 'areaDetector')
        os.mkdir(ad_top)

        for module in self.install_config.get_module_list():
            if (module.name in self.required_in_pacakge or module.package == "YES") and not module.name == "EPICS_BASE":
                if module.rel_path.startswith('$(AREA_DETECTOR)'):
                    self.grab_module(ad_top, module, readme_fp)
                else:
                    self.grab_module(support_top, module, readme_fp)

        readme_fp.close()
        LOG.debug('Generating README file with module versions...')
        shutil.copy(self.output_location + '/README_{}.txt'.format(filename), '__temp__/README_{}.txt'.format(filename))

        LOG.write('Tarring...')
        out = subprocess.call(['tar', 'czf', filename + '.tgz', '-C', '__temp__', '.'])
        if out < 0:
            return out
        os.rename(filename + '.tgz', os.path.join(self.output_location, filename + '.tgz'))
        LOG.write('Done. Wrote bundle to {}.'.format(self.output_location))
        LOG.write('Name of bundle: {}'.format(os.path.join(self.output_location, filename + '.tgz')))
        shutil.rmtree('__temp__')
        return out


    def create_bundle_name(self):
        """Helper function for creating output filename

        Returns
        -------
        str
            An output filename describing architecture and ADCore version
        """

        date_str = datetime.date.today()
        output_filename = '{}_AD_{}_Bin_{}_{}'.format(self.institution, self.install_config.get_core_version(), self.OS, date_str)
        temp = output_filename
        counter = 1
        while os.path.exists(self.output_location + '/' + temp + '.tgz'):
            temp = output_filename
            temp = temp + '_({})'.format(counter)
            counter = counter + 1
        output_filename = temp
        LOG.debug('Generated potential output tarball name as: {}'.format(output_filename))
        return output_filename


    def create_bundle_cleanup_tool(self):
        """Simple function that spawns basic scripts used to remove unused bundles.
        """

        if os.path.exists(self.output_location):
            if platform == 'win32':
                cleanup_tool_path = os.path.join(self.output_location, 'cleanup.bat')
                cleanup_tool = open(cleanup_tool_path, 'w')
                cleanup_tool.write('@echo OFF\n\ndel *.tgz\ndel *.txt\n\n')
                cleanup_tool.close()
            else:
                cleanup_tool_path = os.path.join(self.output_location, 'cleanup.sh')
                cleanup_tool = open(cleanup_tool_path, 'w')
                cleanup_tool.write('#!/bin/bash\n\nrm *.tgz\nrm *.txt\n\n')
                os.chmod(cleanup_tool_path, 0o755)
                cleanup_tool.close()


    def create_package(self, filename, flat_format=True):
        """Top level packager driver function.
        
        Creates output directory, generates filename, creates the tarball, and measures time.

        Returns
        -------
        double
            elapsed time if success, error code otherwise
        """

        # Make sure output path exists
        if not os.path.exists(self.output_location):
            try:
                os.mkdir(self.output_location)
            except OSError:
                return -1
        
        # Start the timer
        self.start_timer()
        
        LOG.write('Beginning bundling process...')

        # Generate the bundle
        status = self.create_tarball(filename, flat_format)

        # Stop the timer
        elapsed = self.stop_timer()
        LOG.write('Tarring took {} seconds'.format(elapsed))

        self.create_bundle_cleanup_tool()

        return status