#
# Driver class for cloning all of the install modules
#
# Author: Jakub Wlodek
#


import os
from subprocess import Popen, PIPE
import shutil
from sys import platform
import installSynApps.DataModel.install_config as IC
import installSynApps.DataModel.install_module as IM
import installSynApps.IO.logger as LOG

class CloneDriver:
    """
    Class responsible for cloning and checking out all of the modules described in a
    given InstallConfiguration

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

    Methods
    -------
    clone_module(module : InstallModule, recursive=False)
        Function responsible for cloning each module into the appropriate location
    checkout_module(module : InstallModule)
        Function that checks out module's tag version if non-master version is specified
    update_submodules()
        Function that updates all submodules for git repos that require it
    cleanup_modules()
        Function that removes any module directories that exist but are not required
    clone_and_checkout()
        Top level function that calls the other functions on each module in self.install_config.get_module_list()
    """


    def __init__(self, install_config):
        """
        Constructor for the CloneDriver class

        Contains lists of modules that require some special treatment when cloning
        """

        self.recursive_modules = ["EPICS_BASE"]
        self.submodule_list = []
        self.submodule_names = {}
        self.install_config = install_config


    def clone_module(self, module, recursive = False):
        """
        Function responsible for cloning each module into the appropriate location

        First checks if the module uses git or a download, and whether it needs to be recursive
        then, uses the information in the module object along with subprocess commands to clone the module.

        Parameters
        ----------
        module : InstallModule
            InstallModule currently being cloned
        recursive=False
            Flag that decides if git clone should be done recursively
        """

        LOG.debug('Cloning module {}'.format(module.name))
        if isinstance(module, IM.InstallModule):
            if module.abs_path != None:
                ret = -1
                if os.path.exists(module.abs_path):
                    shutil.rmtree(module.abs_path)
                if not recursive and module.url_type == "GIT_URL":
                    command = "git clone {} {}".format(module.url + module.repository, module.abs_path)
                elif recursive and module.url_type == "GIT_URL":
                    command = "git clone --recursive {} {}".format(module.url + module.repository, module.abs_path)
                elif module.url_type == "WGET_URL":
                    if platform == "win32":
                        command = "wget --no-check-certificate -P {} {}".format(module.abs_path, module.url + module.repository)
                    else:
                        command = 'wget -P {} {}'.format(module.abs_path, module.url + module.repository)

                LOG.write(command)
                proc = Popen(command.split(' '), stdout = PIPE, stdin=PIPE)
                out, err = proc.communicate()
                ret = proc.returncode
                if ret == 0:
                    LOG.log_write(out.decode())
                    LOG.write('Cloned module {} successfully'.format(module.name))
                else:
                    LOG.log_write(err.decode())
                    return -1

                if module.url_type == "WGET_URL":
                    
                    if (module.repository.endswith(".tar.gz") or module.repository.endswith(".tgz")) and ret == 0:
                        command = "tar -xzf {} -C {} --strip-components=1".format(os.path.join(module.abs_path, module.repository), module.abs_path)
                    elif module.repository.endswith(".zip") and ret == 0:
                        command = "unzip {} -C {}".format(os.path.join(module.abs_path, module.repository), module.abs_path)
                    
                    LOG.write(command)
                    proc = Popen(command.split(' '), stdout=PIPE, stderr=PIPE)
                    out, err = proc.communicate()
                    ret = proc.returncode
                    if ret == 0:
                        LOG.log_write(out.decode())
                        LOG.write('Unpacked module {} successfully'.format(module.name))
                    else:
                        LOG.log_write(err.decode())

                if ret == 0:
                    return ret

                return -1
            return -2
        return -3


    def checkout_module(self, module):
        """
        Function responsible for checking out selected tagged versions of modules.

        Parameters
        ----------
        module : InstallModule
            Module that is being checked out
        
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
                    LOG.write(command)
                    proc = Popen(command.split(' '), stdout = PIPE, stdin=PIPE)
                    out, err = proc.communicate()
                    ret = proc.returncode
                    os.chdir(current_loc)
                    if ret == 0:
                        LOG.write('Checked out version {}'.format(module.version))
                    else:
                        LOG.log_write(err.decode())
        return ret


    def update_submodule(self, module, submodule_name):
        """
        Function that updates submodules given that the input module is in the self.submodule_list array

        Parameters
        ----------
        module : InstallModule
            module for which we must update submodules
        submodule_name : str
            name of submodule to update
        """

        LOG.debug('Updating git submodules for {}'.format(module.name))
        if isinstance(module, IM.InstallModule):
            if module.abs_path != None:
                submodule_path = module.abs_path + "/" + submodule_name
                if os.path.exists(submodule_path):
                    LOG.write('git -C {} submodule init'.format(submodule_path))
                    p1 = Popen(["git", "-C", submodule_path, "submodule", "init"], stdout = PIPE, stdin = PIPE)
                    out, err = p1.communicate()
                    ret1 = p1.communicate()
                    if ret1 == 0:
                        LOG.log_write(out.decode())
                    else:
                        LOG.log_write(err.decode())
                    LOG.write('git -C {} submodule update'.format(submodule_path))
                    p2 = Popen(["git", "-C", submodule_path, "submodule", "update"], stdout = PIPE, stdin = PIPE)
                    out, err = p2.communicate()
                    ret2 = p2.communicate()
                    if ret2 == 0:
                        LOG.log_write(out.decode())
                    else:
                        LOG.log_write(err.decode())


    def cleanup_modules(self):
        """Function responsible for cleaning up directories that were not selected to clone"""

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
                        ret = self.checkout_module(module)
                        if ret < 0:
                            failed_modules.append(module.name)
                        else:
                            if module.name in self.submodule_list:
                                self.update_submodule(module, self.submodule_names[module.name])
            self.cleanup_modules()

            return failed_modules

        return None

