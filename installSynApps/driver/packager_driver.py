"""Class responsible for packaging compiled binaries based on install config
"""

# std lib imports
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
import installSynApps
import installSynApps.data_model.install_config as IC
import installSynApps.io.logger as LOG
import installSynApps.io.file_generator as FILE_GENERATOR
import installSynApps.io.ioc_generator as IOC_GENERATOR


class Packager:
    """Class responsible for packaging compiled binaries based on install config

    Attributes
    ----------
    install_config : InstallConfiguration
        The currently loaded install configuration
    output_location : str
        The target output location of the bundle
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
    """


    def __init__(self, install_config, output_location='DEPLOYMENTS', force_arch=None):
        """Constructor for Packager Driver
        """

        self.install_config     = install_config
        self.output_location    = output_location

        self.file_generator     = FILE_GENERATOR.FileGenerator(install_config)

        if force_arch is not None:
            self.arch_list = force_arch
            self.OS = force_arch[0]
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
            
            # We want to support cross compiling debug versions if desired
            self.arch_list = ['linux-x86_64', 'linux-x86_64-debug']

        elif platform == 'win32':
            # when we are using windows, we don't care if distro is installed, so just assume it is true
            self.found_distro = True
            self.arch_list = ['windows-x64-static']
            self.OS = self.arch_list[0]
        
        # Timer
        self.start_time = 0

        # Modules that will be packaged if available regardless of configuration
        self.required_in_package = ['EPICS_BASE', 'ASYN', 'BUSY', 'AREA_DETECTOR', 
                                    'SUPPORT', 'ADCORE', 'ADSUPPORT', 'CALC', 'SNCSEQ', 
                                    'SSCAN', 'DEVIOCSTATS', 'AUTOSAVE']
        
        self.ioc_gen = IOC_GENERATOR.DummyIOCGenerator(self.install_config)


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

        if os.path.exists(src) and not os.path.exists(dest) and os.path.isdir(src):
            try:
                shutil.copytree(src, dest)
            except shutil.Error:
                LOG.write('Error when copying {}!\nPossibly softlinks in directory tree.'.format(src))


    def grab_file(self, src, dest):
        """Helper function that copies file if it exists

        Parameters
        ----------
        src : str
            folder to copy
        dest : str
            result location
        """

        if os.path.exists(src) and not os.path.exists(dest) and os.path.isfile(src):
            shutil.copy2(src, dest)


    def grab_all_files_in_dir(self, src, dest):
        """Helper method that collects all the files in one directory and moves them to another one.

        Parameters
        ----------
        src : os.PathLike
            Target source directory to pull from
        dest : os.PathLike
            Target destination directory to copy to
        """

        if not os.path.exists(dest):
            try:
                os.mkdir(dest)
            except:
                LOG.write('Failed to grab files from dir {}'.format(src))
                return

        if os.path.exists(src) and os.path.isdir(src) and os.path.exists(dest) and os.path.isdir(dest):
            for elem in os.listdir(src):
                #LOG.debug('Grabbing elem :{}'.format(elem))
                self.grab_file(src + '/' + elem, dest + '/' + elem)


    def grab_base_flat(self, top):
        """Method that collects all the files from EPICS base into a debian package like format

        Parameters
        ----------
        top : str
            Path to the staging area for the tarring process, usually __temp__
        """

        base_path = self.install_config.base_path
        LOG.debug('Grabbing flat epics base files')
        for arch in self.arch_list:
            self.grab_folder(base_path + '/bin/' + arch,   top + '/bin/' + arch)
            self.grab_folder(base_path + '/lib/' + arch,   top + '/lib/' + arch)
        self.grab_folder(base_path + '/cfg',                top + '/cfg')
        self.grab_folder(base_path + '/lib/perl',           top + '/lib/perl')
        self.grab_folder(base_path + '/configure',          top + '/configure')
        
        LOG.debug('Creating rules.d directory to allow for additional rule sets')
        os.mkdir(top + '/configure/rules.d')

        self.grab_folder(base_path + '/include',            top + '/include')
        self.grab_folder(base_path + '/startup',            top + '/startup')
        self.grab_folder(base_path + '/db',                 top + '/db')
        self.grab_folder(base_path + '/dbd',                top + '/dbd')
        self.grab_folder(base_path + '/templates',          top + '/templates')


    def grab_module_flat(self, top, module):
        """Helper method that grabs module files in a debian-packaging like format

        Parameters
        ----------
        top : str
            Path to the temporary staging location prior to tarrting, generally __temp__
        module : data_model.install_module.InstallModule
            Representation of install module to be included in the bundle
        """

        target_folder = module.abs_path
        if not os.path.exists(target_folder):
            LOG.debug('Module {} not found, skipping...'.format(module.name))
            return

        # In a release version we don't need any support helper utilities, so skip it.
        if not module.name == 'SUPPORT':
            LOG.debug('Grabbing flat files for module {}.'.format(module.name))
            self.grab_all_files_in_dir(target_folder + '/db', top + '/db')
            self.grab_all_files_in_dir(target_folder + '/dbd', top + '/dbd')
            for arch in self.arch_list:
                self.grab_all_files_in_dir(target_folder + '/bin/' + arch, top + '/bin/' + arch)
                self.grab_all_files_in_dir(target_folder + '/lib/' + arch, top + '/lib/' + arch)
            self.grab_all_files_in_dir(target_folder + '/include', top + '/include')
            self.grab_all_files_in_dir(target_folder + '/protocol', top + '/protocol')
            self.grab_all_files_in_dir(target_folder + '/pmc', top + '/pmc')

            if os.path.exists(target_folder + '/iocs'):
                self.grab_ioc_files(top, target_folder, module.name, True)

            motor_modules_dir = installSynApps.join_path(target_folder, 'modules')
            if module.name == 'MOTOR' and os.path.exists(motor_modules_dir):
                for dir in os.listdir(motor_modules_dir):
                    motor_module_dir = installSynApps.join_path(motor_modules_dir, dir)
                    motor_module_ioc_dir = installSynApps.join_path(motor_module_dir, 'iocs')
                    if os.path.isdir(motor_module_dir) and os.path.exists(motor_module_ioc_dir):
                        self.grab_ioc_files(top, motor_module_dir, dir.upper(), True)

            self.grab_file(module.abs_path + '/configure/RULES_BUILD', top + '/configure/rules.d/{}.make'.format(module.name))


    def grab_ioc_files(self, top, target_loc, module_name, flat_grab):
        for dir in os.listdir(target_loc + '/iocs'):
            ioc_folder = '/iocs/' + dir
            if 'IOC' in dir:
                if not flat_grab:
                    LOG.debug('Grabbing IOC files for module {} ioc: {}'.format(module_name, dir))
                    module_base_folder = os.path.basename(target_loc)
                    for arch in self.arch_list:
                        self.grab_folder(target_loc + ioc_folder + '/bin/' + arch,  top + '/' + module_base_folder + ioc_folder + '/bin/' + arch)
                        self.grab_folder(target_loc + ioc_folder + '/lib/' + arch,  top + '/' + module_base_folder + ioc_folder + '/lib/' + arch)
                    self.grab_folder(target_loc + ioc_folder + '/dbd',               top + '/' + module_base_folder + ioc_folder + '/dbd')
                    self.grab_folder(target_loc + ioc_folder + '/iocBoot',           top + '/' + module_base_folder + ioc_folder + '/iocBoot')
                else:
                    LOG.debug('Grabbing IOC files for module {} ioc: {}'.format(module_name, dir))
                    for arch in self.arch_list:
                        self.grab_all_files_in_dir(target_loc + ioc_folder + '/bin/' + arch,  top + '/bin/' + arch)
                        self.grab_all_files_in_dir(target_loc + ioc_folder + '/lib/' + arch,  top + '/lib/' + arch)
                    self.grab_all_files_in_dir(target_loc + ioc_folder + '/dbd',               top + '/dbd')
                    self.grab_all_files_in_dir(target_loc + ioc_folder + '/protocol',          top +  '/protocol')



    def grab_base(self, top, include_src=False, flat_grab=False):
        """Function that copies all of the required folders from EPICS_BASE

        Parameters
        ----------
        top : str
            resulting location - __temp__
        """

        if flat_grab:
            self.grab_base_flat(top)
            return

        base_path = self.install_config.base_path
        if not include_src:
            LOG.debug('Grabbing lean epics base files')
            for arch in self.arch_list:
                self.grab_folder(base_path + '/bin/' + arch,   top + '/base/bin/' + arch)
                self.grab_folder(base_path + '/lib/' + arch,   top + '/base/lib/' + arch)
            self.grab_folder(base_path + '/lib/perl',           top + '/base/lib/perl')
            self.grab_folder(base_path + '/cfg',                top + '/base/cfg')
            self.grab_folder(base_path + '/configure',          top + '/base/configure')
            self.grab_folder(base_path + '/include',            top + '/base/include')
            self.grab_folder(base_path + '/startup',            top + '/base/startup')
            self.grab_folder(base_path + '/db',                 top + '/base/db')
            self.grab_folder(base_path + '/dbd',                top + '/base/dbd')
        else:
            LOG.debug('Grabbing full epics base files')
            self.grab_folder(base_path,                         top + '/base')


    def grab_module(self, top, module, include_src=False, flat_grab=False):
        """Function that grabs all of the required folders from each individual module.

        Parameters
        ----------
        top : str
            resulting location - __temp__
        module_name : str
            folder name for the module
        module_location : str
            path to dir of location of module
        """

        if flat_grab:
            self.grab_module_flat(top, module)
            return

        module_name = os.path.basename(module.abs_path)

        target_folder = module.abs_path
        if not os.path.exists(target_folder):
            LOG.debug('Module {} not found, skipping...'.format(module.name))
            return

        # In a release version we don't need any support helper utilities, so skip it.
        if not include_src and not module.name == 'SUPPORT':
            LOG.debug('Grabbing lean files for module {}.'.format(module.name))
            self.grab_folder(target_folder + '/opi',                top + '/' + module_name + '/opi')
            self.grab_folder(target_folder + '/db',                 top + '/' + module_name + '/db')
            self.grab_folder(target_folder + '/dbd',                top + '/' + module_name + '/dbd')
            self.grab_folder(target_folder + '/include',            top + '/' + module_name + '/include')
            for arch in self.arch_list:
                self.grab_folder(target_folder + '/bin/' + arch,   top + '/' + module_name + '/bin/' + arch)
                self.grab_folder(target_folder + '/lib/' + arch,   top + '/' + module_name + '/lib/' + arch)
            self.grab_folder(target_folder + '/configure',          top + '/' + module_name + '/configure')
            self.grab_folder(target_folder + '/modules',            top + '/' + module_name + '/modules')
            self.grab_folder(target_folder + '/iocBoot',            top + '/' + module_name + '/iocBoot')
            self.grab_folder(target_folder + '/modules',            top + '/' + module_name + '/modules')
            self.grab_folder(target_folder + '/ADViewers/ImageJ',   top + '/' + module_name + '/ADViewers/ImageJ')
            for dir in os.listdir(target_folder):
                if 'App' in dir and not dir.startswith('test'):
                    self.grab_folder(target_folder + '/' + dir + '/Db', top + '/' + module_name +'/' + dir + '/Db')
                    self.grab_folder(target_folder + '/' + dir + '/op', top + '/' + module_name +'/' + dir + '/op')
            if os.path.exists(target_folder + '/iocs'):
                self.grab_ioc_files(top, target_folder, module.name, False)

        else:
            LOG.debug('Grabbing full files for module {}.'.format(module.name))

            # Grab some necessary non-module folders and files
            if module.name == 'AREA_DETECTOR':
                self.grab_folder(target_folder + '/configure', top + '/' + module_name + '/configure')
            elif module.name == 'SUPPORT':
                self.grab_folder(target_folder + '/configure', top + '/' + '/configure')
                self.grab_folder(target_folder + '/utils', top + '/' + '/utils')
                self.grab_file(target_folder + '/Makefile', top + '/' + '/Makefile')
            else:
                # Otherwise grab the entire module
                self.grab_folder(target_folder, top + '/' + module_name)


    def setup_tar_staging(self):
        """Function that creates tar staging point.
        """

        if os.path.exists('__temp__'):
            shutil.rmtree('__temp__')\

        os.mkdir('__temp__')
        # Make our bundle top directory


    def cleanup_tar_staging(self, filename, module=None):
        """Function that cleans up tar staging point, and closes readme file.

        Parameters
        ----------
        filename : str
            file path string
        module : InstallModule
            Optional install module to create single module add-on package
        
        Returns
        -------
        int
            Return code of tar creation call.
        """
        
        LOG.debug('Generating README file with module version and append instructions...')
        LOG.debug(os.getcwd())
        shutil.copy(installSynApps.join_path(self.output_location, 'README_{}.txt'.format(filename)), installSynApps.join_path('__temp__', filename, 'README'))

        LOG.write('Tarring...')
        out = subprocess.call(['tar', 'czf', filename + '.tar.gz', '-C', '__temp__', '.'])
        if out < 0:
            return out
        os.rename(filename + '.tar.gz', installSynApps.join_path(self.output_location, filename + '.tar.gz'))
        LOG.write('Done. Wrote tarball to {}.'.format(self.output_location))
        LOG.write('Name of tarball: {}'.format(installSynApps.join_path(self.output_location, filename + '.tar.gz')))
        shutil.rmtree('__temp__')
        return out


    def create_single_module_tarball(self, filename, module, with_sources):
        """Function responsible for creating a tarball for a single module.

        Used to add modules to existing distributions.

        Parameters
        ----------
        filename : str
            Name of output file
        module : InstallModule
            The module to add to the package
        """

        readme_path = installSynApps.join_path(self.output_location, 'README_{}.txt'.format(filename))
        
        self.setup_tar_staging()
        os.rename(installSynApps.join_path('__temp__', 'epicsbundle-1'),'__temp__/{}'.format(module.name))

        self.grab_module('__temp__/{}'.format(module.name), module, include_src=with_sources)
        self.file_generator.generate_readme(filename, installation_type='addon', readme_path=readme_path, module=module)
        
        result = self.cleanup_tar_staging(filename, module=module)
        return result


    def create_tarball(self, filename, install_path, flat_format, with_sources):
        """Function responsible for creating the tarball given a filename.

        Parameters
        ----------
        filename : str
            name for output tarball and readme file
        flat_format=True : bool
            flag to toggle generating flat vs. non-flat binaries
        with_sources : bool
            flag to include non-build artefact files with bundle
        
        Returns
        -------
        out : int
            0 if success <0 if failure
        """

        # Initializes temp directory, and installs bundle to said directory
        self.setup_tar_staging()

        self.install_bundle(filename, flat_format, with_sources=with_sources, force_install_loc='__temp__')
        
        result = self.cleanup_tar_staging(filename)

        return result


    def create_bundle_name(self, module_name=None, source_bundle=False, flat_bundle=False):
        """Helper function for creating output filename

        Returns
        -------
        str
            An output filename describing OS, and the date
        """

        if module_name is not None:
            module = self.install_config.get_module_by_name(module_name)
            if module is None:
                return None

        bundle_type = 'Prod'
        if source_bundle:
            bundle_type = 'Debug'
        elif flat_bundle:
            bundle_type= 'Lean'

        date_str = datetime.date.today()
        output_filename = 'EPICS_{}_Bundle_{}_{}'.format(bundle_type, self.OS, date_str)

        temp = output_filename
        counter = 1
        while os.path.exists(self.output_location + '/' + temp + '.tar.gz'):
            temp = output_filename
            temp = temp + '_({})'.format(counter)
            counter = counter + 1
        output_filename = temp

        LOG.debug('Generated output tarball name as: {}'.format(output_filename))
        return output_filename


    def create_bundle_cleanup_tool(self):
        """Simple function that spawns basic scripts used to remove unused bundles.
        """

        if os.path.exists(self.output_location):
            if platform == 'win32':
                cleanup_tool_path = installSynApps.join_path(self.output_location, 'cleanup.bat')
                cleanup_tool = open(cleanup_tool_path, 'w')
                cleanup_tool.write('@echo OFF\n\ndel *.tar.gz\ndel *.txt\n\n')
                cleanup_tool.close()
            else:
                cleanup_tool_path = installSynApps.join_path(self.output_location, 'cleanup.sh')
                cleanup_tool = open(cleanup_tool_path, 'w')
                cleanup_tool.write('#!/bin/bash\n\nrm *.tar.gz\nrm *.txt\n\n')
                os.chmod(cleanup_tool_path, 0o755)
                cleanup_tool.close()


    def create_repoint_bundle_script(self):
        """Function that generates script for repointing the RELEASE files in the bundle to their current location
        """

        if platform != 'win32':
            rs_fp = open(installSynApps.join_path('__temp__', 'repoint_bundle.sh'), 'w')
            rs_fp.write('#!/bin/bash\n\n')
            rs_fp.write('#\n# Script auto-generated by installSynApps on {}\n#\n\n'.format(datetime.datetime.now()))
            rs_fp.write('BUNDLE_LOC=$(pwd)\nEPICS_BASE=$BUNDLE_LOC/base\nSUPPORT=$BUNDLE_LOC/support\n\n')
            rs_fp.write('sed -i "s|^EPICS_BASE=.*|EPICS_BASE=$EPICS_BASE|g" "$SUPPORT/configure/RELEASE"\n')
            rs_fp.write('sed -i "s|^SUPPORT=.*|SUPPORT=$SUPPORT|g" "$SUPPORT/configure/RELEASE"\n\n')
            rs_fp.write('cd $SUPPORT\n')
            rs_fp.write('make release\n\n')
            rs_fp.write('sed -i "s|^EPICS_BASE=.*|EPICS_BASE=$EPICS_BASE|g" "$SUPPORT/areaDetector/configure/RELEASE_PRODS.local"\n')
            rs_fp.write('sed -i "s|^SUPPORT=.*|SUPPORT=$SUPPORT|g" "$SUPPORT/areaDetector/configure/RELEASE_SUPPORT.local"\n')
            os.chmod(installSynApps.join_path('__temp__', 'repoint_bundle.sh'), 0o755)
            rs_fp.close()


    def install_bundle(self, output_filename, flat_output, with_sources=False, force_install_loc=None, external_readme=True):

        install_loc = self.output_location
        readme_name = 'README'
        if force_install_loc is not None:
            LOG.write('Copying build artifacts to temp directory...')
            install_loc = force_install_loc
            readme_loc = self.output_location
            readme_name = 'README_{}.txt'.format(output_filename)
        else:
            LOG.write('Installing bundle to {}...'.format(self.output_location))
            readme_loc = installSynApps.join_path(install_loc, output_filename)

        bundle_top = installSynApps.join_path(install_loc, output_filename)
        if os.path.exists(bundle_top):
            shutil.rmtree(bundle_top)    
        os.mkdir(bundle_top)

        readme_path = installSynApps.join_path(readme_loc, readme_name)
        self.grab_base(bundle_top, include_src=with_sources, flat_grab=flat_output)

        support_top = bundle_top
        if not flat_output:
            LOG.write('Non-flat output binary structure selected.')
            support_top = installSynApps.join_path(bundle_top, 'support')
            os.mkdir(support_top)

        ad_top = bundle_top
        if not flat_output:
            ad_top = installSynApps.join_path(support_top, 'areaDetector')
            os.mkdir(ad_top)

        for module in self.install_config.get_module_list():
            if (module.name in self.required_in_package or module.package == "YES" or (with_sources and module.build == "YES")) and not module.name == "EPICS_BASE":
                if module.rel_path.startswith('$(AREA_DETECTOR)'):
                    self.grab_module(ad_top, module, include_src=with_sources, flat_grab=flat_output)
                else:
                    self.grab_module(support_top, module, include_src=with_sources, flat_grab=flat_output)


        # We always create a README file to know which modules were included
        package_type = 'bundle'
        if with_sources:
            package_type = 'source'

        self.file_generator.generate_readme(output_filename, installation_type=package_type, readme_path=readme_path, flat_grab=flat_output)
        self.file_generator.generate_license(bundle_top)
        
        if not flat_output or with_sources:
            self.ioc_gen.init_template_dir(output_filename)
            self.ioc_gen.generate_dummy_iocs()

        if with_sources:
            self.create_repoint_bundle_script()

        LOG.write('Done.')

        return 0


    def create_package(self, filename, install_path='DEPLOYMENTS', flat_format=True, with_sources=False):
        """Top level packager driver function.

        Creates output directory, generates filename, creates the tarball, and measures time.

        Parameters
        ----------
        filename : str
            filename of output bundle
        flat_format : bool
            Flag to specify flat vs. non-flat binaries

        Returns
        -------
        int
            status of tar creation command
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
        status = self.create_tarball(filename, install_path, flat_format, with_sources)

        # Stop the timer
        elapsed = self.stop_timer()
        LOG.write('Tarring took {} seconds'.format(elapsed))

        self.create_bundle_cleanup_tool()

        return status


    def create_add_on_package(self, filename, module_name, with_sources=False):
        """Top level packager driver function for creating addon packages.

        Creates output directory, generates filename, creates the tarball, and measures time.


        Parameters
        ----------
        filename : str
            filename of output bundle
        module_name : str
            name of module to create an add-on package for

        Returns
        -------
        int
            status of tar creation command
        """

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
        status = self.create_single_module_tarball(filename, module, with_sources)

        # Stop the timer
        elapsed = self.stop_timer()
        LOG.write('Tarring took {} seconds'.format(elapsed))

        self.create_bundle_cleanup_tool()

        return status


