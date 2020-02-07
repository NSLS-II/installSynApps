"""A python module that helps in downloading, building, and packaging EPICS, synApps and areaDetector.

installSynApps has two primary clients, installCLI, and installGUI, which allow for different ways to 
clone build and package specified modules.
"""

import sys
import re
import os
from sys import platform
import datetime
import subprocess
from subprocess import Popen, PIPE
import installSynApps.IO.logger as LOG

# Only support 64 bit windows
if platform == 'win32':
    OS_class = 'windows-x64'
else:
    try:
        # External package used to identify linux distribution version. Note that this adds external
        # dependancy, but it is required because the platform.linuxdistro() function is being deprecated
        import distro
        v = distro.linux_distribution(full_distribution_name=False)
        OS_class = '{}_{}'.format(v[0], v[1])
    except:
        OS_class='linux'


# Because EPICS versioning is not as standardized as it should be, certain modules cannot be properly auto updated.
# Ex. Calc version R3-7-3 is most recent, but R5-* exists?
update_tags_blacklist = ["SSCAN", "CALC", "STREAM"]

# Module version, author, copyright
__version__     = "R2-5"
__author__      = "Jakub Wlodek"
__copyright__   = "Copyright (c) Brookhaven National Laboratory 2018-2020"
__environment__ = "Python Version: {}, OS Class: {}".format(sys.version.split()[0], OS_class)


def find_isa_version():
    """Function that attempts to get the version of installSynApps used.

    Returns
    -------
    isa_version : str
        The version string for installSynApps. Either hardcoded version, or git tag description
    commit_hash : str
        None if git status not available, otherwise hash of current installSynApps commit.
    """

    isa_version = __version__
    commit_hash = None

    try:
        LOG.debug('git describe --tags')
        out = subprocess.check_output(['git', 'describe', '--tags'])
        isa_version = out.decode('utf-8').strip()
        LOG.debug('git rev-parse HEAD')
        out = subprocess.check_output(['git', 'rev-parse', 'HEAD'])
        commit_hash = out.decode('utf-8')
    except PermissionError:
        LOG.debug('Could not find git information for installSynApps versions, defaulting to internal version.')

    return isa_version, commit_hash


def get_debug_version_info():
    """Function that retrieves printable debug string about current installSynApps version

    Returns
    -------
    debug_info : str
        A string with debug information about installSynApps
    """

    isa_version, commit_hash = find_isa_version()
    return 'installSynApps: {}, {}, Date: {}\n'.format(isa_version, __environment__, datetime.datetime.now())


def get_welcome_text():
    """Function that returns a welcome message with some installSynApps information

    Returns
    -------
    str
        the welcome message
    """

    text = "+----------------------------------------------------------------+\n"
    text = text + "+ installSynApps, Version: {:<38}+\n".format(__version__)
    text = text + "+ {:<63}+\n".format(__environment__)
    text = text + "+ {:<63}+\n".format(__copyright__)
    text = text + "+ This software comes with NO warranty!                          +\n"
    text = text + "+----------------------------------------------------------------+\n"
    return text


