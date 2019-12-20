"""Class that is responsible for writing Install Configurations

Converts datamodel objects back into text files
"""


import datetime
import os
import errno
import shutil
from installSynApps.DataModel import *
from installSynApps.IO import logger as LOG

class ConfigWriter:
    """Class that is responsible for writing Install Configurations

    Attributes
    ----------
    install_config : InstallConfiguration
        install config to write

    Methods
    -------
    write_injector_files(filepath : str)
       Helper Function for writing injector files from install config
    write_build_flags(filepath : str)
       Helper Function for writing build flags from install config
    write_install_config(filepath : str)
        function that writes an install config "saving" it
    """

    def __init__(self, install_config):
        """ constructor for ConfigWriter """

        self.install_config = install_config


    def write_injector_files(self, filepath):
        """Helper Function for writing injector files from install config

        Parameters
        ----------
        filepath : str
            Path into which we wish to save configuration
        """

        # for each injector file write it with its target location
        for injector_file in self.install_config.injector_files:
            LOG.debug('Saving injector file {} with target {}'.format(injector_file, injector_file.target))
            new_fp = open(filepath + "/injectionFiles/" + injector_file.name, 'w')
            new_fp.write('# Saved by installSynApps on {}\n'.format(datetime.datetime.now()))
            new_fp.write('__TARGET_LOC__={}\n\n'.format(injector_file.target))
            new_fp.write(injector_file.contents)
            new_fp.close()


    def write_build_flags(self, filepath):
        """Helper Function for writing build flags from install config

        Parameters
        ----------
        filepath : str
            Path into which we wish to save configuration
        """

        new_build_flag = open(filepath + "/macroFiles/BUILD_FLAG_CONFIG", 'w')
        new_build_flag.write('# Saved by installSynApps on {}\n\n'.format(datetime.datetime.now()))
        for macro_pair in self.install_config.build_flags:
            LOG.debug('Writing build flag {}={}'.format(macro_pair[0], macro_pair[1]))
            new_build_flag.write('{}={}\n'.format(macro_pair[0], macro_pair[1]))
        new_build_flag.close()


    def write_custom_build_scripts(self, filepath):
        """Helper Function for writing custom build scripts of modules

        Parameters
        ----------
        filepath : str
            Path into which we wish to save configuration
        """

        build_script_out = os.path.join(filepath, 'customBuildScripts')
        for module in self.install_config.get_module_list():
            old_script = module.custom_build_script_path
            if old_script is not None:
                if os.path.exists(old_script):
                    LOG.debug('Copying module custom build script: {}'.format(old_script))
                    try:
                        shutil.copyfile(old_script, os.path.join(build_script_out, os.path.basename(old_script)))
                    except:
                        LOG.debug('Encountered error copying: {}'.format(old_script))
                else:
                    LOG.debug('Could not find build script at: {}'.format(old_script))


    def write_install_config(self, filepath='addtlConfDirs/config{}'.format(datetime.date.today()), overwrite_existing=False):
        """Function that saves loaded install configuration

        Main saving function for writing install config. Can create a save directory, then saves 
        main install configuration, build flags, and injector files.

        Parameters
        ----------
        filepath : str
            defaults to addtlConfDirs/config$DATE. The filepath into which to save the install configuration

        Returns
        -------
        bool
            True if successful, False otherwise
        str
            None if successfull, otherwise error message
        """

        if overwrite_existing and os.path.exists(filepath):
            try:
                shutil.rmtree(filepath)
            except PermissionError:
                return False, 'Insufficeint Permissions'

        # Check if path exists, create it if it doesn't
        if not os.path.exists(filepath):
            try:
                os.mkdir(filepath)
            except OSError as err:
                if err.errno == errno.EACCES:
                    return False, 'Permission Error!'
                elif err.errno == errno.EEXIST:
                    return False, 'Path already exists!'
                elif err.errno == errno.ENOSPC:
                    return False, 'No space on device!'
                elif err.errno == errno.EROFS:
                    return False, 'Read Only File System!'
                else:
                    return False, 'Unknown Error'
        try:
            os.mkdir(os.path.join(filepath, 'injectionFiles'))
            os.mkdir(os.path.join(filepath, 'macroFiles'))
            os.mkdir(os.path.join(filepath, 'customBuildScripts'))
        except OSError:
            LOG.write('Failed to make configuration directories!')
            return False, 'Unknown Error'

        LOG.debug('Writing injector files.')
        self.write_injector_files(filepath)

        LOG.debug('Writing build flags.')
        self.write_build_flags(filepath)

        LOG.debug('Writing custom build scripts.')
        self.write_custom_build_scripts(filepath)

        LOG.debug('Writing INSTALL_CONFIG file.')
        new_install_config = open(os.path.join(filepath, "INSTALL_CONFIG"), "w+")
        new_install_config.write('#\n# INSTALL_CONFIG file saved by installSynApps on {}\n#\n\n'.format(datetime.datetime.now())) 
        new_install_config.write("INSTALL={}\n\n\n".format(self.install_config.install_location))

        new_install_config.write('#MODULE_NAME    MODULE_VERSION          MODULE_PATH                             MODULE_REPO         CLONE_MODULE    BUILD_MODULE    PACKAGE_MODULE\n')
        new_install_config.write('#--------------------------------------------------------------------------------------------------------------------------------------------------\n')

        current_url = ""
        for module in self.install_config.get_module_list():
            if module.url != current_url:
                new_install_config.write("\n{}={}\n\n".format(module.url_type, module.url))
                current_url = module.url
            new_install_config.write("{:<16} {:<20} {:<40} {:<24} {:<16} {:<16} {}\n".format(module.name, module.version, module.rel_path, module.rel_repo, module.clone, module.build, module.package))

        new_install_config.close()
        return True, None