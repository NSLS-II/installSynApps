"""
Unit test file for config parser
"""

__author__      = "Jakub Wlodek"
__copyright__   = "Copyright June 2019, Brookhaven Science Associates"

import pytest
import tests.helper_test_funcs as Helper

import installSynApps.data_model.install_config as IC
import installSynApps.data_model.install_module as IM
from installSynApps.io import config_parser as Parser


# Test install 
install_config = IC.InstallConfiguration('tests/TestFiles', 'tests/TestConfigs/basic')
base_module = IM.InstallModule('EPICS_BASE', 'R7.0.2.2', '$(INSTALL)/base', 'GIT_URL', 'https://github.com/dummyurl/', 'base', 'YES', 'YES', 'YES')
support_module = IM.InstallModule('SUPPORT', 'R6-0', '$(INSTALL)/support', 'GIT_URL', 'https://github.com/dummyurl/', 'support', 'YES', 'YES', 'NO')
modbus_module = IM.InstallModule('MODBUS', 'master', '$(SUPPORT)/MODBUS', 'GIT_URL', 'https://github.com/dummyurl/', 'bus', 'YES', 'YES', 'YES')
ad_module = IM.InstallModule('AREA_DETECTOR', 'R3-6', '$(SUPPORT)/areaDetector', 'GIT_URL', 'https://github.com/dummyurl/', 'ad', 'YES', 'YES', 'NO')
core_module = IM.InstallModule('ADCORE', 'R3-6', '$(AREA_DETECTOR)/ADCore', 'GIT_URL', 'https://github.com/dummyurl/', 'ad', 'YES', 'YES', 'YES')
test_module = IM.InstallModule('DUMMY', 'R1-0', '$(AREA_DETECTOR)/dummy', 'GIT_URL', 'https://github.com/dummyurl/', 'dummy', 'YES', 'YES', 'YES')

install_config.add_module(base_module)
install_config.add_module(support_module)
install_config.add_module(modbus_module)
install_config.add_module(ad_module)
install_config.add_module(core_module)
install_config.add_module(test_module)

parser = Parser.ConfigParser('tests/TestConfigs/basic')

parsed_config, message = parser.parse_install_config()


def test_no_permission():
    parsed_into_dev, error = parser.parse_install_config(force_location='/dev')
    assert parsed_into_dev is None
    assert error == 'Permission Error'


def test_not_exist():
    parsed_into_dummy, error = parser.parse_install_config(force_location='/dummy/test')
    assert parsed_into_dummy is None
    assert error == 'Install filepath not valid'


def test_loc_parse():
    assert install_config.install_location == parsed_config.install_location


def test_num_modules():
    assert len(install_config.modules) == len(parsed_config.modules)


def test_modules():
    for i in range(0, len(install_config.modules)):
        assert Helper.compare_mod(install_config.modules[i], parsed_config.modules[i])


def test_injector_files():
    assert len(parsed_config.injector_files) == 4
    for injector in parsed_config.injector_files:
        if injector.name == 'AD_RELEASE_CONFIG':
            assert injector.target == '$(AREA_DETECTOR)/configure/RELEASE_PRODS.local'


def test_macro_files():
    assert len(parsed_config.build_flags) == 3
    assert parsed_config.build_flags[0][0] == 'MACRO_A'
    assert parsed_config.build_flags[0][1] == 'YES'
