"""Class responsible for packaging compiled binaries based on install config
"""

# imports
import os
import shutil
import sys
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
import installSynApps
import installSynApps.DataModel.install_config as IC
import installSynApps.IO.logger as LOG
import installSynApps.IO.config_writer as Writer


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
            LOG.debug('cd {}'.format(base_path))
            os.chdir(base_path)
            LOG.debug('git describe --tags')
            out = subprocess.check_output(['git', 'describe', '--tags'])
            LOG.debug('Checked version for EPICS base.')
            LOG.debug('cd {}'.format(current_loc))
            os.chdir(current_loc)
            LOG.debug('Detected version git tag {} for EPICS_BASE'.format(out.decode("utf-8").strip()))
            readme_fp.write('{:<16}- {}'.format('base', out.decode("utf-8")))
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
                LOG.debug('cd {}'.format(module.abs_path))
                os.chdir(module.abs_path)
                LOG.debug('git describe --tags')
                out = subprocess.check_output(['git', 'describe', '--tags'])
                LOG.debug('cd {}'.format(current_loc))
                os.chdir(current_loc)
                LOG.debug('Detected git tag/version: {} for module {}'.format(out.decode("utf-8").strip(), module.name))
                readme_fp.write('{:<16}- {}'.format(module_name, out.decode("utf-8")))
            else:
                LOG.debug('Detected version {} for module {}'.format(module.version, module.name))
                readme_fp.write('{:<16}- {}\n'.format(module_name, module.version))
        except subprocess.CalledProcessError:
            pass


    def write_readme_heading(self, text, readme_fp):
        """Simple helper function used to write headings for README file sections
        """

        readme_fp.write('{}\n#{}#\n# {:<61}#\n#{}#\n{}\n\n'.format('#' * 64, ' '* 62, text, ' '* 62, '#' * 64))


    def find_isa_version(self):
        """Function that attempts to get the version of installSynApps used.

        Returns
        -------
        str
            The version string for installSynApps. Either hardcoded version, or git tag description
        str
            None if git status not available, otherwise hash of current installSynApps commit.
        """

        isa_version = installSynApps.__version__
        commit_hash = None

        try:
            LOG.debug('git describe --tags')
            out = subprocess.check_output(['git', 'describe', '--tags'])
            isa_version = out.decode('utf-8').strip()
            LOG.debug('git rev-parse HEAD')
            out = subprocess.check_output(['git', 'rev-parse', 'HEAD'])
            commit_hash = out.decode('utf-8')
        except:
            LOG.debug('Could not find git information for installSynApps versions.')

        return isa_version, commit_hash


    def grab_configuration_used(self, top_location, readme_fp, module):
        """Function that includes the install configuration into the bundle for reuse.
        
        Parameters
        ----------
        top : str
            resulting location - __temp__
        """

        try:
            isa_version, isa_commit_hash = self.find_isa_version()
            if module is None:
                LOG.write('Copying build configuration into bundle.')
                writer = Writer.ConfigWriter(self.install_config)
                build_config_dir = os.path.join(top_location, 'build-config')
                writer.write_install_config(filepath=build_config_dir)
                self.write_readme_heading('Build environment version information', readme_fp)
            else:
                self.write_readme_heading('Implementing add on in exisitng bundle', readme_fp)
                readme_fp.write('This add on tarball contains a folder with a compiled version of {}.\n'.format(module.name))
                readme_fp.write('To use it with an existing bundle, please copy the folder into {} in the target bundle.\n'.format(module.rel_path))
                readme_fp.write('It is also recommended to edit the build-config for the bundle to reflect the inclusion of this module.\n\n')
            readme_fp.write('Build configuration:')
            readme_fp.write('installSynApps Version: {}\n\n'.format(isa_version))
            if isa_commit_hash is not None:
                readme_fp.write('To grab this version:\n\n\tgit clone https://github.com/epicsNSLS2-deploy/installSynApps\n')
                readme_fp.write('\tgit checkout {}\n'.format(isa_commit_hash))
            else:
                readme_fp.write('To grab this version use:\n\n\tgit clone https://github.com/epicsNSLS2-deploy/installSynApps\n')
                readme_fp.write('\tgit checkout -q {}\n'.format(isa_version))
            readme_fp.write('To regenerate sources for this bundle, grab installSynApps as described above, and use:\n\n')
            readme_fp.write('\t./installCLI.py -c BUILD_CONFIG -p\n\n')
            readme_fp.write('where BUILD_CONFIG is the path to the build-config directory in this bundle.\n')
            readme_fp.write('Make sure to specify an install location as well\n{}\n\n'.format('-' * 64))
            readme_fp.write('{:<20}{}\n'.format('Python 3 Version:',sys.version.split()[0]))
            readme_fp.write('{:<20}{}\n'.format('OS Class:', self.OS))
            readme_fp.write('{:<20}{}\n'.format('Build Date:', datetime.datetime.now()))
        except:
            LOG.debug('Failed to copy install configuration into bundle.')


    def add_versions_from_install_config(self, readme_fp, target):

        for module in self.install_config.get_module_list():
            if module.name != target.name and module.package == 'YES':
                readme_fp.write('{:<16}- {}\n'.format(module.name, module.version))


    def setup_tar_staging(self, filename, readme_fp, module=None):

        if os.path.exists('__temp__'):
            shutil.rmtree('__temp__')
        os.mkdir('__temp__')
        
        if module is not None:
            self.write_readme_heading('{} - Add-On Package'.format(module.name), readme_fp)
        else:
            self.write_readme_heading('Bundle - {}'.format(filename), readme_fp)
        isa_version, commit_hash = self.find_isa_version()
        readme_fp.write('Module package generated using installSynApps version: {}\n'.format(isa_version))
        readme_fp.write('See below for detailed build tool version information.\n')
        readme_fp.write('Module versions used in this deployment:\n')
        if module is not None:
            readme_fp.write('To add module to existing deployment, place it in the {} directory of the bundle.\n'.format(module.rel_path))
        readme_fp.write('[folder name] - [git tag]\n\n')


    def cleanup_tar_staging(self, filename, readme_fp, module=None):
        
        readme_fp.write('\n\n')
        self.grab_configuration_used('__temp__', readme_fp, module)
        LOG.debug('Generating README file with module version and append instructions...')
        shutil.copy(os.path.join(self.output_location, 'README_{}.txt'.format(filename)), os.path.join('__temp__', 'README_{}.txt'.format(filename)))

        LOG.write('Tarring...')
        out = subprocess.call(['tar', 'czf', filename + '.tgz', '-C', '__temp__', '.'])
        if out < 0:
            return out
        os.rename(filename + '.tgz', os.path.join(self.output_location, filename + '.tgz'))
        LOG.write('Done. Wrote tarball to {}.'.format(self.output_location))
        LOG.write('Name of tarball: {}'.format(os.path.join(self.output_location, filename + '.tgz')))
        shutil.rmtree('__temp__')
        return out


    def create_single_module_tarball(self, filename, module):
        """Function responsible for creating a tarball for a single module.

        Used to add modules to existing distributions.

        Parameters
        ----------
        module : InstallModule
            The module to add to the package
        """

        readme_fp = open(self.output_location + '/README_{}.txt'.format(filename), 'w')
        self.setup_tar_staging(filename, readme_fp, module=module)
        self.grab_module('__temp__', module, readme_fp)
        readme_fp.write('\nThe module was built against the following versions:\n\n')
        self.add_versions_from_install_config(readme_fp, module)
        result = self.cleanup_tar_staging(filename, readme_fp, module=module)
        readme_fp.close()
        return result


    def create_opi_tarball(self):
        """Function that collects autoconverted .opi files from epics_dir.

        OPI screens are saved  in output_location/ad_opis and creats a tarball.

        Returns
        -------
        int
            0 if suceeded, nonzero otherwise
        """

        opi_base_dir = os.path.join(self.output_location, '__opis_temp__')
        opi_dir = os.path.join(opi_base_dir, 'opis')
        try:
            os.mkdir(opi_base_dir)
            os.mkdir(opi_dir)
        except OSError:
            LOG.write('Error creating ' + opi_dir + ' directory', )

        for (root, dirs, files) in os.walk(self.install_config.install_location, topdown=True):
            for name in files:
                if '.opi' in name and 'autoconvert' in root:
                    file_name = os.path.join(root, name)
                    try:
                        shutil.copy(file_name, opi_dir)
                    except OSError:
                        LOG.debug("Can't copy {} to {}".format(file_name, opi_dir))

        opi_tarball_basename = 'opis_{}'.format(self.install_config.get_core_version())
        opi_tarball = opi_tarball_basename
        counter = 1
        while os.path.exists(os.path.join(self.output_location, opi_tarball + '.tgz')):
            opi_tarball = opi_tarball_basename + '_({})'.format(counter)
            counter = counter + 1

        out = subprocess.call(['tar', 'czf', opi_tarball + '.tgz', '-C', opi_base_dir, '.'])
        shutil.rmtree(opi_base_dir)
        os.rename(opi_tarball + '.tgz', os.path.join(self.output_location, opi_tarball + '.tgz'))
        return out
        

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

        readme_fp = open(self.output_location + '/README_{}.txt'.format(filename), 'w')
        self.setup_tar_staging(filename, readme_fp)

        self.grab_base('__temp__', readme_fp)

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


        result = self.cleanup_tar_staging(filename, readme_fp)
        readme_fp.close()
        return result


    def create_bundle_name(self, module_name=None):
        """Helper function for creating output filename

        Returns
        -------
        str
            An output filename describing architecture and ADCore version
        """

        if module_name is not None:
            module = self.install_config.get_module_by_name(module_name)
            if module is None:
                return None

        date_str = datetime.date.today()
        if module_name is None:
            output_filename = '{}_AD_{}_Bin_{}_{}'.format(self.institution, self.install_config.get_core_version(), self.OS, date_str)
        else:
            output_filename = '{}_AD_{}_Bin_{}_{}_addon'.format(self.institution, self.install_config.get_core_version(), self.OS, module.name)
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


    def create_add_on_package(self, filename, module_name):

        module = self.install_config.get_module_by_name(module_name)
        if module is None:
            return -1
        
        # Make sure output path exists
        if not os.path.exists(self.output_location):
            try:
                os.mkdir(self.output_location)
            except OSError:
                return -1
        
        # Start the timer
        self.start_timer()

        LOG.write('Beginning construction of {} add on...'.format(module.name))

        # Generate the bundle
        status = self.create_single_module_tarball(filename, module)

        # Stop the timer
        elapsed = self.stop_timer()
        LOG.write('Tarring took {} seconds'.format(elapsed))

        self.create_bundle_cleanup_tool()

        return status


    def create_opi_package(self):

        # Make sure output path exists
        if not os.path.exists(self.output_location):
            try:
                os.mkdir(self.output_location)
            except OSError:
                return -1

        # Start the timer
        self.start_timer()

        LOG.write('Beginning construction of opi tarball...')

        # Generate the bundle
        status = self.create_opi_tarball()

        # Stop the timer
        elapsed = self.stop_timer()
        LOG.write('Tarring took {} seconds'.format(elapsed))

        self.create_bundle_cleanup_tool()

        return status

