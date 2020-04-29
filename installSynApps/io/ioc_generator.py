
import installSynApps
import shutil
import os
from installSynApps import installSynApps_path_join as PATH_JOIN
from sys import platform
from installSynApps.io import logger as LOG
import datetime


class DummyIOCGenerator:

    def __init__(self, install_config):
        self.install_config         = install_config
        self.ioc_template_dir       = os.path.join('__temp__', 'ioc-templates')
        if not os.path.exists(self.ioc_template_dir):
            os.mkdir(self.ioc_template_dir)


    def get_env_paths_name(self, module):

        if module == 'seq':
            return 'SNCSEQ'
        elif module == 'iocStats':
            return 'DEVIOCSTATS'
        elif module == 'areaDetector':
            return 'AREA_DETECTOR'
        else:
            return module.upper()


    def generate_env_paths(self, ioc_top_path, ioc_boot_path, target, action):

        LOG.debug('Generating template envPaths based on compiled binaries...')
        ioc_path = PATH_JOIN(self.ioc_template_dir, action.ioc_name)
        envPaths_fp = open(PATH_JOIN(ioc_path, 'envPaths'), 'w')

        arch='linux-x86_64'
        if platform == 'win32':
            arch = 'windows-x64-static'

        envPaths_fp.write('# Path propagated to remaining envPaths (binary bundle location). \
                            Edit to the absolute bundle location on your machine.\nepicsEnvSet \
                                ("BUNDLE_LOCATION", "/ad-nfs/epics/production")\n\n')
        
        envPaths_fp.write('epicsEnvSet("ARCH", "{}")\n'.format(arch))
        envPaths_fp.write('epicsEnvSet("TOP", "{}")\n'.format(ioc_top_path))

        base_path = PATH_JOIN('$(BUNDLE_LOCATION)', 'base')
        envPaths_fp.write('epicsEnvSet("EPICS_BASE",{}"{}")\n'.format((' ' * 14), base_path))

        support_path = "$(BUNDLE_LOCATION)"
        support_path = PATH_JOIN(support_path, "support")
        envPaths_fp.write('epicsEnvSet("SUPPORT",{}"{}")\n\n'.format((' ' * 17), support_path))

        for dir in os.listdir(self.install_config.support_path):
            mod_path = PATH_JOIN(self.install_config.support_path, dir)
            if os.path.isdir(mod_path) and dir not in ['base', 'configure', 'utils', 'documentation', '.git', 'lib', 'bin']:
                mod_path = PATH_JOIN('$(SUPPORT)', dir)
                envPaths_fp.write('epicsEnvSet("{}",{}"{}")\n'.format(self.get_env_paths_name(dir), ' ' * (24 - len(self.get_env_paths_name(dir))), mod_path))

        envPaths_fp.write('\n')

        for dir in os.listdir(self.install_config.ad_path):
            mod_path = PATH_JOIN(self.install_config.ad_path, dir)
            if os.path.isdir(mod_path) and dir not in ['configure', 'docs', 'documentation', 'ci', '.git', '']:
                mod_path = PATH_JOIN('$(AREA_DETECTOR)', dir)
                envPaths_fp.write('epicsEnvSet("{}",{}"{}")\n'.format(self.get_env_paths_name(dir), ' ' * (24 - len(self.get_env_paths_name(dir))), mod_path))

        envPaths_fp.close()


    def create_config_file(self, action):

        LOG.debug('Generating config file for use with procServ...')
        ioc_path = PATH_JOIN(self.ioc_template_dir, action.ioc_name)
        config_fp = open(PATH_JOIN(ioc_path, 'config'), 'w')
        config_fp.write('NAME={}\nPORT={}\nUSER=softioc\nHOST={}\n'.format(action.ioc_name, '4000', 'localhost'))
        config_fp.close()


    def find_paths_for_dummy_ioc(self, driver_type):
        """Finds ioc_top, executable, and iocBoot folder for IOCAction
        """

        try:
            driver_path = PATH_JOIN(self.install_config.ad_path, driver_type)

            # identify the IOCs folder
            for name in os.listdir(driver_path):
                if "ioc" == name or "iocs" == name:
                    driver_path = PATH_JOIN(driver_path, name)
                    break

            # identify the IOC 
            for name in os.listdir(driver_path):
                # Add check to see if NOIOC in name - occasional problems generating ADSimDetector
                if ("IOC" in name or "ioc" in name) and "NOIOC" not in name.upper():
                    driver_path = PATH_JOIN(driver_path, name)
                    break

            ioc_top_path = driver_path

            # find the driver executable
            executable_path = PATH_JOIN(driver_path, "bin")
            # There should only be one architecture in the bundle
            for name in os.listdir(executable_path):
                executable_path = PATH_JOIN(executable_path, name)
                break

            # We look for the executable that ends with App
            for name in os.listdir(executable_path):
                if 'App' in name:
                    executable_path = PATH_JOIN(executable_path, name)
                    break

            iocBoot_path = PATH_JOIN(driver_path, 'iocBoot')
            for dir in os.listdir(iocBoot_path):
                if dir.startswith('ioc') and os.path.isdir(PATH_JOIN(iocBoot_path, dir)):
                    iocBoot_path = PATH_JOIN(iocBoot_path, dir)
                    break
            return ioc_top_path, executable_path, iocBoot_path
        except:
            return None, None, None


    def get_lib_path_for_module(self, module_path, architecture, delimeter):
        """Generates a library path for specific module
        """

        bin_loc = PATH_JOIN(module_path, 'bin')
        bin_loc = PATH_JOIN(bin_loc, architecture)
        lib_loc = PATH_JOIN(module_path, 'lib')
        lib_loc = PATH_JOIN(lib_loc, architecture)
        return bin_loc + delimeter + lib_loc + delimeter


    def get_lib_path_str(self, driver_type):
        """Function that generates library path for shared built iocs
        Parameters
        ----------
        action : IOCAction
            ioc action for which we are generating lib path.
        Returns
        -------
        lib_path : str
            Library path set in form of str
        """

        lib_path_str = ''
        if platform == "win32":
            delimeter = ';'
            closer = '%PATH%"'
            arch='windows-x64-static'
            
        else:
            arch = 'linux-x86_64'
            delimeter = ':'
            closer = '$LD_LIBRARY_PATH'

        if platform == "win32":
            lib_path_str = lib_path_str + 'SET "PATH='
        else:
            lib_path_str = lib_path_str + 'export LD_LIBRARY_PATH='

        lib_path_str = lib_path_str + self.get_lib_path_for_module(self.install_config.base_path, arch, delimeter)

        if os.path.exists(self.install_config.support_path) and os.path.isdir(self.install_config.support_path):
            for dir in os.listdir(self.install_config.support_path):
                mod_path = PATH_JOIN(self.install_config.support_path, dir)
                if os.path.isdir(mod_path) and dir != "base" and dir != "areaDetector":
                    lib_path_str = lib_path_str + self.get_lib_path_for_module(mod_path, arch, delimeter)

        if os.path.exists(self.install_config.ad_path) and os.path.isdir(self.install_config.ad_path):
            for dir in os.listdir(self.install_config.ad_path):
                mod_path = PATH_JOIN(self.install_config.ad_path, dir)
                if os.path.isdir(mod_path) and (dir == 'ADCore' or dir == 'ADSupport' or dir in ad_plugins or dir == action.ioc_type):
                    lib_path_str = lib_path_str + self.get_lib_path_for_module(mod_path, arch, delimeter)

        lib_path_str = lib_path_str + closer
        return lib_path_str


    def initialize_st_base_file(self, ioc_path, lib_path, executable_path):
        """Function responsible for handling executable path injection, and base file creation
        """

        exec_written    = False
        if platform == 'win32':
            # On windows, no shebangs, so st.cmd will always run executable followed by st_base.cmd
            st_exe = open(PATH_JOIN(ioc_path, 'st.cmd'), 'w+')
            st_exe.write('@echo OFF\n\n{}\n\n{} st_base.cmd\n'.format(lib_path, executable_path))
            st_exe.close()
            st = open(PATH_JOIN(ioc_path, "st_base.cmd"), "w+")
            exec_written = True

        elif len(executable_path) > KERNEL_PATH_LIMIT or self.set_lib_path:
            if len(executable_path) > KERNEL_PATH_LIMIT:
                # The path length limit for shebangs (#!/) on linux is usually kernel based and set to 127
                LOG.debug('WARNING - Path to executable exceeds legal bash shebang limit, splitting into st.cmd and st_base.cmd')
            else:
                # If we want to set LD_LIBRARY_PATH we do that here.
                LOG.debug('Appending library path to start of st.cmd...')
            st_exe = open(PATH_JOIN(ioc_path, 'st.cmd'), 'w+')
            st_exe.write('#!/bin/bash\n\n{}\n\n{} st_base.cmd\n'.format(lib_path, executable_path))
            st_exe.close()
            st = open(PATH_JOIN(ioc_path, "st_base.cmd"), "w+")
            exec_written = True
        else:
            st = open(PATH_JOIN(ioc_path, "st.cmd"), "w+")

        return st, exec_written


    def genertate_st_cmd(self, action, executable_path, st_base_path):

        LOG.debug('Generating st.cmd using base file:\n{}'.format(st_base_path))
        ioc_path        = PATH_JOIN(self.ioc_template_dir, action.ioc_name)

        lib_path        = ''
        if self.set_lib_path:
            lib_path  = self.get_lib_path_str(action)
        
        # Create base st.cmd, add call to executable
        st, exec_written = self.initialize_st_base_file(ioc_path, lib_path, executable_path)

        # If the executable will be in the base file, write the shebang
        if not exec_written:
            st.write('#!{}\n\n'.format(executable_path))

        # Define envPaths
        st.write('< envPaths\n\n')

        # Open existing st.cmd base file
        st_base_fp = open(st_base_path, 'r')

        # Read through the lines, add a 'unique.cmd' call after all env sets, and add envSet calls to action environment
        lines = st_base_fp.readlines()
        wrote_unique = False
        for line in lines:
            if line.startswith('#!') or 'unique.cmd' in line or 'envPaths' in line:
                pass
            elif line.startswith('#'):
                st.write(line)
            elif 'Config(' in line and not wrote_unique:
                st.write('\n< unique.cmd\n\n')
                st.write(line)
                wrote_unique = True
            elif line.startswith('epicsEnvSet'):
                action.add_to_environment(line)
                st.write(line)
            else:
                st.write(line)

        st_base_fp.close()
        st.close()

        # Collect environment variables set in any other files
        self.grab_additional_env(action, st_base_path)
        # Make st.cmd executable.
        os.chmod(PATH_JOIN(ioc_path, "st.cmd"), 0o755)


    def generate_unique_cmd(self, action):

        LOG.debug('Generating template unique.cmd from ioc environment...')
        ioc_path = PATH_JOIN(self.ioc_template_dir, action.ioc_name)
        unique_fp = open(PATH_JOIN(ioc_path, 'unique.cmd'), 'w')

        unique_fp.write('#############################################\n')
        unique_fp.write('# installSynApps Auto-Generated IOC Template    #\n')
        unique_fp.write('# Meant for use with bundles running ADCore {} #'.format(self.install_config.get_core_version()))
        unique_fp.write('# Generated: {:<31}#\n'.format(str(datetime.datetime.now())))
        unique_fp.write('#############################################\n\n\n')

        for env_var in action.epics_environment.keys():
            unique_fp.write('epicsEnvSet("{}",{}"{}")\n'.format(env_var, ' ' * (32 - len(env_var)), action.epics_environment[env_var]))

        unique_fp.close()


    def grab_dependencies_from_bundle(self, ioc_path, iocBoot_path):

        LOG.debug('Collecting additional iocBoot files from bundle...')
        for file in os.listdir(iocBoot_path):
            target = PATH_JOIN(iocBoot_path, file)
            if os.path.isfile(target):
                if not file.startswith(('Makefile', 'st', 'test', 'READ', 'dll', 'envPaths')) and not file.endswith(('.xml')):
                    shutil.copyfile(target, PATH_JOIN(ioc_path, file))


    def create_dummy_ioc(self, action):

        LOG.debug("-------------------------------------------")
        LOG.debug("Setup process for dummy IOC template " + action.ioc_name)
        LOG.debug("-------------------------------------------")

        ioc_top_path, executable_path, iocBoot_path = self.find_paths_for_action(action.ioc_type)
        
        if executable_path is None:
            LOG.debug('Warning - Could not find binary for {}, skipping...'.format(action.ioc_type))
            return
        elif ioc_top_path is None or iocBoot_path is None:
            LOG.debug('WARNING - Could not find ioc top and iocBoot folder, for {}. Skipping...'.format(action.ioc_type))
        
        if os.path.exists(PATH_JOIN(self.ioc_template_dir, action.ioc_name)):
            shutil.rmtree(PATH_JOIN(self.ioc_template_dir, action.ioc_name))
        
        LOG.debug('Generating template IOC for {}...'.format(action.ioc_type))

        ioc_path = PATH_JOIN(self.ioc_top, action.ioc_name)
        os.mkdir(ioc_path)
        os.mkdir(PATH_JOIN(ioc_path, 'autosave'))

        current_base_len = 0
        current_base = None
        for file in os.listdir(iocBoot_path):
            next = PATH_JOIN(iocBoot_path, file)
            if os.path.isfile(next) and file.startswith('st'):
                fp = open(next, 'r')
                lines = fp.readlines()
                fp.close()
                if len(lines) > current_base_len:
                    current_base = next
                    current_base_len = len(lines)

        if current_base is None:
            LOG.debug('ERROR - Could not fine suitable st_base file. Aborting...')
            return

        self.genertate_st_cmd(action, executable_path, current_base)
        self.generate_unique_cmd(action)
        self.generate_env_paths(ioc_top_path, iocBoot_path, ioc_path, action)
        self.grab_dependencies_from_bundle(ioc_path, iocBoot_path)

        self.create_config_file(action)
        #self.make_ignore_files(action) TODO
        LOG.debug('Done.')


    def generate_dummy_iocs(self):

        LOG.write('Generating dummy IOCs for included driver binaries')
        dummy_ioc_actions = []
        for module in self.install_config.get_module_list():
            if module.name.startswith('AD') and os.path.exists(os.path.join(module.abs_path, 'iocs')):
                dummy_ioc_actions.append(DummyIOCAction(os.path.basename(module.abs_path)))
        
        for action in dummy_ioc_actions:
            self.create_dummy_ioc(action)

        LOG.write('Done.')



