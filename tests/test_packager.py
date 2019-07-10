"""
Class for testing if integrated packager works as intended.
"""

__author__      = "Jakub Wlodek"
__copyright__   = "Copyright June 2019, Brookhaven Science Associates"

import pytest
import installSynApps.IO as IO
import installSynApps.Driver as Driver


parser = IO.config_parser.ConfigParser('tests/TestConfigs/basic')
install_config, message = parser.parse_install_config(allow_illegal=True)
packager = Driver.packager_driver.Packager(install_config)

def test_get_ad_modules():
    out = packager.get_drivers_to_package()
    assert len(out) == 1
    assert out[0] == 'dummy'

def test_get_support_modules():
    out = packager.get_modules_to_package()
    assert len(out) == 1
    assert out[0] == 'MODBUS'