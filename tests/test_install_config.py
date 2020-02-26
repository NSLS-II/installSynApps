"""
Unit test file for config injector
"""

__author__      = "Jakub Wlodek"
__copyright__   = "Copyright June 2019, Brookhaven Science Associates"


# unit test include
import pytest

# installSynApps include
import installSynApps.data_model.install_config as InstallConfig
import installSynApps.data_model.install_module as InstallModule


# Test install 
install_config = InstallConfig.InstallConfiguration('/epics/test', 'configure')
base_module = InstallModule.InstallModule('EPICS_BASE', 'R7.0.2.2', '$(INSTALL)/base', 'GIT_URL', 'https://github.com/dummyurl/test/', 'base', 'YES', 'YES', 'YES')
support_module = InstallModule.InstallModule('SUPPORT', 'R6-0', '$(INSTALL)/support', 'GIT_URL', 'https://github.com/dummyurl/test/', 'support', 'YES', 'YES', 'NO')
ad_module = InstallModule.InstallModule('AREA_DETECTOR', 'R3-6', '$(SUPPORT)/areaDetector', 'GIT_URL', 'https://github.com/dummyurl/test/', 'ad', 'YES', 'YES', 'NO')
core_module = InstallModule.InstallModule('ADCORE', 'R3-6', '$(AREA_DETECTOR)/ADCore', 'GIT_URL', 'https://github.com/dummyurl/test/', 'ad', 'YES', 'YES', 'YES')

test_module = InstallModule.InstallModule('DUMMY', 'R1-0', '$(AREA_DETECTOR)/dummy', 'GIT_URL', 'https://github.com/dummyurl/test/', 'dummy', 'YES', 'YES', 'YES')


def reset():
    install_config.modules.clear()


# Tests for adding modules
def test_add_base():
    install_config.add_module(base_module)
    assert install_config.base_path == '/epics/test/base'
    assert len(install_config.modules) == 1
    reset()


def test_add_support_ad():
    install_config.add_module(support_module)
    install_config.add_module(ad_module)
    assert install_config.support_path == '/epics/test/support'
    assert install_config.ad_path == '/epics/test/support/areaDetector'
    assert len(install_config.modules) == 2
    reset()


def test_add_mod():
    install_config.add_module(support_module)
    install_config.add_module(ad_module)
    install_config.add_module(test_module)
    assert install_config.modules[2].name == test_module.name
    reset()


# test for converting path
def test_convert_path():
    install_config.add_module(base_module)
    install_config.add_module(support_module)
    install_config.add_module(ad_module)
    assert install_config.convert_path_abs(test_module.rel_path) == '/epics/test/support/areaDetector/dummy'
    reset()


def test_get_core_version():
    install_config.add_module(core_module)
    assert install_config.get_core_version() == 'R3-6'
    reset()