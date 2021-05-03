"""Driver class for cloning all of the install modules

The clone driver uses git, wget, tar and zip to download all modules specified in install configuration
to the local machine.
"""

import os
from subprocess import Popen, PIPE
import shutil

try:
    import requests
    USE_WGET=False
except ImportError:
    USE_WGET=True

from sys import platform
import installSynApps.data_model.install_config as IC
import installSynApps.data_model.install_module as IM
import installSynApps.io.logger as LOG
import installSynApps

class CloneDriver:
    """Class responsible for cloning and checking out all of the modules described in a given InstallConfiguration

    Attributes
    ----------
    recursive_modules : List of str
        list of module names that need to be cloned recursively
    submodule_list : List of str
        list of module names that have submodules that must be initialized
    submodule_names : Dict of str -> str
        pairings of module names to submodules that must be initialized
    install_config : InstallConfiguration
        contains all necessary install configuration information including list of modules
    """


    def __init__(self, install_config):
        """Constructor for the CloneDriver class
        """

        self.recursive_modules = ["EPICS_BASE", "MOTOR"]
        self.install_config = install_config


    def clone_module(self, module, recursive = False):
        """Function responsible for cloning each module into the appropriate location

        First checks if the module uses git or a download, and whether it needs to be recursive
        then, uses the information in the module object along with subprocess commands to clone the module.

        Parameters
        ----------
        module : InstallModule
            InstallModule currently being cloned
        recursive=False
            Flag that decides if git clone should be done recursively
        """

        global USE_URLLIB
        LOG.debug('Cloning module {}'.format(module.name))
        if isinstance(module, IM.InstallModule):
            if module.abs_path != None:
                command = None
                ret = -1
                if os.path.exists(module.abs_path):
                    shutil.rmtree(module.abs_path)
                if not recursive and module.url_type == "GIT_URL":
                    command = "git clone {} {}".format(module.url + module.repository, module.abs_path)
                elif recursive and module.url_type == "GIT_URL":
                    command = "git clone --recursive {} {}".format(module.url + module.repository, module.abs_path)
                elif module.url_type == "WGET_URL":
                    try:
                        archive_path = installSynApps.join_path(os.path.dirname(module.abs_path), module.repository)
                        if not USE_WGET:
                            r = requests.get(module.url + module.repository)
                            with open(archive_path, 'wb') as fp:
                                fp.write(r.content)
                            os.mkdir(module.abs_path)
                            ret = 0
                        else:
                            if platform == "win32":
                                command = "wget --no-check-certificate -P {} {}".format(os.path.dirname(module.abs_path), module.url + module.repository)
                            else:
                                command = 'wget -P {} {}'.format(os.path.dirname(module.abs_path), module.url + module.repository)

                    except Exception as e:
                        LOG.write(str(e))
                        ret = -1

                if command is not None:
                    LOG.print_command(command)
                    proc = Popen(command.split(' '))
                    proc.wait()
                    ret = proc.returncode

                if ret == 0:
                    LOG.write('Cloned module {} successfully.'.format(module.name))
                else:
                    LOG.write('Failed to clone module {}.'.format(module.name))
                    return -1

                if module.url_type == "WGET_URL":
                    archive_path = installSynApps.join_path(os.path.dirname(module.abs_path), module.repository)
                    if not os.path.exists(module.abs_path):
                        os.mkdir(module.abs_path)
                    command = None
                    if (module.repository.endswith(".tar.gz") or module.repository.endswith(".tgz")) and ret == 0:
                        command = "tar -xzf {} -C {} --strip-components=1".format(archive_path, module.abs_path)
                    elif module.repository.endswith(".zip") and ret == 0:
                        command = "tar -xf {} -C {} --strip-components=1".format(archive_path, module.abs_path)
                    else:
                        LOG.write('Unsupported archive format detected!')
                        ret = -1
                    
                    if command is not None:
                        LOG.print_command(command)
                        proc = Popen(command.split(' '))
                        proc.wait()
                        ret = proc.returncode
                        if ret == 0:
                            LOG.write('Unpacked module {} successfully.'.format(module.name))
                            os.remove(installSynApps.join_path(os.path.dirname(module.abs_path), module.repository))
                        else:
                            LOG.write('Failed to unpack module {}.'.format(module.name))

                if ret == 0:
                    return ret

                return -1
            return -2
        return -3


    def checkout_module(self, module, recursive = False):
        """Function responsible for checking out selected tagged versions of modules.

        Parameters
        ----------
        module : InstallModule
            Module that is being checked out
        recursive : bool
            Specifies whether there are git submodules that need to be initialized
        
        Returns
        -------
        int
            -3 if input was not an InstallModule, -2 if the absolute path is not known, -1 if checkout fails, 0 if success
        """

        ret = -1
        LOG.debug('Checking out version for module {}'.format(module.name))
        if isinstance(module, IM.InstallModule):
            if module.abs_path != None:
                ret = 0
                if module.version != "master" and module.url_type == "GIT_URL":
                    current_loc = os.getcwd()
                    os.chdir(module.abs_path)
                    command = "git checkout -q {}".format(module.version)
                    LOG.print_command(command)
                    proc = Popen(command.split(' '))
                    proc.wait()
                    ret = proc.returncode

                    if recursive and ret == 0:
                        command = 'git submodule update'
                        LOG.print_command(command)
                        proc = Popen(command.split(' '))
                        proc.wait()
                        ret = proc.returncode

                    os.chdir(current_loc)
                    if ret == 0:
                        LOG.write('Checked out version {}'.format(module.version))
                    else:
                        LOG.write('Checkout of version {} failed for module {}.'.format(module.version, module.name))
        return ret


    def cleanup_modules(self):
        """Function responsible for cleaning up directories that were not selected to clone
        """

        if self.install_config != None and isinstance(self.install_config, IC.InstallConfiguration):
            for module in self.install_config.modules:
                if isinstance(module, IM.InstallModule):
                    if module.clone == "NO" and os.path.exists(module.abs_path):
                        LOG.debug('Removing unused repo {}'.format(module.name))
                        shutil.rmtree(module.abs_path)


    def clone_and_checkout(self):
        """Top level function that clones and checks out all modules in the current install configuration.

        Returns
        -------
        List of str
            List of all modules that failed to be correctly cloned and checked out
        """

        if isinstance(self.install_config, IC.InstallConfiguration):
            failed_modules = []
            for module in self.install_config.get_module_list():
                if module.clone == "YES":
                    ret = 0
                    if module.name in self.recursive_modules:
                        ret = self.clone_module(module, recursive=True)
                    else:
                        ret = self.clone_module(module)
                    if ret < 0:
                        failed_modules.append(module.name)
                    else:
                        if module.name in self.recursive_modules:
                            ret = self.checkout_module(module, recursive=True)
                        else:
                            ret = self.checkout_module(module)
                        if ret < 0:
                            failed_modules.append(module.name)
                    self.cleanup_modules()

            return failed_modules

        return None

