#
# Class that parses the CONFIG files
#
# Author: Jakub Wlodek
#

import os
import re
import DataModel.install_config as IC
import DataModel.install_module as IM

class ConfigParser:

    def __init__(self, configure_path):
        self.configure_path = configure_path


    def check_valid_config_path(self):
        if os.path.exists(self.configure_path) and os.path.isdir(self.configure_path):
            return True
        elif os.path.exists(self.configure_path) and os.path.isfile(self.configure_path):
            self.configure_path = self.configure_path.rsplit('/', 1)
        return False


    def parse_line_to_module(self, line, current_url, current_url_type):
        line = re.sub(' +', ' ', line)
        module_components = line.split(' ')
        name        = module_components[0]
        version     = module_components[1]
        rel_path    = module_components[2]
        repository  = module_components[3]
        clone       = module_components[4]
        build       = module_components[5]
        install_module = IM.InstallModule(name, version, rel_path, current_url_type, current_url, repository, clone, build)
        return install_module


    def parse_install_config(self, config_filename = "INSTALL_CONFIG"):
        if os.path.exists(self.configure_path + "/" + config_filename):
            install_file = open(self.configure_path + "/" + config_filename, "r")

            if install_file == None:
                return None
            install_config = None
            current_url = ""
            current_url_type = ""
            epics_arch = ""
            install_loc = ""

            line = install_file.readline()
            while line:
                line = line.strip()
                if not line.startswith('#') and len(line) > 1:
                    if line.startswith("INSTALL="):
                        install_loc = line.split('=')[-1]
                    elif line.startswith("EPICS_ARCH"):
                        epics_arch = line.split('=')[-1]
                        install_config = IC.InstallConfiguration(install_loc, self.configure_path, epics_arch)
                        if install_config.is_install_valid() < 0:
                            return None
                        elif install_config.is_install_valid() == 0:
                            os.mkdir(install_config.install_location)
                    elif line.startswith("GIT_URL") or line.startswith("WGET_URL"):
                        current_url = line.split('=')[1]
                        current_url_type = line.split('=')[0]
                    else:
                        install_module = self.parse_line_to_module(line, current_url, current_url_type)
                        install_config.add_module(install_module)
                line = install_file.readline()
            
            install_file.close()
            # install_config.print_installation_info()
            return install_config
        return None
                    