"""
Class that is responsible for writing an Install Configuration
"""

import datetime
import os
from installSynApps.DataModel import *

class ConfigWriter:
    """
    Class that is responsible for writing an Install Configuration

    Attributes
    ----------
    install_config : InstallConfiguration
        install config to write

    Methods
    -------
    write_install_config(filepath : str)
        function that writes an install config "saving" it
    """

    def __init__(self, install_config):
        """ constructor for configwriter """

        self.install_config = install_config


    def write_install_config(self, filepath='addtlConfDirs/config{}'.format(datetime.date.today())):
        """
        Main saving function for writing install config
        """

        if not os.path.exists(filepath):
            os.mkdir(filepath)
            os.mkdir(filepath + "/injectionFiles")
            os.mkdir(filepath + "/macroFiles")
        for injector_file in self.install_config.injector_files:
            new_fp = open(filepath + "/injectionFiles/" + injector_file.name, 'w')
            new_fp.write('# Saved by installSynApps on {}\n'.format(datetime.datetime.now()))
            new_fp.write('__TARGET_LOC__={}\n\n'.format(injector_file.target))
            new_fp.write(injector_file.contents)
            new_fp.close()

        new_build_flag = open(filepath + "/macroFiles/BUILD_FLAG_CONFIG", 'w')
        new_build_flag.write('# Saved by installSynApps on {}\n\n'.format(datetime.datetime.now()))
        for macro_pair in self.install_config.build_flags:
            new_build_flag.write('{}={}\n'.format(macro_pair[0], macro_pair[1]))
        new_build_flag.close()

        new_install_config = open(filepath + "/INSTALL_CONFIG", "w+")
        new_install_config.write('#\n# INSTALL_CONFIG file saved by installSynApps on {}\n#\n\n'.format(datetime.datetime.now())) 
        new_install_config.write("INSTALL={}\n\n\n".format(self.install_config.install_location))

        new_install_config.write('#MODULE_NAME    MODULE_VERSION          MODULE_PATH                             MODULE_REPO         CLONE_MODULE    BUILD_MODULE\n')
        new_install_config.write('#-----------------------------------------------------------------------------------------------------------------------------------\n')

        current_url = ""
        for module in self.install_config.get_module_list():
            if module.url != current_url:
                new_install_config.write("\n{}={}\n\n".format(module.url_type, module.url))
                current_url = module.url
            new_install_config.write("{:<16} {:<20} {:<40} {:<24} {:<16} {}\n".format(module.name, module.version, module.rel_path, module.repository, module.clone, module.build))

        new_install_config.close()