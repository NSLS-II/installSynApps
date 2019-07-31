"""
Unit test file for builder
"""

__author__      = "Jakub Wlodek"
__copyright__   = "Copyright June 2019, Brookhaven Science Associates"


import pytest
import tests.helper_test_funcs as Helper

import installSynApps.DataModel.install_config as IC
from installSynApps.IO import config_parser as Parser
from installSynApps.Driver import build_driver as Builder

parser = Parser.ConfigParser('tests/TestConfigs/basic')
parsed_config, message = parser.parse_install_config()
builder = Builder.BuildDriver(parsed_config, 0)


def test_create_make_flag_1():
    assert builder.make_flag == '-sj'


def test_create_make_flag_2():
    builder.threads = 4
    builder.create_make_flags()
    assert builder.make_flag == '-sj4'


def test_create_make_flag_3():
    builder.one_thread = True
    builder.create_make_flags()
    assert builder.make_flag == '-s'
