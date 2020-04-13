"""Class that will represent a single install module

The building block of the install configuration, InstallModule objects
are used to represent each module defined in the configuration. It stores all module-specific
information pertinent to building and cloning it.
"""

import os

class InstallModule:
    """Class that represents individual install module

    It stores all the information per module in the INSTALL_CONFIG file

    Attributes
    ----------
    name : str
        the name of the module
    version : str
        the desired module tag, or alternatively master
    rel_path : str
        relative path to module
    abs_path : str
        absolute path to module
    url_type : str
        either GIT_URL if using git version control, or WGET_URL if sources hosted in .tar.gz file
    url : str
        url where the git repository or wget download resies
    repository : str
        name of the git repo to clone or wget file to download
    clone : str
        YES or NO, flag to clone the module
    build : str
        YES or NO, flag to build the module
    package : str
        YES or NO, flag to package the module
    custom_build_script_path : str
        path to script used to build module instead of just make
    dependencies : list of str
        list of modules identified as dependencies for module
    """


    def __init__(self, name, version, rel_path, url_type, url, repository, clone, build, package):
        """Constructor for the InstallModule class
        """

        self.name       = name
        self.version    = version
        self.rel_path   = rel_path
        self.abs_path   = None
        self.url_type   = url_type
        self.url        = url
        self.rel_repo = repository
        # Some download links have versions in the name, so we need to replace it with the current version number
        if "$(VERSION)" in repository:
            self.repository = repository.replace("$(VERSION)", self.version, 1)
        else:
            self.repository = repository
        self.clone      = clone
        self.build      = build
        self.package    = package
        self.custom_build_script_path = None

        # List of epics modules that this module depends on
        self.dependencies = []


    def print_info(self, fp = None):
        """Function that prints information about an install module

        if fp is None, will print to stdout, otherwise will print to the fp file pointer

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
        """Function that gets an InstallModule toString
        
        Returns
        -------
        str
            A string representation of the install module
        """

        out = "-----------------------------------------\n"
        out = out + "Module: {}, Version: {}\n".format(self.name, self.version)
        out = out + "Install Location Abs: {}\n".format(self.abs_path)
        out = out + "Install Location Rel: {}\n".format(self.rel_path)
        out = out + "Repository: {}{} w/ Type: {}\n".format(self.url, self.repository, self.url_type)
        out = out + "Clone: {}, Build: {}, Package: {}\n".format(self.clone, self.build, self.package)
        return out