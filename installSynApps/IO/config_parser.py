#
# Class that parses the CONFIG files
#
# Author: Jakub Wlodek
#


import os
import re
from sys import platform
import installSynApps.DataModel.install_config as IC
import installSynApps.DataModel.install_module as IM
from installSynApps.IO import logger as LOG


class ConfigParser:
    """
    Class responsible for parsing the INSTALL_CONFIG file into an InstallConfguration object

    Attributes
    ----------
    configure_path : str
        path to installSynApps configure directory

    Methods
    -------
    check_valid_config_path()
        Checks if confgure path is valid
    parse_line_to_module(line : str, current_url : str, current_url_type : str)
        parses module line into an InstllModule object
    parse_install_config(config_filename=INSTALL_CONFIG)
        main top level function that parses install config file
    generate_default_injector_files(install_config : InstallConfiguration)
        Function that creates some new base default injector files
    read_injector_files(install_config : InstallConfiguration)
        Function that reads the injector files and adds them to install config
    parse_injector_files(injector_file_name : str, install_config : InstallConfiguration)
        Function that parses an injector file and adds it to the install_config
    read_build_flags(install_config : InstallConfiguration)
        Function that reads the build flag files and adds them to install config
    parse_macro_file(macro_file_name : str, install_config : InstallConfiguration)
        Function to parse macro-value pairs and adds them to install config
    parse_custom_build_scripts(install_config : InstallConfiguration)
        Function that checks for custom build scripts
    """


    def __init__(self, configure_path):
        """Constructor for ConfigParser
        """

        self.configure_path = configure_path

        # These modules must be included in an areaDetector binary bundle for the IOC to be able to run
        self.required_in_package = ['EPICS_BASE', 'ASYN', 'BUSY', 'ADCORE', 'ADSUPPORT', 'CALC', 'SNCSEQ', 'SSCAN', 'DEVIOCSTATS', 'AUTOSAVE']


    def check_valid_config_path(self):
        """Function that checks if configure path is valid

        Returns
        -------
        bool
            True if install path is valid, false otherwise
        """

        if os.path.exists(self.configure_path) and os.path.isdir(self.configure_path):
            return True
        elif os.path.exists(self.configure_path) and os.path.isfile(self.configure_path):
            self.configure_path = self.configure_path.rsplit('/', 1)
            return True
        return False


    def parse_line_to_module(self, line, current_url, current_url_type):
        """Function that parses a line in the INSTALL_CONFIG file into an InstallModule object

        Parameters
        ----------
        line : str
            line from table in file
        current_url : str
            url at which module is located
        current_url_type : str
            either GIT_URL or WGET_URL
        
        Returns
        -------
        InstallModule
            module parsed from the table line
        """

        # Remove extra whitespace
        line = re.sub('\t', ' ', line)
        line = re.sub(' +', ' ', line)
        module_components = line.split(' ')
        # If a line is read that isn't in the correct format return None
        if len(module_components) < 6:
            return None
        # line will be in format:
        # NAME   VERSION   RELATIVE_PATH   REPOSITORY   CLONE   BUILD   PACKAGE
        name        = module_components[0]
        version     = module_components[1]
        rel_path    = module_components[2]
        repository  = module_components[3]
        clone       = module_components[4]
        build       = module_components[5]
        if name in self.required_in_package:
            package = "YES"
        # Add length check for compatibility with older configure directories - default package to NO
        elif len(module_components) == 7:
            package = module_components[6]
        else:
            package = "NO"
        # create object from line and return it
        LOG.debug('Parsed install module: {}'.format(name))
        install_module = IM.InstallModule(name, version, rel_path, current_url_type, current_url, repository, clone, build, package)
        return install_module


    def parse_install_config(self, config_filename = "INSTALL_CONFIG", force_location = None, allow_illegal = False):
        """Top level install config parser function

        Parses the self.path_to_configure/config_filename file

        Parameters
        ----------
        config_filename : str
            name of main config file, defaults to INSTALL_CONFIG
        force_location : str
            default to None. if set, will force the install location to its value instead of the one read from file
        allow_illegal : bool
            defaults to false. If True, will load install config even if install location is invalid

        Returns
        -------
        InstallConfiguration
            valid install_config object if parse was successful, or None
        str
            None if there is no error, or a message describing the error
        """

        # Check if exists
        if os.path.exists(self.configure_path + "/" + config_filename):
            # open the configure file
            install_file = open(self.configure_path + "/" + config_filename, "r")

            # variables
            if install_file == None:
                return None, "Couldn't open install file"
            install_config = None
            current_url = "dummy_url.com"
            current_url_type = "GIT_URL"
            install_loc = ""
            message = None

            line = install_file.readline()
            while line:
                line = line.strip()
                if not line.startswith('#') and len(line) > 1:
                    # Check for install location
                    if line.startswith("INSTALL="):
                        if force_location is None:
                            install_loc = line.split('=')[-1]
                            if install_loc.endswith('/'):
                                install_loc = install_loc[:-1]
                        else:
                            install_loc = force_location
                        if install_loc.startswith('/') and platform == 'win32':
                            LOG.debug('Using linux path on windows, prepending C: to path.')
                            install_loc = 'C:' + install_loc
                        # create install config object
                        install_config = IC.InstallConfiguration(install_loc, self.configure_path)
                        # Error checking
                        if install_config.is_install_valid() < 0:
                            if not allow_illegal:
                                return None, 'Permission Error'
                            else:
                                message = 'Permission Error'
                        elif install_config.is_install_valid() == 0:
                            try:
                                os.mkdir(install_config.install_location)
                            except FileNotFoundError:
                                if not allow_illegal:
                                    return None, 'Install filepath not valid'
                                else:
                                    message = 'Install filepath not valid'
                    # URL definition lines
                    elif line.startswith("GIT_URL") or line.startswith("WGET_URL"):
                        current_url = line.split('=')[1]
                        if not current_url.endswith('/'):
                            current_url = current_url + '/'
                        current_url_type = line.split('=')[0]
                    else:
                        # Parse individual module line
                        install_module = self.parse_line_to_module(line, current_url, current_url_type)
                        if install_module is not None and install_config is not None:
                            install_config.add_module(install_module)
                line = install_file.readline()
            
            install_file.close()
            # Read injectors and build flags
            if install_config is None:
                return None, 'Could not find INSTALL defined in given path'
            self.read_injector_files(install_config)
            self.read_build_flags(install_config)
            self.parse_custom_build_scripts(install_config)
            return install_config , message
        else:
            # Configure file not found
            return None, 'Configure Path not found'


    def generate_default_injector_files(self, install_config):
        """Function that creates some new base default injector files

        Parameters
        ----------
        install_config : InstallConfiguration
            currently loaded install configuration into which injector files will be added
        """

        install_config.add_injector_file('AD_RELEASE_CONFIG',   '', '$(AREA_DETECTOR)/configure/RELEASE_PRODS.local')
        install_config.add_injector_file('AUTOSAVE_CONFIG',     '', '$(AREA_DETECTOR)/ADCore/iocBoot/EXAMPLE_commonPlugin_settings.req')
        install_config.add_injector_file('MAKEFILE_CONFIG',     '', '$(AREA_DETECTOR)/ADCore/ADApp/commonDriverMakefile')
        install_config.add_injector_file('PLUGIN_CONFIG',       '', '$(AREA_DETECTOR)/ADCore/iocBoot/EXAMPLE_commonPlugins.cmd')
        # Adds injector required for building QuadEM
        install_config.add_injector_file('QUADEM_RELEASE',      '-include $(AREA_DETECTOR)/configure/RELEASE_PRODS.local', '$(SUPPORT)/quadEM/configure/RELEASE')


    def read_injector_files(self, install_config):
        """Function that reads the injector files and adds them to install config
        
        Parameters
        ----------
        install_config : InstallConfiguration
            currently loaded install configuration into which injector files will be added
        """

        if install_config is None:
            return
        elif not os.path.exists(self.configure_path + '/injectionFiles'):
            self.generate_default_injector_files(install_config)
            return
        num_found = 0
        for file in os.listdir(self.configure_path + '/injectionFiles'):
            if os.path.isfile(self.configure_path + '/injectionFiles/' + file):
                self.parse_injector_file(file, install_config)
                num_found = num_found + 1
        if num_found == 0:
            self.generate_default_injector_files(install_config)


    def parse_injector_file(self, injector_file_name, install_config):
        """Function that parses an injector file and adds it to the install_config

        Parameters
        ----------
        injector_file_name : str
            name of the file
        install_config : InstallConfiguration
            config to add the file to
        """

        fp = open(self.configure_path + '/injectionFiles/' + injector_file_name, 'r')
        contents = ''
        link=''

        line = fp.readline()
        while line:
            if not line.startswith('#') and len(line) > 1:
                if line.startswith('__TARGET_LOC__='):
                    line = line.strip()
                    link = line.split('=')[1]
                else:
                    contents = contents + line

            line = fp.readline()

        fp.close()
        install_config.add_injector_file(injector_file_name, contents, link)


    def read_build_flags(self, install_config):
        """Function that reads the build flag files and adds them to install config
        
        Parameters
        ----------
        install_config : InstallConfiguration
            currently loaded install configuration into which macro-value pairs will be added
        """

        if install_config is None:
            return
        elif not os.path.exists(self.configure_path + '/macroFiles'):
            return
        for file in os.listdir(self.configure_path + '/macroFiles'):
            if os.path.isfile(self.configure_path + '/macroFiles/' + file):
                self.parse_macro_file(file, install_config)


    def parse_macro_file(self, macro_file_name, install_config):
        """Function to parse macro-value pairs and adds them to install config
        
        Parses each individual build flag file into macro-value pairs,
        and appends them to the list stored in the loaded install configuration

        Parameters
        ----------
        macro_file_name : str
            name of the macro file to parse
        install_config : InstallConfiguration
            Loaded intall configuration into which the macros should be parsed
        """

        with open(self.configure_path + '/macroFiles/' + macro_file_name) as fp:
            contents = fp.readlines()

        macros = []
        for line in contents:
            if not line.startswith('#'):
                line = line.strip()
                if len(line) > 1 and '=' in line:
                    macros.append(line.split('='))

        install_config.add_macros(macros)


    def parse_custom_build_scripts(self, install_config):
        """Function that checks for custom build scripts
        """

        # make sure the build script path is absolute
        build_script_folder = os.path.abspath(os.path.join(self.configure_path, 'customBuildScripts'))
        if os.path.exists(build_script_folder):
            for module in install_config.get_module_list():
                for file in os.listdir(build_script_folder):
                    if file.startswith(module.name):
                        module.custom_build_script_path = os.path.join(build_script_folder, file)