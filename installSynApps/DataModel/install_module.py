#
# Class that will represent a single install module
#
# Author: Jakub Wlodek
#

import os

class InstallModule:
    """
    Class that represents individual install module

    It stores all the information per module in the INSTALL_CONFIG file

    Attributes
    ----------
    name : str
        the name of the module
    version : str
        the desired module tag, or alternatively master
    rel_path : str
        relative path to install, base, support, or area_detector
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

    Methods
    -------
    print_info(fp=None)
        Method that prints information about the given install module
    """


    def __init__(self, name, version, rel_path, url_type, url, repository, clone, build):
        """Constructor for the InstallModule class"""

        self.name       = name
        self.version    = version
        self.rel_path   = rel_path
        self.abs_path   = None
        self.url_type   = url_type
        self.url        = url
        # Some download links have versions in the name, so we need to replace it with the current version number
        if "$(VERSION)" in repository:
            self.repository = repository.replace("$(VERSION)", self.version, 1)
        else:
            self.repository = repository
        self.clone      = clone
        self.build      = build


    def print_info(self, fp = None):
        """
        Function that prints information about an install module

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
        """ Function that gets an InstallModule toString """

        out = "-----------------------------------------\n"
        out = out + "Module: {}, Version: {}\n".format(self.name, self.version)
        out = out + "Install Location Abs: {}\n".format(self.abs_path)
        out = out + "Install Location Rel: {}\n".format(self.rel_path)
        out = out + "Repository: {}{} w/ Type: {}\n".format(self.url, self.repository, self.url_type)
        return out