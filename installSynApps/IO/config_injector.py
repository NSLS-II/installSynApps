#
# Class responsible for injecting settings into configuration files
#
# Author: Jakub Wlodek
#

import os
import re
import installSynApps.DataModel.install_config as IC

class ConfigInjector:
    """
    Class that is responsible for injecting configuration information and replaces macros.

    Attributes
    ----------
    injector_file_links : Dict of str to str
        locations of target files for specific injections
    path_to_configure : str
        path to installSynApps configuration directory
    install_config : InstallConfiguration
        the currently loaded install configuration
    ad_modules : List of str
        Used to decide which modules to include when with_ad = False in update_macros_file()

    Methods
    -------
    get_injector_files()
        gets list of current injector files in configuration directory
    get_macro_replace_files()
        gets list of files with lists of macro replacements
    get_injector_file_link(injector_file_path : str)
        gets the target file path for a given injector file
    inject_into_file(injector_file_path : str)
        injects a given injector file into its target
    get_macro_replace_from_file(macro_list : List, macro_file_path : str)
        appends list of macro-value pairs to main list from file
    update_macros(macro_val_list : List, target : str)
        updates the macros in a target directory files given a list of macro-value pairs
    update_macros_file(macro_replace_list : List, target_dir : 
        str, target_filename : str, comment_unsupported : bool, with_ad : bool)
            Function that updates the macros for a single file, with settings for commenting unupported macros
            and for including the ad blacklist
    """


    def __init__(self, path_to_configure, install_config):
        """Constructor for ConfigInjector"""

        self.injector_file_links = {
            "AD_RELEASE_CONFIG"     : "$(AREA_DETECTOR)/configure/RELEASE_PRODS.local",
            "AUTOSAVE_CONFIG"       : "$(AREA_DETECTOR)/ADCore/iocBoot/EXAMPLE_commonPlugin_settings.req",
            "MAKEFILE_CONFIG"       : "$(AREA_DETECTOR)/ADCore/ADApp/commonDriverMakefile",
            "PLUGIN_CONFIG"         : "$(AREA_DETECTOR)/ADCore/iocBoot/EXAMPLE_commonPlugins.cmd",
        }
        self.path_to_configure = path_to_configure
        self.injector_file_contents = {}
        self.module_replace_list = []
        self.initialize_addtl_config()
        self.install_config = install_config
        self.ad_modules = ["ADCORE", "AREA_DETECTOR", "ADSUPPORT"]


    def initialize_addtl_config(self):
        """ Function that initializes macro replacers and injector files """

        self.injector_file_contents = {}
        self.macro_replace_list = []
        self.parse_injector_file_contents()
        macro_file_paths = self.get_macro_replace_files()
        for file in macro_file_paths:
            self.macro_replace_list.extend(self.get_macro_replace_from_file(file))


    def get_injector_files(self):
        """
        Function that gets list of injector files by searching configure/injectionFiles

        Returns
        -------
        injector_files : List
            List of injector file paths
        """

        injector_files = []
        if os.path.exists(self.path_to_configure + '/injectionFiles') and os.path.isdir(self.path_to_configure + '/injectionFiles'):
            for file in os.listdir(self.path_to_configure + "/injectionFiles"):
                if os.path.isfile(self.path_to_configure + "/injectionFiles/" + file):
                    if self.injector_file_links[file] != None:
                        injector_files.append(self.path_to_configure + "/injectionFiles/" + file)
        
        return injector_files


    def parse_injector_file_contents(self):
        """ Function that reads injector files and gets their contents """

        files = self.get_injector_files()
        for filename in self.injector_file_links:
            found = False
            for file in files:
                if file.split('/')[-1] == filename:
                    found = True
                    contents = ''
                    fp = open(file, "r")
                    line = fp.readline()
                    while line:
                        if not line.startswith('#') and len(line) > 0:
                            contents = contents + line
                        line = fp.readline()
                    self.injector_file_contents[file.split('/')[-1]] = contents
            if not found:
                self.injector_file_contents[filename] = ''


    def get_macro_replace_files(self):
        """
        Function that retrieves the list of macro replace files from configure/macroFiles

        Returns
        -------
        macro_replace_files : List
            List of macro file paths
        """

        macro_replace_files = []
        if os.path.exists(self.path_to_configure + '/macroFiles') and os.path.isdir(self.path_to_configure + '/macroFiles'):
            for file in os.listdir(self.path_to_configure + "/macroFiles"):
                if os.path.isfile(self.path_to_configure + "/macroFiles/" + file):
                    macro_replace_files.append(self.path_to_configure + "/macroFiles/" + file)

        return macro_replace_files


    def get_injector_file_link(self, injector_file_path):
        """
        Function that given an injector file path returns a target file

        Parameters
        ----------
        injector_file_path : str
            path to a given injector file
        
        Returns
        -------
        self.injector_file_links[filename] : str
            the relative path to the target file as stored in the class's dictionary
        """

        filename = injector_file_path.split('/')[-1]
        return self.injector_file_links[filename]


    def inject_to_file(self, injector_file_path):
        """
        Function that injects contents of specified file into target

        First, convert to absolute path given the install config. Then open it in append mode, then
        write all uncommented lines in the injector file into the target, and then close both

        Parameters
        ----------
        injector_file_path : str
            path to a given injector file
        """

        target_path = self.get_injector_file_link(injector_file_path)
        target_path = self.install_config.convert_path_abs(target_path)
        target_file = target_path.rsplit('/', 1)[-1]
        target_path_no_example = target_path.rsplit('/', 1)[0] + "/" + target_file[8:]
        if (not os.path.exists(target_path) and not os.path.exists(target_path_no_example)) or not os.path.exists(injector_file_path):
            return
        if target_file.startswith("EXAMPLE_"):
            if os.path.exists(target_path):
                os.rename(target_path, target_path_no_example)
            target_path = target_path_no_example
        target_fp = open(target_path, "a")
        target_fp.write("\n# ------------The following was auto-generated by installSynApps-------\n\n")
        if self.injector_file_contents[injector_file_path.split('/')[-1]] is not None:
            target_fp.write(self.injector_file_contents[injector_file_path.split('/')[-1]])
        target_fp.write("\n# --------------------------Auto-generated end----------------------\n")
        target_fp.close()


    def get_macro_replace_from_file(self, macro_file_path):
        """
        Function that adds to a list of macro-value pairs as read from a configurtion file

        Parameters
        ----------
        macro_list : List
            list containting macro-value pairs to append
        macro_file_path : str
            path to config file with new macro settings
        
        Return
        ------
        output : List of Pairs
            List of Macro value pairs read from file
        """

        output = []
        if os.path.exists(macro_file_path) and os.path.isfile(macro_file_path):
            macro_fp = open(macro_file_path, "r")
            line = macro_fp.readline()
            while line:
                line = line.strip()
                if not line.startswith('#') and '=' in line:
                    output.append(line.strip().split('='))

                line = macro_fp.readline()
            macro_fp.close()
        return output


    def update_macros_dir(self, macro_replace_list, target_dir):
        """
        Function that updates the macros for all files in a target location, given a list of macro-value pairs

        Parameters
        ----------
        macro_replace_list : List
            list containting macro-value pairs
        target_dir : str
            path of target dir for which all macros will be edited.
        """

        if os.path.exists(target_dir) and os.path.isdir(target_dir):
            for file in os.listdir(target_dir):
                if os.path.isfile(target_dir + "/" + file) and not file.endswith(".pl") and file != "Makefile" and not file.endswith(".ioc"):
                    self.update_macros_file(macro_replace_list, target_dir, file)


    def update_macros_file(self, macro_replace_list, target_dir, target_filename, comment_unsupported = False, with_ad = True):
        """
        Function that updates the macro values in a single configure file

        Parameters
        ----------
        macro_replace_list : List of [str, str]
            list of macro-value pairs to replace
        target_dir : str
            location of target file
        target_filename : str
            name of the file
        comment_unsupported : bool
            if true, will comment out any macros that are in the file that are not in input list. Important for updating RELEASE in support/
        with_ad : bool
            if false, will comment out macros for area detector modules. used for RELEASE in support - AD is built separately
        """

        if not os.path.exists(target_dir + "/OLD_FILES"):
            os.mkdir(target_dir + "/OLD_FILES")
        os.rename(target_dir + "/" + target_filename, target_dir + "/OLD_FILES/" + target_filename)
        old_fp = open(target_dir + "/OLD_FILES/" + target_filename, "r")

        if target_filename.startswith("EXAMPLE_"):
            new_fp = open(target_dir + "/" + target_filename[8:], "w")
        else:
            new_fp = open(target_dir + "/" + target_filename, "w")
        line = old_fp.readline()
        while line:
            line = line.strip()
            if not line.startswith('#') and '=' in line:
                line = line = re.sub(' +', '', line)
            if line.startswith('#') and '=' not in line:
                new_fp.write(line + "\n")
            else:
                wrote_line = False
                for macro in macro_replace_list:
                    if line.startswith(macro[0] + "=") and (with_ad or (macro[0] not in self.ad_modules)):
                        new_fp.write("{}={}\n".format(macro[0], macro[1]))
                        wrote_line = True
                    elif line.startswith("#" + macro[0] + "="):
                        print(macro[0])
                        new_fp.write("#{}={}\n".format(macro[0], macro[1]))
                        wrote_line = True
                if not wrote_line:
                    if comment_unsupported and not line.startswith('#') and len(line) > 1:
                        new_fp.write("#" + line + "\n")
                    else:
                        new_fp.write(line + "\n")
            line = old_fp.readline()
        new_fp.close()
        old_fp.close()