def sync_module_tag(module_name, install_config, save_path = None):
    """Function that syncs module version tags with those hosted with git.

    This function is still buggy, and certain modules do not update correctly

    Parameters
    ----------
    module_name : str
        The name of the module to sync
    install_config : InstallConfiguration
        instance of install configuration for which to update tags
    save_path : str
        None by default. If set, will save the install configuration to the given location after updating.
    """

    module = install_config.get_module_by_name(module_name)
    if module.url_type == 'GIT_URL' and module.version != 'master' and module.name not in update_tags_blacklist:
        account_repo = '{}{}'.format(module.url, module.repository)
        LOG.print_command("git ls-remote --tags {}".format(account_repo))
        sync_tags_proc = Popen(['git', 'ls-remote', '--tags', account_repo], stdout=PIPE, stderr=PIPE)
        out, err = sync_tags_proc.communicate()
        ret = out.decode('utf-8')
        tags_temp = ret.splitlines()
        tags = []
        for tag in tags_temp:
            tags.append(tag.rsplit('/')[-1])

        if len(tags) > 0:

            best_tag = tags[0]
            best_tag_ver_str_list = re.split(r'\D+', tags[0])
            best_tag_ver_str_list = [num for num in best_tag_ver_str_list if num.isnumeric()]
            best_tag_version_numbers = list(map(int, best_tag_ver_str_list))
            for tag in tags:
                tag_ver_str_list = re.split(r'\D+', tag)
                tag_ver_str_list = [num for num in tag_ver_str_list if num.isnumeric()]
                tag_version_numbers = list(map(int, tag_ver_str_list))
                for i in range(len(tag_version_numbers)):
                    if best_tag.startswith('R') and not tag.startswith('R'):
                        break
                    elif not best_tag.startswith('R') and tag.startswith('R'):
                        best_tag = tag
                        best_tag_version_numbers = tag_version_numbers
                        break
                    elif i == len(best_tag_version_numbers) or tag_version_numbers[i] > best_tag_version_numbers[i]:
                        best_tag = tag
                        best_tag_version_numbers = tag_version_numbers
                        break
                    elif tag_version_numbers[i] < best_tag_version_numbers[i]:
                        break

            tag_updated = False
            module_ver_str_list = re.split(r'\D+', module.version)
            module_ver_str_list = [num for num in module_ver_str_list if num.isnumeric()]
            module_version_numbers = list(map(int, module_ver_str_list))
            for i in range(len(best_tag_version_numbers)):
                if i == len(module_version_numbers) or best_tag_version_numbers[i] > module_version_numbers[i]:
                    tag_updated = True
                    LOG.write('Updating {} from version {} to version {}'.format(module.name, module.version, best_tag))
                    module.version = best_tag
                    break
                elif best_tag_version_numbers[i] < module_version_numbers[i]:
                    break
            if not tag_updated:
                LOG.debug('Module {} already at latest version: {}'.format(module.name, module.version))

    if save_path is not None:
        writer = IO.config_writer.ConfigWriter(install_config)
        ret, message = writer.write_install_config(save_path, overwrite_existing=True)
        LOG.write('Updated install config saved to {}'.format(save_path))
        return ret
    else:
        return True


def sync_all_module_tags(install_config, save_path=None, overwrite_existing=True):
    """Function that syncs module version tags with those found in git repositories.

    Parameters
    ----------
    install_config : InstallConfiguration
        instance of install configuration for which to update tags
    save_path : str
        None by default. If set, will save the install configuration to the given location after updating.
    overwrite_existing : bool
        Flag that tells installSynApps to overwrite or not the existing module tags. Default: True
    """

    LOG.write('Syncing...')
    LOG.write('Please wait while tags are synced - this may take a while...')
    for module in install_config.get_module_list():
        sync_module_tag(module.name, install_config)

    if save_path is not None:
        writer = IO.config_writer.ConfigWriter(install_config)
        ret, message = writer.write_install_config(save_path, overwrite_existing=overwrite_existing)
        LOG.write('Updated install config saved to {}'.format(save_path))
        return ret
    else:
        return True


def create_new_install_config(install_location, configuration_type, update_versions = True, save_path=None):
    """Helper function for creating new install configurations

    Parameters
    ----------
    install_location : str
        The path to the install location
    configuration_type : str
        The type of new install configuration
    update_versions : bool
        Flag to tell config to update versions from git remotes.
    save_path : str
        If defined, save config to specified path.
    """

    if configuration_type.lower() == 'ad':
        install_template = 'NEW_CONFIG_AD'
    elif configuration_type.lower() == 'motor':
        install_template = 'NEW_CONFIG_MOTOR'
    else:
        install_template = 'NEW_CONFIG_ALL'
    if save_path is not None:
        LOG.write('\nCreating new install configuration with template: {}'.format(install_template))
        write_loc = os.path.abspath(save_path)
        LOG.write('Target output location set to {}'.format(write_loc))
    parser = IO.config_parser.ConfigParser('resources')
    install_config, message = parser.parse_install_config(config_filename=install_template, force_location=install_location, allow_illegal=True)
    if install_config is None:
        LOG.write('Parse Error - {}'.format(message))
    elif message is not None:
        LOG.write('Warning - {}'.format(message))
    else:
        LOG.write('Loaded template install configuration.')
    if update_versions and save_path is not None:
        ret = sync_all_module_tags(install_config, save_path=write_loc, overwrite_existing=False)
    elif update_versions and save_path is None:
        ret = sync_all_module_tags(install_config, overwrite_existing=False)
    elif not update_versions and save_path is not None:
        writer = IO.config_writer.ConfigWriter(install_config)
        ret, message = writer.write_install_config(filepath=write_loc)
    else:
        ret = True
    if not ret:
        LOG.write('Write Error - {}'.format(message))
    elif save_path is not None:
        LOG.write('\nWrote new install configuration to {}.'.format(write_loc))
        LOG.write('Please edit INSTALL_CONFIG file to specify build specifications.')
        LOG.write('Then run ./installCLI.py -c {} to run the install configuration.'.format(write_loc))
    return install_config, message