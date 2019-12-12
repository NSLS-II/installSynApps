"""A python module that helps in downloading, building, and packaging EPICS, synApps and areaDetector.

installSynApps has two primary clients, installCLI, and installGUI, which allow for different ways to 
clone build and package specified modules.
"""

import sys
from sys import platform
import installSynApps.IO.logger as LOG

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


# pygithub for github autosync tags integration.
WITH_PYGITHUB=True
try:
    from github import Github
except ImportError:
    WITH_PYGITHUB=False

__version__     = "R2-3"
__author__      = "Jakub Wlodek"
__copyright__   = "Copyright (c) Brookhaven National Laboratory 2018-2019"
__environment__ = "Python Version: {}, OS Class: {}".format(sys.version.split()[0], OS_class)


def get_welcome_text():
    """Function that returns a welcome message with some installSynApps information

    Returns
    -------
    str
        the welcome message
    """

    text = "+----------------------------------------------------------------+\n"
    text = text + "+ installSynApps, version: {:<38}+\n".format(__version__)
    text = text + "+ {:<63}+\n".format(__environment__)
    text = text + "+ {:<63}+\n".format(__copyright__)
    text = text + "+ This software comes with NO warranty!                          +\n"
    text = text + "+----------------------------------------------------------------+\n"
    return text


def sync_github_tags(user, passwd, install_config, save_path=None):
    """Function that syncs module version tags with those found on github.

    This function is still buggy, and certain modules do not update correctly

    Parameters
    ----------
    user : str
        github username
    passwd : str
        github password
    install_config : InstallConfiguration
        instance of install configuration for which to update tags
    save_path : str
        None by default. If set, will save the install configuration to the given location after updating.
    """

    try:
        LOG.write('Syncing...', 'Please wait while tags are synced - this may take a while...')
        g = Github(user, passwd)
        for module in install_config.get_module_list():
            if module.url_type == 'GIT_URL' and 'github' in module.url and module.version != 'master' and module.name not in update_tags_blacklist:
                account_repo = '{}/{}'.format(module.url.split('/')[-2], module.repository)
                repo = g.get_repo(account_repo)
                if repo is not None:
                    tags = repo.get_tags()
                    if tags.totalCount > 0 and module.name != 'EPICS_BASE':
                        tag_found = False
                        for tag in tags:
                            if tag.name.startswith('R') and tag.name[1].isdigit():
                                if tag.name == module.version:
                                    tag_found = True
                                    break
                                LOG.write('Updating {} from version {} to version {}'.format(module.name, module.version, tag.name))
                                module.version = tag.name
                                tag_found = True
                                break
                        if not tag_found:
                            for tag in tags:
                                if tag.name[0].isdigit() and tag.name != module.version:
                                    LOG.write('Updating {} from version {} to version {}'.format(module.name, module.version, tag.name))
                                    module.version = tags[0].name
                                    break
                                elif tag.name[0].isdigit():
                                    break
                    elif module.name == 'EPICS_BASE':
                        for tag in tags:
                            if tag.name.startswith('R7'):
                                if tag.name != module.version:
                                    LOG.write('Updating {} from version {} to version {}'.format(module.name, module.version, tag.name))
                                    module.version = tag.name
                                    break
        if save_path is not None:
            writer = IO.config_writer.ConfigWriter(install_config)
            writer.write_install_config(save_path)
            LOG.write('Updated install config saved to {}'.format(save_path))
    except:
        LOG.write('ERROR - Possibly invalid Github credentials')


