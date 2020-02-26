"""
Unit test file for install_module
"""

__author__      = "Jakub Wlodek"
__copyright__   = "Copyright June 2019, Brookhaven Science Associates"

import pytest


import installSynApps.data_model.install_module as Module


def test_version_replace():
    module = Module.InstallModule('TEMP', 'R1-0', '$(SUPPORT)/test', 'WGET_URL', 'https://dummy.url/', 'temp-$(VERSION).tgz', 'YES', 'YES', 'NO')
    assert module.repository == 'temp-R1-0.tgz'
