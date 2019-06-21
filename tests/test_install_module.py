"""
Unit test file for install_module
"""

__author__      = "Jakub Wlodek"
__copyright__   = "Copyright June 2019, Brookhaven Science Associates"
__credits__     = ["Jakub Wlodek", "Kazimierz Gofron"]
__license__     = "GPL"
__version__     = "R2-0"
__maintainer__  = "Jakub Wlodek"
__status__      = "Production"

import pytest


import installSynApps.DataModel.install_module as Module


def test_version_replace():
    module = Module.InstallModule('TEMP', 'R1-0', '$(SUPPORT)/test', 'WGET_URL', 'https://dummy.url/', 'temp-$(VERSION).tgz', 'YES', 'YES')
    assert module.repository == 'temp-R1-0.tgz'
