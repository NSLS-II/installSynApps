"""
Unit test file for config injector
"""

__author__      = "Jakub Wlodek"
__copyright__   = "Copyright June 2019, Brookhaven Science Associates"


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

config_injector = Injector.ConfigInjector(install_config)


def test_inject_into_file():
    testFile = 'tests/TestFiles/outputs/InjectExpectedFile'
    inputFile = 'tests/TestFiles/inputs/InjectTestFile'
    shutil.copy(inputFile, inputFile + '_TEST')
    config_injector.inject_to_file(install_config.injector_files[3])
    temp = open(inputFile + '_TEST', 'r')
    expected = open(testFile, 'r')
    assert Helper.compare_files(temp, expected)
    temp.close()
    expected.close()
    os.remove(inputFile + '_TEST')


def test_macro_replace_file():
    testFile = 'tests/TestFiles/outputs/MacroExpectedFile'
    inputFile = 'tests/TestFiles/inputs/MacroTestFile'
    shutil.copy(inputFile, inputFile + '_TEST')
    macros = install_config.build_flags
    config_injector.update_macros_file(macros, 'tests/TestFiles/inputs', 'MacroTestFile_TEST', comment_unsupported=True)
    temp = open(inputFile + '_TEST', 'r')
    expected = open(testFile, 'r')
    assert Helper.compare_files(temp, expected)
    temp.close()
    expected.close()
    os.remove(inputFile + '_TEST')
    shutil.rmtree('tests/TestFiles/inputs/OLD_FILES')
