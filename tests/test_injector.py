"""
Unit test file for config injector
"""

__author__      = "Jakub Wlodek"
__copyright__   = "Copyright June 2019, Brookhaven Science Associates"
__credits__     = ["Jakub Wlodek", "Kazimierz Gofron"]
__license__     = "GPL"
__version__     = "R2-0"
__maintainer__  = "Jakub Wlodek"
__status__      = "Production"


import os
import shutil
import pytest

import tests.helper_test_funcs as Helper
import installSynApps.DataModel.install_config as IC
import installSynApps.DataModel.install_module as IM
import installSynApps.IO.config_parser as Parser
import installSynApps.IO.config_injector as Injector

parser = Parser.ConfigParser('tests/TestConfigs/basic')
install_config, message = parser.parse_install_config()

config_injector = Injector.ConfigInjector('tests/TestConfigs/basic', install_config)


def test_get_link():
    input = 'tests/TestConfigs/basic/injectorFiles/PLUGIN_CONFIG'
    temp = config_injector.get_injector_file_link(input)
    assert temp == '$(AREA_DETECTOR)/ADCore/iocBoot/EXAMPLE_commonPlugins.cmd'


def test_get_files():
    files = config_injector.get_injector_files()
    macro_files = config_injector.get_macro_replace_files()
    assert len(files) == 4
    print(files)
    assert (config_injector.path_to_configure + '/injectionFiles/AD_RELEASE_CONFIG') in files
    assert (config_injector.path_to_configure + '/injectionFiles/AUTOSAVE_CONFIG') in files
    assert (config_injector.path_to_configure + '/injectionFiles/MAKEFILE_CONFIG') in files
    assert (config_injector.path_to_configure + '/injectionFiles/PLUGIN_CONFIG') in files
    assert macro_files[0] == config_injector.path_to_configure + '/macroFiles/TEST_MACRO_FILE'


def test_get_macros():
    macro_files = config_injector.get_macro_replace_files()
    test = [['MACRO_A', 'YES'], ['MACRO_B', '12'], ['MACRO_C', 'TEST']]
    out = config_injector.get_macro_replace_from_file(macro_files[0])
    for i in range(0, len(out)):
        assert out[i][0] == test[i][0]
        assert out[i][1] == test[i][1]


def test_parse_contents():
    test = 'file "NDTEST_settings.req",          P=$(P),  R=TEST1:\n'
    config_injector.parse_injector_file_contents()

    assert config_injector.injector_file_contents['AUTOSAVE_CONFIG'] == test


def test_inject_into_file():
    testFile = 'tests/TestFiles/outputs/InjectExpectedFile'
    inputFile = 'tests/TestFiles/inputs/InjectTestFile'
    shutil.copy(inputFile, inputFile + '_TEST')
    config_injector.parse_injector_file_contents()
    old = config_injector.injector_file_links['AUTOSAVE_CONFIG']
    config_injector.injector_file_links['AUTOSAVE_CONFIG'] = inputFile+'_TEST'
    config_injector.inject_to_file(config_injector.path_to_configure + '/injectionFiles/AUTOSAVE_CONFIG')
    temp = open(inputFile + '_TEST', 'r')
    expected = open(testFile, 'r')
    assert Helper.compare_files(temp, expected)
    temp.close()
    expected.close()
    config_injector.injector_file_links['AUTOSAVE_CONFIG'] = old
    os.remove(inputFile + '_TEST')


def test_macro_replace_file():
    testFile = 'tests/TestFiles/outputs/MacroExpectedFile'
    inputFile = 'tests/TestFiles/inputs/MacroTestFile'
    shutil.copy(inputFile, inputFile + '_TEST')
    files = config_injector.get_macro_replace_files()
    macros = config_injector.get_macro_replace_from_file(files[0])
    config_injector.update_macros_file(macros, 'tests/TestFiles/inputs', 'MacroTestFile_TEST', comment_unsupported=True)
    temp = open(inputFile + '_TEST', 'r')
    expected = open(testFile, 'r')
    assert Helper.compare_files(temp, expected)
    temp.close()
    expected.close()
    os.remove(inputFile + '_TEST')
    shutil.rmtree('tests/TestFiles/inputs/OLD_FILES')
