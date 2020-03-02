"""
Unit test file for config injector
"""

__author__      = "Jakub Wlodek"
__copyright__   = "Copyright June 2019, Brookhaven Science Associates"


import os
import shutil
import pytest

import tests.helper_test_funcs as Helper
import installSynApps.data_model.install_config as IC
import installSynApps.data_model.install_module as IM
import installSynApps.io.config_parser as Parser
import installSynApps.io.config_injector as Injector

parser = Parser.ConfigParser('tests/TestConfigs/basic')
install_config, message = parser.parse_install_config(force_location='tests', allow_illegal=True)

config_injector = Injector.ConfigInjector(install_config)


def test_inject_into_file():
    testFile = 'tests/TestFiles/outputs/InjectExpectedFile'
    inputFile = 'tests/TestFiles/inputs/InjectTestFile'
    shutil.copy(inputFile, inputFile + '_TEST')
    for injector in install_config.injector_files:
        if injector.name == 'AUTOSAVE_CONFIG':
            config_injector.inject_to_file(injector)
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
