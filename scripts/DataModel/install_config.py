#
# A class representing an install configuration.
# This will potentially allow for multiple install configurations in
# the future.
#
# Author: Jakub Wlodek
#


import os
import install_module as IM


class InstallConfiguration:
    """
    Class that represents an Install Configuration for installSynApps
    
    It stores the top level install_location, the path to the configuration files,
    any OS specific configurations, and the actual list of modules that will be 
    installed.

    Attributes
    ----------
    install_location : str
        path to top level install location
    path_to_configure : str
        path to configure folder of installSynApps
    os_specific : str
        flag determining any os-specific behavior
    modules : List of InsallModule
        list of InstallModule objects representing the modules that will be installed
    base_path : str
        abs path to install location of EPICS base
    support_path : str
        abs path to install location of EPICS support modules
    ad_path : str
        abs path to install location of EPICS area detector

    Methods
    -------
    is_install_valid()
        Function that checks if given install location is valid
    os_config_exists()
        Function that checks if os configuration is valid
    add_module(module : InstallModule)
        Function that appends a new module to the list of InstallModules
    get_module_list()
        Function that gets the current list of InstallModules
    convert_path_abs(rel_path : str)
        Function that converts a relative path to an absolute path based on locations of install, base, support, and ad
    """


    def __init__(self, install_location, path_to_configure, os_specific = "DEFAULT"):
        """
        Constructor for the InstallConfiguration object

        Parameters
        ----------
        self : InstallConfiguration
            Self object
        install_location : str
            Path of the target install location
        os_specific : str
            String deciding if install should use any custom OS-Specific install config
        """

        self.os_specific = os_specific
        self.path_to_configure = path_to_configure

        if os_specific != "DEFAULT":
            if not self.os_config_exists():
                self.os_specific = "DEFAULT"

        self.install_location = install_location
        self.modules = []

        # Paths to the three install location paths used for relative path correction
        self.base_path = None
        self.support_path = None
        self.ad_path = None

    
    def is_install_valid(self):
        """
        Function that checks if given install location is valid

        Parameters
        ----------
        self : InstallConfiguration
            Self object

        Returns
        -------
        int
            1 if the path is valid, 0 if it does not exist, -1 if the user doesn't 
            have permissions to write to it.
        """

        valid = 1
        if not os.path.exists(install_location):
            valid = 0
        elif not os.access(self.install_location, os.W_OK | os.X_OK):
            valid = -1
        return valid



    def os_config_exists(self):
        """
        Function that checks if given os has a specific install config

        Parameters
        ----------
        self : InstallConfiguration
            Self object

        Returns
        -------
        int
            True if it does exist, otherwise False
        """

        exists = False
        for file in os.listdir(self.path_to_configure +"/os-specific"):
            if os.path.isfile(self.path_to_configure +"/os-specific/"+file):
                if self.os_specific in file:
                    exists = True

        return exists


    def add_module(self, module):
        """
        Function that adds a module to the InstallConfiguration module list

        First checks if parameter is a valid InstallModule, then sets the config, and abs path,
        then if it is one of the three key modules to track, sets the appropriate variables

        Parameters
        ----------
        module : InstallModule
            new installation module being added.
        """

        if isinstance(module, IM.InstallModule):
            # Sets the modules config to this, and updates the abs path
            module.set_install_config(self)

            # Key paths to track
            if module.name == "EPICS_BASE":
                self.base_path = module.abs_path
            elif module.name == "SUPPORT":
                self.support_path = module.abs_path
            elif module.name == "AREA_DETECTOR":
                self.ad_path = module.abs_path
            
            self.modules.append(module)


    def get_module_list(self):
        """
        Function that adds a module to the InstallConfiguration module list

        Parameters
        ----------
        self : InstallConfiguration
            Self object

        Returns
        -------
        List
            self.modules - list of modules to install in this install configuration
        """

        return self.modules


    def convert_path_abs(self, rel_path):
        """
        Function that converts a given modules relative path to an absolute path

        Parameters
        ----------
        rel_path : str
            The relative installation path for the given module

        Returns
        -------
        Path : str
            The absolute installation path for the module. (Macros are replaced)
        """

        temp = rel_path.split('/', 1)[-1]
        if "$(INSTALL)" in rel_path and self.install_location != None:
            return self.install_location + "/" + temp
        elif "$(EPICS_BASE)" in rel_path and self.base_path != None:
            return self.base_path + "/" + temp
        elif "$(SUPPORT)" in rel_path and self.support_path != None:
            return self.support_path + "/" + temp
        elif "$(AREA_DETECTOR)" in rel_path and self.ad_path != None:
            return self.ad_path + "/" + temp
        else:
            return None
        