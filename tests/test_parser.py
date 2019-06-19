"""
Unit test file for config parser
"""

__author__      = "Jakub Wlodek"
__copyright__   = "Copyright June 2019, Brookhaven Science Associates"
__credits__     = ["Jakub Wlodek", "Kazimierz Gofron"]
__license__     = "GPL"
__version__     = "R2-0"
__maintainer__  = "Jakub Wlodek"
__status__      = "Production"


import pytest
import tests.helper_test_funcs as Helper

import installSynApps.DataModel.install_config as IC
import installSynApps.DataModel.install_module as IM
from installSynApps.IO import config_parser as Parser


# Test install 
install_config = IC.InstallConfiguration('/epics/test', 'tests/TestConfigs/basic')
base_module = IM.InstallModule('EPICS_BASE', 'R7.0.2.2', '$(INSTALL)/base', 'GIT_URL', 'https://github.com/dummyurl/', 'base', 'YES', 'YES')
support_module = IM.InstallModule('SUPPORT', 'R6-0', '$(INSTALL)/support', 'GIT_URL', 'https://github.com/dummyurl/', 'support', 'YES', 'YES')
ad_module = IM.InstallModule('AREA_DETECTOR', 'R3-6', '$(SUPPORT)/areaDetector', 'GIT_URL', 'https://github.com/dummyurl/', 'ad', 'YES', 'YES')

test_module = IM.InstallModule('DUMMY', 'R1-0', '$(AREA_DETECTOR)/dummy', 'GIT_URL', 'https://github.com/dummyurl/', 'dummy', 'YES', 'YES')

install_config.add_module(base_module)
install_config.add_module(support_module)
install_config.add_module(ad_module)
install_config.add_module(test_module)

parser = Parser.ConfigParser('tests/TestConfigs/basic')

parsed_config, message = parser.parse_install_config()


def test_no_permission():
    parsed_into_dev, error = parser.parse_install_config(force_location='/dev')
    assert parsed_into_dev is None
    assert error == 'Permission Error'


def test_loc_parse():
    assert install_config.install_location == parsed_config.install_location


def test_num_modules():
    assert len(install_config.modules) == len(parsed_config.modules)


def test_modules():
    for i in range(0, len(install_config.modules)):
        assert Helper.compare_mod(install_config.modules[i], parsed_config.modules[i])
