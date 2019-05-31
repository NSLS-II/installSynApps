#
# Class that will represent a single install module
#
# Author: Jakub Wlodek
#

import os
import install_config as IC

class InstallModule:

    def __init__(self, name, version, rel_path, url_type, url, repository, clone, build):

        self.name       = name
        self.version    = version
        self.rel_path   = rel_path
        self.abs_path   = None
        self.url_type   = url_type
        self.url        = url
        self.repository = repository
        self.clone      = clone
        self.build      = build
        self.config     = None



    def set_install_config(self, config):
        if isinstance(config, IC.InstallConfiguration):
            self.config = config
            self.abs_path = self.config.convert_path_abs(self.rel_path)