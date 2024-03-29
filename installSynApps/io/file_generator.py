"""Module responsible for generating README files and bash build scripts once the package/sources are built
"""


# Python library imports
import os
import sys
from sys import platform
import shutil
import datetime
import subprocess
from subprocess import Popen, PIPE

# InstallSynApps internal imports
import installSynApps
import installSynApps.data_model.install_config as IC
from installSynApps.io import config_writer as WRITER
from installSynApps.io import logger as LOG

# External package used to identify linux distribution version. Note that this adds external
# dependancy, but it is required because the platform.linuxdistro() function is being deprecated
WITH_DISTRO=True
try:
    import distro
except ImportError:
    # user does not have distro installed, so generic name will be used.
    WITH_DISTRO=False


WITH_YAML=True
try:
    import yaml
except ImportError:
    # User does not have pyyaml installed, so dummy IOCs will not have configuration stored in yaml file
    WITH_YAML = False


class FileGenerator:
    """Class responsible for auto-generating install, uninstall, and README files for a given install config

    Attributes
    ----------
    install_config : InstallConfiguration
        currently loaded install configuration
    message : str
        Simple autogenerated message at the top of scripts
    OS : str
        used for naming on linux. Allows for using different bundles for different linux distributions
    """


    def __init__(self, install_config):
        """Constructor for FileGenerator
        """

        self.install_config = install_config
        self.message = "# This script was autogenerated by installSynApps on {}\n \
# The module is available at \
https://github.com/NSLS-II/installSynApps\n\n".format(datetime.datetime.now())

        global WITH_DISTRO
        if platform == 'win32':
            self.OS = 'Windows'
        elif WITH_DISTRO:
            v = distro.linux_distribution(full_distribution_name=False)
            self.OS = '{}_{}'.format(v[0], v[1])
        else:
            self.OS = 'Linux'


    def initialize_dir(self):
        """Function that creates an autogenerated directory
        """

        autogenerated_dir = installSynApps.join_path(self.install_config.install_location, "autogenerated")
        if os.path.exists(autogenerated_dir):
            LOG.debug('Removing existing autogenerated script directory')
            shutil.rmtree(autogenerated_dir)
        
        LOG.debug('Creating autogenerated script directory')
        os.mkdir(autogenerated_dir)


    def find_config_info(self):
        config_name = os.path.basename(self.install_config.path_to_configure)
        config_repo = None
        config_hash = None
        pwd = os.getcwd()

        if os.path.exists(self.install_config.path_to_configure):
            os.chdir(self.install_config.path_to_configure)
            LOG.debug('Checking version info for config at {}'.format(self.install_config.path_to_configure))
            try:
                p = Popen(['git', 'status'], stdout=PIPE, stderr=PIPE)
                p.communicate()
                if p.returncode == 0:
            
                    LOG.debug('Identifying remote for config {}...'.format(config_name))
                    out = subprocess.check_output(['git', 'remote', '-v'], stderr=PIPE)
                    out = out.decode('utf-8')
                    remotes = out.splitlines()
                    for remote in remotes:
                        if remote.startswith('origin'):
                            config_repo = remote.split('\t')[1].split(' ')[0]
                            break
                
                    LOG.debug('Finding current commit hash for config...')
                    out = subprocess.check_output(['git', 'rev-parse', 'HEAD'], stderr=PIPE)
                    config_hash = out.decode('utf-8').strip()
                    LOG.debug('Found config: {} with commit hash {}'.format(config_name, config_hash))
                    LOG.debug('Config remote: {}'.format(config_repo))
                
                else:
                    LOG.debug('Config located at {} is not a git repository.'.format(self.install_config.path_to_configure))
                os.chdir(pwd)
                
            
            except subprocess.CalledProcessError:
                os.chdir(pwd)
                LOG.debug('Failed to find version information for config: {}'.format(config_name))

        return config_name, config_repo, config_hash


    def generate_install(self):
        """Function that generates an install file based on currently loaded install_config
        """

        LOG.debug('Autogenerating bash install script')
        install_fp = open(self.install_config.install_location + "/autogenerated/install.sh", "w+")
        install_fp.write("#!/bin/bash\n")
        
        install_fp.write(self.message)

        for module in self.install_config.get_module_list():
            if module.build == "YES":
                install_fp.write("{}={}\n".format(module.name, module.abs_path))

        for module in self.install_config.get_module_list():
            if module.build == "YES":
                install_fp.write("cd ${}\n".format(module.name))
                install_fp.write("make -sj\n")

        install_fp.close()


    def generate_uninstall(self):
        """Function that generates an uninstall file based on currently loaded install_config
        """

        LOG.debug('Autogenerating bash uninstall script')
        uninstall_fp = open(installSynApps.join_path(self.install_config.install_location, "/autogenerated/uninstall.sh"), "w+")
        uninstall_fp.write("#!/bin/bash\n")

        uninstall_fp.write(self.message)

        modules = self.install_config.get_module_list()
        modules.reverse()

        for module in modules:
            if module.build == "YES":
                uninstall_fp.write("{}={}\n".format(module.name, module.abs_path))

        for module in modules:
            if module.build == "YES":
                uninstall_fp.write("cd ${}\n".format(module.name))
                uninstall_fp.write("make clean uninstall\n")
                uninstall_fp.write("make clean uninstall\n")
    
        modules.reverse()
        uninstall_fp.close()


    def generate_remake_sources(self):
        """Function that creates a bash/batch script for regenerating binaries from sources
        """

        LOG.debug('Autogenerating regenerateSources bash script')
        regenerate_fp = open(installSynApps.join_path(self.install_config.install_location, 'autogenerated', 'regenerateSources.sh'), 'w+')
        regenerate_fp.write('#!/bin/bash\n\ngit clone https://github.com/NSLS-II/installSynApps\n')
        isa_version, isa_commit_hash = installSynApps.find_isa_version()
        regenerate_fp.write('cd installSynApps\n')
        if isa_commit_hash is not None:
            regenerate_fp.write('git checkout {}\n'.format(isa_commit_hash))
        else:
            regenerate_fp.write('git checkout -q {}\n'.format(isa_version))
        abs_loc = os.path.abspath(self.install_config.install_location)
        regenerate_fp.write('./installCLI.py -i {} -c {} -p -y\n\n'.format(installSynApps.join_path(abs_loc, 'regenerated'), installSynApps.join_path(abs_loc, 'build-config')))
        regenerate_fp.close()


    def generate_readme_simple(self):
        """Generates README file based on configuration

        Function that takes the currently loaded install configuration, 
        and writes a readme file describing modules and versions
        """

        if os.path.exists(self.install_config.install_location + "/README"):
            os.remove(self.install_config.install_location + "/README")
        
        readme_fp = open(self.install_config.install_location + "/README", "w+")
        readme_fp.write("Autogenerated installSynApps README file created on {}\n".format(datetime.datetime.now()))
        readme_fp.write("https://github.com/NSLS-II/installSynApps\n")
        readme_fp.write("-------------------------------------------------------\n")
        readme_fp.write("The following modules were installed with the following version numbers:\n\n")
        for module in self.install_config.get_module_list():
            if module.build == "YES":
                readme_fp.write("{} -> {}\n".format(module.name, module.version))
        
        readme_fp.write("-------------------------------------------------------\n")
        readme_fp.write("The following modules were cloned with the given versions but not auto-built\n\n")
        
        for module in self.install_config.get_module_list():
            if module.build == "NO" and module.clone == "YES":
                readme_fp.write("{} -> {}\n".format(module.name, module.version))
        
        readme_fp.close()


    def write_readme_heading(self, text, readme_fp):
        """Simple helper function used to write headings for README file sections
        """

        readme_fp.write('{}\n#{}#\n# {:<61}#\n#{}#\n{}\n\n'.format('#' * 64,
                                                                   ' '* 62,
                                                                   text,
                                                                   ' '* 62,
                                                                   '#' * 64))


    def generate_module_version_info(self, module):
        """Function that gets string with module version information

        Parameters
        ----------
        module : installSynApps.DataModel.install_module.InstallModule
            The module we want to generate the information for
        
        Returns
        -------
        info : str
            String with module name and version information on single line
        """
        current_loc = os.getcwd()
        try:
            if module.url_type == 'GIT_URL':
                LOG.debug('cd {}'.format(module.abs_path))
                os.chdir(module.abs_path)
                LOG.debug('git describe --tags')
                out = subprocess.check_output(['git', 'describe', '--tags'], stderr=PIPE)
                LOG.debug('Checking version for {}'.format(module.name))
                LOG.debug('cd {}'.format(current_loc))
                os.chdir(current_loc)
                LOG.debug('Detected git tag/version: {} for module {}'.format(out.decode("utf-8").strip(), module.name))
                return '{:<16}- {}'.format(module.name, out.decode("utf-8"))
            else:
                LOG.debug('Detected version {} for module {}'.format(module.version, module.name))
                return '{:<16}- {}\n'.format(module.name, module.version)
        except subprocess.CalledProcessError:
            os.chdir(current_loc)
            return ''


    def write_included_modules_to_readme(self, installation_type, add_on_module, readme_fp):
        """Function that writes module + version info to readme file

        Parameters
        ----------
        installation_type : str
            The type of package generated
        add_on_module : installSynApps.DataModel.install_module.InstallModule
            If not None, module being packaged as add on
        readme_fp : file pointer
            Open file pointer for README file.
        """

        for module in self.install_config.get_module_list():
            if not os.path.exists(module.abs_path):
                # If path doesn't exist, do nothing
                pass
            elif installation_type == 'source' and module.build == 'YES':
                # if source, we only care if module was built
                readme_fp.write(self.generate_module_version_info(module))
            elif installation_type == 'bundle' and module.package == 'YES':
                # If bundle, we only include packaged modules
                readme_fp.write(self.generate_module_version_info(module))
            elif installation_type == 'addon' and module.name == add_on_module.name:
                # if add-on, only include add-on module
                readme_fp.write(self.generate_module_version_info(module))


    def grab_configuration_used(self, top_location, module, readme_fp, flat_grab):
        """Function that includes the install configuration into the bundle for reuse.
        
        Parameters
        ----------
        top : str
            resulting location - __temp__
        """

        try:
            isa_version, isa_commit_hash = installSynApps.find_isa_version()
            config_name, config_remote, config_hash = self.find_config_info()

            if not flat_grab:
                self.generate_build_config(top_location, module, readme_fp)
            
            readme_fp.write('Build configuration:\n\n')
            readme_fp.write('installSynApps Version: {}\n'.format(isa_version))
            if config_hash is not None:
                readme_fp.write('{} Version: {}\n\n'.format(config_name, config_hash))
            readme_fp.write('To grab these versions:\n\n    git clone https://github.com/NSLS-II/installSynApps\n    cd installSynApps\n')
            
            if isa_commit_hash is not None:
                readme_fp.write('    git checkout {}\n\n'.format(isa_commit_hash))
            else:
                readme_fp.write('    git checkout -q {}\n'.format(isa_version))

            if config_hash is not None:
                readme_fp.write('    cd ..\n    git clone {}\n    cd {}\n    git checkout {}\n\n'.format(config_remote, config_remote.split('/')[-1], config_hash))

            readme_fp.write('To regenerate sources for this bundle, grab installSynApps, and run:\n\n')
            readme_fp.write('    ./installCLI.py -c $BUILD_CONFIG -i $INSTALL_LOCATION -p\n\n')
            readme_fp.write('where $BUILD_CONFIG is the path to the {} directory,\n'.format(config_name))
            readme_fp.write('and $INSTALL_LOCATION is your target install path.\n\n{}\n'.format('-' * 64))
            readme_fp.write('{:<20}{}\n'.format('Python 3 Version:', sys.version.split()[0]))
            readme_fp.write('{:<20}{}\n'.format('OS Class:', self.OS))
            readme_fp.write('{:<20}{}\n'.format('Build Date:', datetime.datetime.now()))
        except:
            LOG.debug('Failed to copy install configuration into bundle.')


    def generate_readme(self, installation_name, installation_type='source', readme_path=None, module=None, flat_grab=False):
        """Function used to generate a README file that includes version/build information

        Parameters
        ----------
        installation_name : str
            Name of the output source/binary bundle
        installation_type : str
            Type of installation that a README file is generated for
        readme_path : str
            Non-standard readme path. Standard is install_location/README
        module : installSynApps.DataModel.install_module.InstallModule
            Default none. If not None, module that is being packaged as add-on
        """

        # Open the correct readme file path in write mode, set the top location
        if readme_path is None:
            if os.path.exists(installSynApps.join_path(self.install_config.install_location, 'README')):
                os.remove(installSynApps.join_path(self.install_config.install_location, 'README'))
            readme_fp = open(installSynApps.join_path(self.install_config.install_location, 'README'), 'w')
            top_location = self.install_config.install_location
        else:
            readme_fp = open(readme_path, 'w')
            top_location = installSynApps.join_path('__temp__', installation_name)

        # Write heading based on type of installation
        if installation_type == 'source':
            self.write_readme_heading('Source Package - {}'.format(installation_name), readme_fp)
        elif installation_type == 'bundle':
            self.write_readme_heading('Bundle - {}'.format(installation_name), readme_fp)
        elif installation_type == 'addon':
            self.write_readme_heading('Add-On - {}'.format(installation_name), readme_fp)
        
        # Grab some basic version info
        isa_version, _ = installSynApps.find_isa_version()
        config_name, config_repo, config_version = self.find_config_info()

        readme_fp.write('Package generated using installSynApps version: {}\n\n'.format(isa_version))
        if config_version is not None:
            readme_fp.write('Configuration repository: {}\nConfiguration directory: {}\nConfiguration commit hash: {}\n'.format(config_repo, config_name, config_version))
        
        if installation_type == 'source':
            readme_fp.write('NOTE: To perform development using this bundle, run the repoint_bundle.sh script to edit RELEASE file locations.\n')
        
        readme_fp.write('\nModule versions used in this deployment:\n')
        if module is not None:
            readme_fp.write('\nAdd-On should be located here: {}.\n\n'.format(module.rel_path))
        readme_fp.write('[module name] - [git tag]\n\n')

        # Get included modules + versions
        self.write_included_modules_to_readme(installation_type, module, readme_fp)

        # If it is an add-on-package, list what modules it was built against
        if module is not None:
            readme_fp.write('\nThe module was built against:\n\n')
            self.write_included_modules_to_readme('source', None, readme_fp)

        readme_fp.write('\n\n')

        # Grab some final build configuration information, and close the file.
        self.grab_configuration_used(top_location, module, readme_fp, flat_grab)
        readme_fp.close()


    def generate_license(self, bundle_path):
        """Function for generating license file for bundle

        Parameters
        ----------
        bundle_path : str
            path to the temp staging location for bundle before tarring
        """

        fp = open(installSynApps.join_path(bundle_path, 'LICENSE'), 'w')

        #TODO - Allow for specifying license type

        fp.close()


    def generate_build_config(self, top_location, module, readme_fp):
        """Function that writes the build configuration used to create the source/binary package.

        Parameters
        ----------
        top_location : str
            Output location of the package
        module : installSynApps.DataModel.install_module.InstallModule
            If not None, module being packaged as add on
        readme_fp : file pointer
            Open file pointer for README file.
        """

        if module is None:
            LOG.write('Copying build configuration into bundle.')
            writer = WRITER.ConfigWriter(self.install_config)
            build_config_dir = installSynApps.join_path(top_location, 'build-config')
            writer.write_install_config(filepath=build_config_dir, overwrite_existing=True)
            self.write_readme_heading('Build environment version information', readme_fp)
        else:
            self.write_readme_heading('Implementing add on in exisitng bundle', readme_fp)
            readme_fp.write('This add on tarball contains a folder with a compiled version of {}.\n'.format(module.name))
            readme_fp.write('To use it with an existing bundle, please copy the folder into {} in the target bundle.\n'.format(module.rel_path))
            readme_fp.write('It is also recommended to edit the build-config for the bundle to reflect the inclusion of this module.\n\n')


    def autogenerate_all(self, create_simple_readme=True):
        """Top level function that calls all autogeneration functions

        Parameters
        ----------
        create_simple_readme : bool
            If true, generate simplified README file based on install config
        """

        if platform == 'win32':
            LOG.debug('Windows machine detected, skipping script generation.')
        else:
            LOG.debug('Generating auto-(un)install helper scripts')
            self.initialize_dir()
            self.generate_install()
            self.generate_uninstall()
            self.generate_remake_sources()
        if create_simple_readme:
            self.generate_readme_simple()