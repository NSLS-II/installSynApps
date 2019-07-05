"""
Class responsible for packaging compiled binaries based on install config
"""


import os
import tarfile
from sys import platform
import datetime
import installSynApps.DataModel.install_config as IC

class Packager:


    def __init__(self, install_config):
        self.install_config = install_config


    def create_tarball(self):
        if not os.path.exists('DEPLOYMENTS'):
            os.mkdir('DEPLOYMENTS')
        tar = tarfile.open('DEPLOYMENTS/NSLS2_AD_{}_Bin_{}_{}.tgz'.format(self.install_config.get_core_version(), platform, datetime.date.today()), 'w:gz')
        return tar


    def add_to_tar(self, tar):
        tar.add(self.install_config.base_path + '/bin')
        tar.add(self.install_config.base_path + '/lib')
        tar.add(self.install_config.base_path + '/configure')
        tar.add(self.install_config.base_path + '/startup')
        tar.add(self.install_config.base_path + '/include')
        tar.add(self.install_config.base_path + '/Makefile')
        for elem in os.listdir(self.install_config.support_path):
            tar.add(self.install_config.support_path + '/' + elem)


    def close_tarball(self, tar):
        tar.close()