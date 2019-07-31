"""
Class responsible for packaging compiled binaries based on install config
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
# dependancy, but it is required because the platform.linuxdistro() is being deprecated
import distro

# Only depends on install config
import installSynApps.DataModel.install_config as IC

class Packager:
    """
    Class responsible for packaging compiled binaries based on install config

    Attributes
    ----------
    install_config : InstallConfiguration
        The currently loaded install configuration
    ad_drivers : list of str
        a list of ADDrivers and Plugins to include in the bundle
    opt_modules : list of str
        list of optional modules to include in the bundle
    arch : str
        architecture of bundle. Used for locating binaries in file structure and for naming
    OS : str
        used for naming on linux. Allows for using different bundles for different linux distributions
    start_time : a timestamp for the start of the tarring process

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
    grab_ad(top : str, readme_fp : FILE*)
        grabs all required ad directories
    grab_support(top : str, readme_fp : FILE*)
        grabs all required support directories
    create_tarball(filename : str)
        top level generator that creates tarball in DEPLOTMENTS/tarball
    create_package():
        function that should be called to use packager. Generates a unique package name, creates tarball, and measures time
    """

    def __init__(self, install_config, output_location='DEPLOYMENTS', force_arch=None):
        """
        Constructor for Packager

        Parameters
        ----------
        install_config : InstallConfiguration
            The currently loaded install configuration
        ad_drivers : list of str
            a list of ADDrivers and Plugins to include in the bundle
        opt_modules : list of str
            list of optional modules to include in the bundle
        force_arch : str
            defaults to None. If set, will force the packager to use a certain architecture. Useful for building on multiple OS. (ex. pacakging through WSL on windows)
        """
        self.install_config = install_config
        self.output_location = output_location

        self.ad_drivers = None
        self.opt_modules = None
        if force_arch is not None:
            self.arch = force_arch
            self.OS = force_arch
        elif platform.startswith('linux'):
            v = distro.linux_distribution(full_distribution_name=False)
            if len(v[0]) > 0 and len(v[1]) > 0:
                self.OS = '{}_{}'.format(v[0], v[1])
            else:
                self.OS = 'linux-x86_64'
            self.arch = 'linux-x86_64'
        elif platform == 'win32':
            self.arch = 'windows-x64-static'
            self.OS = self.arch
        self.start_time = 0
        self.required_in_pacakge = ['EPICS_BASE', 'ASYN', 'BUSY', 'ADCORE', 'ADSUPPORT', 'CALC', 'SNCSEQ', 'SSCAN', 'DEVIOCSTATS', 'AUTOSAVE']


    def start_timer(self):
        """ Helper function that starts the timer """

        self.start_time = time.time()


    def stop_timer(self):
        """
        Helper function that stops the timer

        Returns
        -------
        elapsed_time : int
            time since start_timer() was called in seconds
        """

        end_time = time.time()
        return end_time - self.start_time


    def get_drivers_to_package(self):
        """
        Function that gets list of ADDrivers/ADPlugins to package

        Returns
        -------
        list of str
            list of folder names of areaDetctor drivers to package
        """

        output = []
        for module in self.install_config.get_module_list():
            if module.rel_path.startswith('$(AREA_DETECTOR)') and module.name not in self.required_in_pacakge:
                if module.package == 'YES':
                    output.append(module.rel_path.split('/')[-1])

        return output


    def get_modules_to_package(self):
        """
        Function that gets list of support modules to package

        Returns
        -------
        list of str
            list of folder names of support modules to package
        """

        output = []
        for module in self.install_config.get_module_list():
            if module.rel_path.startswith('$(SUPPORT)') and module.name not in self.required_in_pacakge:
                if module.package == 'YES':
                    output.append(module.rel_path.split('/')[-1])
        return output


    def grab_folder(self, src, dest):
        """
        Helper function that copies folder if it exists

        Parameters
        ----------
        src : str
            folder to copy
        dest : str
            result location
        """

        if os.path.exists(src):
            shutil.copytree(src, dest)


    def grab_base(self, top, readme_fp):
        """
        Function that copies all of the required folders from EPICS_BASE

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
            out = subprocess.check_output(['git', '-C', base_path, 'describe', '--tags'])
            readme_fp.write('base : {}'.format(out.decode("utf-8")))
        except subprocess.CalledProcessError:
            pass


    def grab_module(self, top, module_name, module_location, readme_fp, is_ad_module = False):
        """
        Function that grabs all of the required folders from each individual module.

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

        target_folder = module_location + '/' + module_name
        self.grab_folder(target_folder + '/opi',                top + '/' + module_name +'/opi')
        self.grab_folder(target_folder + '/db',                 top + '/' + module_name +'/db')
        self.grab_folder(target_folder + '/include',            top + '/' + module_name +'/include')
        self.grab_folder(target_folder + '/bin/' + self.arch,   top + '/' + module_name +'/bin/' + self.arch)
        self.grab_folder(target_folder + '/lib/' + self.arch,   top + '/' + module_name +'/lib/' + self.arch)
        self.grab_folder(target_folder + '/configure',          top + '/' + module_name +'/configure')
        self.grab_folder(target_folder + '/iocBoot',            top + '/' + module_name +'/iocBoot')
        for dir in os.listdir(target_folder):
            if 'App' in dir and not dir.startswith('test'):
                self.grab_folder(target_folder + '/' + dir + '/Db', top + '/' + module_name +'/' + dir + '/Db')
                self.grab_folder(target_folder + '/' + dir + '/op', top + '/' + module_name +'/' + dir + '/op')
        if is_ad_module:
            if os.path.exists(target_folder + '/iocs'):
                for dir in os.listdir(target_folder + '/iocs'):
                    ioc_folder = '/iocs/' + dir
                    if 'IOC' in dir:
                        self.grab_folder(target_folder + ioc_folder + '/bin/' + self.arch,  top + '/' + module_name + ioc_folder + '/bin/' + self.arch)
                        self.grab_folder(target_folder + ioc_folder + '/lib/' + self.arch,  top + '/' + module_name + ioc_folder + '/lib/' + self.arch)
                        self.grab_folder(target_folder + ioc_folder + '/dbd',               top + '/' + module_name + ioc_folder + '/dbd')
                        self.grab_folder(target_folder + ioc_folder + '/iocBoot',           top + '/' + module_name + ioc_folder + '/iocBoot')

        try:
            out = subprocess.check_output(['git', '-C', module_location + '/' + module_name, 'describe', '--tags'])
            readme_fp.write('{} : {}'.format(module_name, out.decode("utf-8")))
        except subprocess.CalledProcessError:
            pass


    def grab_support(self, top, readme_fp):
        """
        Function that copies all of the required folders from SUPPORT

        Parameters
        ----------
        top : str
            resulting location - __temp__
        readme_fp : FILE*
            output readme file
        """

        support_path = self.install_config.support_path
        support_modules = ['asyn', 'autosave', 'busy', 'calc', 'iocStats', 'seq', 'sscan']
        if self.opt_modules is not None:
            support_modules.extend(self.opt_modules)
        for module in support_modules:
            self.grab_module(top, module, support_path, readme_fp)


    def grab_ad(self, top, readme_fp):
        """
        Function that copies all of the required folders from AREA_DETECTOR

        Parameters
        ----------
        top : str
            resulting location - __temp__
        readme_fp : FILE*
            output readme file
        """

        ad_path = self.install_config.ad_path
        self.grab_folder(ad_path + '/ADCore/db',                        top + '/areaDetector/ADCore/db')
        self.grab_folder(ad_path + '/ADCore/ADApp/Db',                  top + '/areaDetector/ADCore/ADApp/Db')
        self.grab_folder(ad_path + '/ADCore/ADApp/op',                  top + '/areaDetector/ADCore/ADApp/op')
        self.grab_folder(ad_path + '/ADCore/iocBoot',                   top + '/areaDetector/ADCore/iocBoot')
        self.grab_folder(ad_path + '/ADViewers/ImageJ',                 top + '/areaDetector/ADViewers/ImageJ')
        self.grab_folder(ad_path + '/ADCore/bin/'       + self.arch,    top + '/areaDetector/ADCore/bin/'       + self.arch)
        self.grab_folder(ad_path + '/ADCore/lib/'       + self.arch,    top + '/areaDetector/ADCore/lib/'       + self.arch)
        self.grab_folder(ad_path + '/ADSupport/bin/'    + self.arch,    top + '/areaDetector/ADSupport/bin/'    + self.arch)
        self.grab_folder(ad_path + '/ADSupport/lib/'    + self.arch,    top + '/areaDetector/ADSupport/lib/'    + self.arch)
        try:
            out = subprocess.check_output(['git', '-C', ad_path + '/ADCore',    'describe', '--tags'])
            readme_fp.write('ADCore : {}'.format(out.decode("utf-8")))
            out = subprocess.check_output(['git', '-C', ad_path + '/ADSupport', 'describe', '--tags'])
            readme_fp.write('ADSupport : {}'.format(out.decode("utf-8")))
        except subprocess.CalledProcessError:
            pass
        if self.ad_drivers is not None:
            for driver in self.ad_drivers:
                self.grab_module(top + '/areaDetector', driver, ad_path, readme_fp, is_ad_module=True)


    def create_tarball(self, filename):
        """
        Function responsible for creating the tarball given a filename.

        Parameters
        ----------
        filename : str
            name for output tarball and readme file
        
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
        self.grab_support(  '__temp__', readme_fp)
        self.grab_ad(       '__temp__', readme_fp)

        readme_fp.close()
        shutil.copy(self.output_location + '/README_{}.txt'.format(filename), '__temp__/README_{}.txt'.format(filename))

        out = subprocess.call(['tar', 'czf', filename + '.tgz', '-C', '__temp__', '.'])
        if out < 0:
            return out
        os.rename(filename + '.tgz', self.output_location + '/' + filename + '.tgz')
        shutil.rmtree('__temp__')
        return out


    def create_bundle_name(self):
        """ Helper function for creating output filename """

        date_str = datetime.date.today()
        output_filename = 'NSLS2_AD_{}_Bin_{}_{}'.format(self.install_config.get_core_version(), self.OS, date_str)
        temp = output_filename
        counter = 1
        while os.path.exists(self.output_location + '/' + temp + '.tgz'):
            temp = output_filename
            temp = temp + '_({})'.format(counter)
            counter = counter + 1
        output_filename = temp
        return output_filename


    def create_package(self, filename):
        """
        Top level driver function. Creates output dir, generates filename, and measures time.

        Returns
        -------
        int
            elapsed time if success, error code otherwise
        """

        self.ad_drivers     = self.get_drivers_to_package()
        self.opt_modules    = self.get_modules_to_package()

        if not os.path.exists(self.output_location):
            try:
                os.mkdir(self.output_location)
            except OSError:
                return -1
        
        self.start_timer()
        status = self.create_tarball(filename)
        elapsed = self.stop_timer()
        if status < 0:
            return status
        else:
            return elapsed
