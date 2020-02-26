"""
Class for testing if integrated packager works as intended.
"""

__author__      = "Jakub Wlodek"
__copyright__   = "Copyright June 2019, Brookhaven Science Associates"

import pytest
import os
import shutil
import installSynApps.io as IO
import installSynApps.driver as Driver


parser = IO.config_parser.ConfigParser('tests/TestConfigs/basic')
install_config, message = parser.parse_install_config(allow_illegal=True)
packager = Driver.packager_driver.Packager(install_config)

def test_grab_folder():
    os.mkdir('__TEMP__')
    packager.grab_folder('../TestConfigs/basic', '__TEMP__')
    for file in os.listdir('__TEMP__'):
        assert os.path.exists('../TestConfigs/basic/' + file)
    shutil.rmtree('__TEMP__')