class DummyIOCAction:
    """Helper class that stores information and functions for each IOC in the CONFIGURE file
    
    Attributes
    ----------
    ioc_type : str
        name of areaDetector driver instance the IOC is linked to ex. ADProsilica
    ioc_name : str
        name of the IOC ex. cam-ps1
    ioc_prefix : str
        Prefix used by the IOC
    asyn_port : str
        asyn port used for outputting NDArrays
    ioc_port : str
        telnet port on which procserver will run the IOC
    connection : str
        Value used to connect to the device ex. IP, serial num. etc.
    """


    def __init__(self, driver_type):
        """Constructor for the IOCAction class
        """

        self.epics_environment              = {}
        self.ioc_name                       = '{}-template'.format(driver_type.lower[2:])
        self.ioc_type                       = driver_type
        self.epics_environment['IOCNAME']   = self.ioc_name
        self.epics_environment['ENGINEER']  = 'Dummy Engineer'


    def add_to_environment(self, line):
        try:
            line_s = line.strip()
            line_s = re.sub('"', '', line_s)
            line_s = re.sub('\t', '', line_s)
            line_s = re.sub(' +', '', line_s)
            line_s = re.sub('epicsEnvSet', '', line_s)
            temp = line_s.split(',')
            self.epics_environment[temp[0][1:]] = temp[1][:-1]
        except IndexError:
            LOG.debug('Error, failed to parse epics environment variable.')