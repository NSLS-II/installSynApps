"""A file containing representations of install configurations.

The core Data representation for installSynApps. An InstallConfiguration object
is parsed from a configuration, and is then used throughout the build process.

InjectorFile objects are used for representing text that need to be injected
into configuration files prior to builds.
"""


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
    motor_path : str
        abs path to install location of EPICS motor
    module_map : dict of str -> int
        Dictionary storing relation of module names to build index
    injector_files : list of InjectorFile
        list of injector files loaded by install configuration
    build_flags : list of list of str
        list of macro-value pairs enforced at build time

    Methods
    -------
    is_install_valid() : int
        Function that checks if given install location is valid
    add_module(module : InstallModule)
        Function that appends a new module to the list of InstallModules
    add_injector_file(name : str, contents : str, target : str)
        Creates new injector file object and adds it to list
    add_macros(macro_list : list of list of str)
        appends macros to build flag list
    get_module_list() : List InstallModule
        Function that gets the current list of InstallModules
    get_module_by_name(name : str)
        gets module given module name
    get_module_build_index(name : str)
        returns module build order index
    get_core_version()
        returns ADCORE version
    swap_module_positions(module_A : str, module_B : str)
        swaps build index positions o modules A and B
    convert_path_abs(rel_path : str) : str
        Function that converts a relative path to an absolute path based on locations of install, base, support, and ad
    print_installation_info(fp=None)
        Method that prints information about the given install module
    get_printable_string()
        gets install configuration info into string
    """


    def __init__(self, install_location, path_to_configure):
        """Constructor for the InstallConfiguration object
        """

        self.path_to_configure = path_to_configure

        self.install_location = install_location
        self.modules = []

        # Dict that maps module name to index in module list for easier searching.
        self.module_map = {}

        self.injector_files = []
        self.build_flags = []

        # Paths to the three install location paths used for relative path correction
        self.base_path = None
        self.support_path = None
        self.ad_path = None
        self.motor_path = None

    
    def is_install_valid(self):
        """Function that checks if given install location is valid

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
        """Function that adds a module to the InstallConfiguration module list

        First checks if parameter is a valid InstallModule, then sets the config, and abs path,
        then if it is one of the three key modules to track, sets the appropriate variables. Also,
        add the module to the map of modules which will keep track of which position each module is 
        in in the list/build order

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
            elif module.name == "MOTOR":
                self.motor_path = module.abs_path
            
            self.module_map[module.name] = len(self.modules)
            self.modules.append(module)


    def add_injector_file(self, name, contents, target):
        """Function that adds a new injector file to the install_config object
        
        Parameters
        ----------
        name : str
            name of the file
        contents : str
            The contents of the file
        target : str
            The target location file into which contents will be injected.
        """

        new_injector = InjectorFile(self.path_to_configure, name, contents, target)
        self.injector_files.append(new_injector)


    def add_macros(self, macro_list):
        """Function that adds macro-value pairs to a list of macros

        Parameters
        ----------
        macro_list : list of [str, str]
            list of new macros to append
        """

        self.build_flags = self.build_flags + macro_list


    def get_module_list(self):
        """Function that gets the list of modules in the configuration

        Returns
        -------
        List
            self.modules - list of modules to install in this install configuration
        """

        return self.modules


    def get_module_by_name(self, name):
        """Function that returns install module object given module name
        
        Uses module name as a key in a dictionary to return reference to given module object.

        Parameters
        ----------
        name : str
            Module name
    
        Returns
        -------
        obj - InstallModule
            Return matching module, or None if not found.
        """

        if name in self.module_map.keys():
            return self.modules[self.module_map[name]]
        else:
            return None


    def get_module_build_index(self, name):
        """Function that returns the index in the build order for the module
        
        Used for ensuring dependencies are built before lower level packages.

        Parameters
        ----------
        name : str
            Module name
        
        Returns
        -------
        int
            Index of module in build order if found, otherwise -1
        """

        if name in self.module_map.keys():
            return self.module_map[name]
        else:
            return -1


    def get_core_version(self):
        """Funciton that returns selected version of ADCore
        """

        return self.get_module_by_name('ADCORE').version


    def swap_module_positions(self, module_A, module_B):
        """Swaps build order of modules

        Used to ensure dependencies are built before lower level packages

        Parameters
        ----------
        module_A : str
            Name of first module
        module_B : str
            Name of second module
        """

        index_A = self.get_module_build_index(module_A)
        index_B = self.get_module_build_index(module_B)
        if index_A >= 0 and index_B >= 0:
            temp_A = self.get_module_by_name(module_B)
            temp_B = self.get_module_by_name(module_A)
            self.modules[index_A] = temp_A
            self.modules[index_B] = temp_B
            self.module_map[module_A] = index_B
            self.module_map[module_B] = index_A


    def convert_path_abs(self, rel_path):
        """Function that converts a given modules relative path to an absolute path

        If the macro name can be found in the list of accounted for modules, replace it with that module's absolute path

        Parameters
        ----------
        rel_path : str
            The relative installation path for the given module

        Returns
        -------
        str
            The absolute installation path for the module. (Macros are replaced)
        """

        temp = rel_path.split('/', 1)[-1]
        if "$(INSTALL)" in rel_path and self.install_location != None:
            return os.path.join(self.install_location, temp)
        elif "$(EPICS_BASE)" in rel_path and self.base_path != None:
            return os.path.join(self.base_path, temp)
        elif "$(SUPPORT)" in rel_path and self.support_path != None:
            return os.path.join(self.support_path, temp)
        elif "$(AREA_DETECTOR)" in rel_path and self.ad_path != None:
            return os.path.join(self.ad_path, temp)
        elif "$(MOTOR)" in rel_path and self.motor_path != None:
            return os.path.join(self.motor_path, temp)
        elif "$(" in rel_path:
            macro_part = rel_path.split(')')[0]
            rel_to = macro_part.split('(')[1]
            rel_to_module = self.get_module_by_name(rel_to)
            if rel_to_module is not None:
                return os.path.join(rel_to_module.abs_path, temp)

        return rel_path


    def print_installation_info(self, fp = None):
        """Function that prints installation info
        
        Prints list of all modules including clone/build/package information

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
        """Function that gets a toString for an InstallConfigurations

        Returns
        -------
        str
            A string representing the install configuration
        """

        out = "--------------------------------\n"
        out = out + "Install Location = {}\n".format(self.install_location)
        out = out + "This Install Config is saved at {}\n".format(self.path_to_configure)
        for module in self.modules:
            if module.clone == 'YES':
                out = out + module.get_printable_string()
        return out


    def get_module_names_list(self):
        """Function that gets list of modules being built

        Returns
        -------
        list of str
            list of module names that are set to build
        """

        out = []
        for module in self.modules:
            if module.build == 'YES':
                out.append(module.name)
        return out


class InjectorFile:
    """Class that represents an injector file and stores its name, contents, and target

    Injector file classes are used to represent data that needs to be appended to target files 
    at build time. Used to add to commonPlugins, commonPlugin_settings, etc.

    TODO: This class can probably be abstracted into a simpler data structure (since its used as a struct anyway)

    Attributes
    ----------
    path_to_configure : str
        path to the configure dir that houses this injector file
    name : str
        name of the file
    contents : str
        The contents of the file
    target : str
        The target location file into which contents will be injected.
    """

    def __init__(self, path_to_configure, name, contents, target):
        """Constructor of InjectorFile class
        """

        self.path_to_configure = path_to_configure
        self.name = name
        self.contents = contents
        self.target = target