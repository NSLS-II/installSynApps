"""A file containing representations of install configurations.

The core Data representation for installSynApps. An InstallConfiguration object
is parsed from a configuration, and is then used throughout the build process.

InjectorFile objects are used for representing text that need to be injected
into configuration files prior to builds.
"""


import os
import installSynApps
from installSynApps.data_model.install_module import InstallModule as IM


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
    """


    def __init__(self, install_location, path_to_configure):
        """Constructor for the InstallConfiguration object
        """

        # Paths to configure and output locations
        self.path_to_configure  = path_to_configure
        self.install_location   = os.path.abspath(install_location)

        # Modules loaded into install config
        self.modules        = []

        # Dict that maps module name to index in module list for easier searching.
        self.module_map     = {}

        self.injector_files = []
        self.build_flags    = []

        # Paths to the three install location paths used for relative path correction
        self.base_path      = None
        self.support_path   = None
        self.ad_path        = None
        self.motor_path     = None

    
    def is_install_valid(self):
        """Function that checks if given install location is valid

        Parameters
        ----------
        self : InstallConfiguration
            Self object

        Returns
        -------
        bool
            True if install location is valid, false otherwise
        str
            Error message if applicable, None otherwise
        """

        valid = True
        message = None
        target = self.install_location

        if not os.path.exists(target):
            target = os.path.dirname(self.install_location)

        if not os.path.exists(target):
            valid = False
            message = 'Install location and parent directory do not exist'
        elif not os.access(target, os.W_OK | os.X_OK):
            valid = False
            message = 'Permission Error: {}'.format(target)
        
        return valid, message


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

        if isinstance(module, IM):
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
            return installSynApps.join_path(self.install_location, temp)
        elif "$(EPICS_BASE)" in rel_path and self.base_path != None:
            return installSynApps.join_path(self.base_path, temp)
        elif "$(SUPPORT)" in rel_path and self.support_path != None:
            return installSynApps.join_path(self.support_path, temp)
        elif "$(AREA_DETECTOR)" in rel_path and self.ad_path != None:
            return installSynApps.join_path(self.ad_path, temp)
        elif "$(MOTOR)" in rel_path and self.motor_path != None:
            return installSynApps.join_path(self.motor_path, temp)
        elif "$(" in rel_path:
            macro_part = rel_path.split(')')[0]
            rel_to = macro_part.split('(')[1]
            rel_to_module = self.get_module_by_name(rel_to)
            if rel_to_module is not None:
                return installSynApps.join_path(rel_to_module.abs_path, temp)

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



def generate_default_install_config(target_install_loc='/epics', update_versions=False, with_pva=True):

    config = InstallConfiguration(target_install_loc, None)
    
    y   = 'YES'
    n   = 'NO'
    gu  = 'GIT_URL'
    wu  = 'WGET_URL'
    
    base_org    = 'https://github.com/epics-base/'
    syn_org     = 'https://github.com/EPICS-synApps/'
    mod_org     = 'https://github.com/epics-modules/'
    ad_org      = 'https://github.com/areaDetector/'
    seq_rel     = 'http://www-csr.bessy.de/control/SoftDist/sequencer/releases/'
    psi_org     = 'https://github.com/paulscherrerinstitute/'


    # Add core modules that will generally always be built
    config.add_module(IM("EPICS_BASE",      "R7.0.3",   "$(INSTALL)/base",      gu, base_org,   "epics-base", y, y, y))
    config.add_module(IM("SUPPORT",         "R6-1",     "$(INSTALL)/support",   gu, syn_org,    "support",  y, y, n))
    config.add_module(IM("CONFIGURE",       "R6-1",     "$(SUPPORT)/configure", gu, syn_org,    "configure", y, y, n))
    config.add_module(IM("UTILS",           "R6-1",     "$(SUPPORT)/utils",     gu, syn_org,    "utils",    y, y, n))
    config.add_module(IM("SNCSEQ",          "2.2.8",    "$(SUPPORT)/seq",       wu, seq_rel,    "seq-2.2.8.tar.gz", y, y, y))
    config.add_module(IM("IPAC",            "2.15",     "$(SUPPORT)/ipac",      gu, mod_org,    "ipac",     y, y, y))
    config.add_module(IM("ASYN",            "R4-37",    "$(SUPPORT)/asyn",      gu, mod_org,    "asyn",     y, y, y))
    config.add_module(IM("AUTOSAVE",        "R5-10",    "$(SUPPORT)/autosave",  gu, mod_org,    "autosave", y, y, y))
    config.add_module(IM("BUSY",            "R1-7-2",   "$(SUPPORT)/busy",      gu, mod_org,    "busy",     y, y, y))
    config.add_module(IM("CALC",            "R3-7-3",   "$(SUPPORT)/calc",      gu, mod_org,    "calc",     y, y, y))
    config.add_module(IM("DEVIOCSTATS",     "master",   "$(SUPPORT)/iocStats",  gu, mod_org,    "iocStats", y, y, y))
    config.add_module(IM("SSCAN",           "R2-11-3",  "$(SUPPORT)/sscan",     gu, mod_org,    "sscan",    y, y, y))
    config.add_module(IM("IPUNIDIG",        "R2-11",    "$(SUPPORT)/ipUnidig",  gu, mod_org,    "ipUnidig", y, y, y))

    # Some modules that are commonly needed
    config.add_module(IM("XSPRESS3",        "master",   "$(SUPPORT)/xspress3",  gu, mod_org, "xspress3", y, y, y))
    config.add_module(IM("MOTOR",           "R7-1",     "$(SUPPORT)/motor",     gu, mod_org, "motor", y, y, y))
    config.add_module(IM("QUADEM",          "R9-3",     "$(SUPPORT)/quadEM",    gu, mod_org, "quadEM", y, y, y))
    config.add_module(IM("STREAM",          "2.8.10",   "$(SUPPORT)/stream",    gu, psi_org, "StreamDevice", y, y, y))

    # AreaDetector and commonly used drivers
    config.add_module(IM("AREA_DETECTOR",   "R3-8",     "$(SUPPORT)/areaDetector",          gu, ad_org, "areaDetector", y, y, n))
    config.add_module(IM("ADSUPPORT",       "R1-9",     "$(AREA_DETECTOR)/ADSupport",       gu, ad_org, "ADSupport",    y, y, y))
    config.add_module(IM("ADCORE",          "R3-8",     "$(AREA_DETECTOR)/ADCore",          gu, ad_org, "ADCore",       y, y, y))
    config.add_module(IM("ADPERKINELMER",   "master",   "$(AREA_DETECTOR)/ADPerkinElmer",   gu, ad_org, "ADPerkinElmer", n, n, n))
    config.add_module(IM("ADGENICAM",       "master",   "$(AREA_DETECTOR)/ADGenICam",       gu, ad_org, "ADGenICam",    n, n, n))
    config.add_module(IM("ADANDOR3",        "master",   "$(AREA_DETECTOR)/ADAndor3",        gu, ad_org, "ADAndor3",     n, n, n))
    config.add_module(IM("ADPROSILICA",     "R2-5",     "$(AREA_DETECTOR)/ADProsilica",     gu, ad_org, "ADProsilica",  n, n, n))
    config.add_module(IM("ADSIMDETECTOR",   "R2-10",    "$(AREA_DETECTOR)/ADSimDetector",   gu, ad_org, "ADSimDetector", n, n, n))
    config.add_module(IM("ADPILATUS",       "R2-8",     "$(AREA_DETECTOR)/ADPilatus",       gu, ad_org, "ADPilatus",    n, n, n))
    config.add_module(IM("ADMERLIN",        "master",   "$(AREA_DETECTOR)/ADMerlin",        gu, ad_org, "ADMerlin",     n, n, n))
    config.add_module(IM("ADARAVIS",        "master",   "$(AREA_DETECTOR)/ADAravis",        gu, ad_org, "ADAravis",     n, n, n))
    config.add_module(IM("ADEIGER",         "R2-6",     "$(AREA_DETECTOR)/ADEiger",         gu, ad_org, "ADEiger",      n, n, n))
    config.add_module(IM("ADVIMBA",         "master",   "$(AREA_DETECTOR)/ADVimba",         gu, ad_org, "ADVimba",      n, n, n))
    config.add_module(IM("ADPOINTGREY",     "master",   "$(AREA_DETECTOR)/ADPointGrey",     gu, ad_org, "ADPointGrey",  n, n, n))
    config.add_module(IM("ADANDOR",         "R2-8",     "$(AREA_DETECTOR)/ADAndor",         gu, ad_org, "ADAndor",      n, n, n))
    config.add_module(IM("ADDEXELA",        "R2-3",     "$(AREA_DETECTOR)/ADDexela",        gu, ad_org, "ADDexela",     n, n, n))
    config.add_module(IM("ADMYTHEN",        "master",   "$(AREA_DETECTOR)/ADMythen",        gu, ad_org, "ADMythen",     n, n, n))
    config.add_module(IM("ADURL",           "master",   "$(AREA_DETECTOR)/ADURL",           gu, ad_org, "ADURL",        n, n, n))


    common_plugins_str = 'dbLoadRecords("$(DEVIOCSTATS)/db/iocAdminSoft.db", "IOC=$(PREFIX)")\n'
    autosave_str = 'file "sseqRecord_settings.req",     P=$(P),  S=AcquireSequence\n'


    if with_pva:
        autosave_str += 'file "NDPva_settings.req", P=$(P), R=Pva1:\n'

        common_plugins_str += 'NDPvaConfigure("PVA1", $(QSIZE), 0, "$(PORT)", 0, $(PREFIX)Pva1:Image, 0, 0, 0)\n' \
                    'dbLoadRecords("NDPva.template",  "P=$(PREFIX),R=Pva1:, PORT=PVA1,ADDR=0,TIMEOUT=1,NDARRAY_PORT=$(PORT)")\n' \
                    '# Must start PVA server if this is enabled\n' \
                    'startPVAServer\n' \
                        
    config.add_injector_file('PLUGIN_CONFIG', common_plugins_str, '$(AREA_DETECTOR)/ADCore/iocBoot/EXAMPLE_commonPlugins.cmd')
    config.add_injector_file('AUTOSAVE_CONFIG', autosave_str, '$(AREA_DETECTOR)/ADCore/iocBoot/EXAMPLE_commonPlugin_settings.req')
    
    if update_versions:
        installSynApps.sync_all_module_tags(config)

    return config