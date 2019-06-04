#!/usr/bin/python3

#
# Python script for running the installSynApps module through the CLI
#
# Author: Jakub Wlodek
#


import os
import subprocess

import installSynApps.DataModel.install_config as Configuration
import installSynApps.Driver.build_driver as Builder
import installSynApps.Driver.clone_driver as Cloner
import installSynApps.Driver.update_config_driver as Updater
import installSynApps.IO.config_parser as Parser
import installSynApps.IO.script_generator as Autogenerator


# -------------- Some helper functions ------------------





# ----------------- Run the script ------------------------

version = "R2-0"


# Welcome message
print("+-----------------------------------------------------------------")
print("+ installSynApps, version: {}                                  +".format(version))
print("+ Author: Jakub Wlodek                                           +")
print("+ Copyright (c): Brookhaven National Laboratory 2018-2019        +")
print("+ This software comes with NO warranty!                          +")
print("+-----------------------------------------------------------------")
print()


path_to_configure = "configure"


parser = Parser.ConfigParser(path_to_configure)
install_config = parser.parse_install_config()
cloner = Cloner.CloneDriver(install_config)
updater = Updater.UpdateConfigDriver(path_to_configure, install_config)
builder = Builder.BuildDriver(install_config)
autogenerator = Autogenerator.ScriptGenerator(install_config)

print("Ready to clone and build EPICS and synApps into {}...".format(install_config.install_location))
response = input("Proceed? (y/n) > ")

if response == "n":
    print("Exiting...")
    exit()

print()

clone = input("Have you already cloned EPICS and synApps? (y/n) > ")
if clone == "n":
    print("Cloning EPICS and synApps into {}...".format(install_config.install_location))
    print("----------------------------------------------")
    unsuccessful = cloner.clone_and_checkout()
    if len(unsuccessful) > 0:
        for module in unsuccessful:
            print("Module {} was either unsuccessfully cloned or checked out.".format(module.name))
        print("Check INSTALL_CONFIG file to make sure repositories and versions are valid")
print("----------------------------------------------")
update = input("Do you need installSynApps to update configuration files? (y/n) > ")
if update == "y":
    print("Updating all RELEASE and configuration files...")
    updater.run_update_config()
print("----------------------------------------------")
print("Building EPICS base, support and areaDetector...")
dep = input("Have dependency packages already been installed on this machine? (y/n) > ")
if dep == "n":
    print("Installing all dependencies...")
    builder.acquire_dependecies("scripts/dependencyInstall.sh")
print("Done installing dependencies, starting build...")
ret, message, failed_list = builder.build_all()
if ret < 0:
    print("Build failed - {}".format(message))
    print("Check the INSTALL_CONFIG file to make sure settings are valid")
elif len(failed_list) > 0:
    for admodule in failed_list:
        print("AD Module {} failed to build".format(admodule.name))
    print("Check for missing dependecies, and if INSTALL_CONFIG is valid.")
print("----------------------------------------------")
print("Autogenerating scripts and README file...")
autogenerator.autogenerate_all()
print("Done.")




