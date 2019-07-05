#
# A class representing an install configuration.
# This will potentially allow for multiple install configurations in
# the future.
#
# Author: Jakub Wlodek
#


import os
import installSynApps.DataModel.install_module as IM


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
    is_install_valid() : int
        Function that checks if given install location is valid
    add_module(module : InstallModule)
        Function that appends a new module to the list of InstallModules
    get_module_list() : List InstallModule
        Function that gets the current list of InstallModules
    convert_path_abs(rel_path : str) : str
        Function that converts a relative path to an absolute path based on locations of install, base, support, and ad
    print_installation_info(fp=None)
        Method that prints information about the given install module
    """


    def __init__(self, install_location, path_to_configure):
        """Constructor for the InstallConfiguration object"""

        self.path_to_configure = path_to_configure

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
        if not os.path.exists(self.install_location):
            valid = 0
        elif not os.access(self.install_location, os.W_OK | os.X_OK):
            valid = -1
        return valid


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
            # Updates the abs path
            module.abs_path = self.convert_path_abs(module.rel_path)

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


    def get_core_version(self):
        """
        Funciton that returns selected version of ADCore
        """

        for module in self.get_module_list():
            if module.name == "ADCORE":
                return module.version


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
            return rel_path


    def print_installation_info(self, fp = None):
        """
        Function that prints installation info, along with the info for all modules being cloned

        Parameters
        ----------
        fp = None : file pointer
            Optional pointer to an external log file
        """

        if fp == None:
            print(self.get_printable_string().strip())
        else:
            fp.write(self.get_printable_string())


    def get_printable_string(self):
        """ Function that gets a toString for an InstallConfigurations """

        out = "--------------------------------\n"
        out = out + "Install Location = {}\n".format(self.install_location)
        out = out + "This Install Config is saved at {}\n".format(self.path_to_configure)
        for module in self.modules:
            if module.clone == 'YES':
                out = out + module.get_printable_string()
        return out