#!/usr/bin/python3

""" Python script for running the installSynApps module through the CLI """

__author__      = "Jakub Wlodek"
__copyright__   = "Copyright June 2019, Brookhaven Science Associates"
__version__     = "R2-1"

# Support python modules
import os
import subprocess
import argparse
from sys import platform

# InstallSynAppsModules
import installSynApps.DataModel as DataModel
import installSynApps.Driver as Driver
import installSynApps.IO as IO


# -------------- Some helper functions ------------------

def parse_user_input():
    path_to_configure = "configure"
    parser = argparse.ArgumentParser(description="installSynApps for CLI EPICS and synApps auto-compilation")
    parser.add_argument('-y', '--forceyes', action='store_true', help='Add this flag to automatically go through all of the installation steps without prompts')
    parser.add_argument('-d', '--dependency', action='store_true', help='Add this flag to install dependencies via a dependency script.')
    parser.add_argument('-c', '--customconfigure', help = 'Use an external configuration directory. Note that it must have the same structure as the default one')
    parser.add_argument('-t', '--threads', help = 'Define a limit on the number of threads that make is allowed to use')
    parser.add_argument('-s', '--singlethread', action='store_true', help='Flag that forces make to run on only one thread. Use this for low power devices.')
    arguments = vars(parser.parse_args())
    print(arguments)
    if arguments['customconfigure'] is not None:
        path_to_configure = arguments['customconfigure']

    return path_to_configure, arguments


# ----------------- Run the script ------------------------

path_to_configure, args = parse_user_input()
yes             = args['forceyes']
single_thread   = args['singlethread']
dep             = args['dependency']

threads         = args['threads']
if threads is None:
    threads = 0

# Welcome message
print("+-----------------------------------------------------------------")
print("+ installSynApps, version: {}                                  +".format(__version__))
print("+ Author: Jakub Wlodek                                           +")
print("+ Copyright (c): Brookhaven National Laboratory 2018-2019        +")
print("+ This software comes with NO warranty!                          +")
print("+-----------------------------------------------------------------")
print()

print("Welcome to the installSynApps module.")
print("It is designed to automate the build process for EPICS and areaDetector.")
print("The scripts included will automatically edit all configuration files")
print("required, and then build with make.")
print()
print('Reading install configuration directory located at: {}...'.format(path_to_configure))
print()


# Parse base config file, make sure that it is valid - ask for user input until it is valid
parser = IO.config_parser.ConfigParser(path_to_configure)
install_config, message = parser.parse_install_config(allow_illegal=True)
if install_config is None:
    print('Error parsing Install Config... {}'.format(message))
    exit()
elif message is not None:
    loc_ok = False
else:
    if not yes:
        new_loc = input('Install location {} OK. Do you wish to choose a different location? (y/n) > '.format(install_config.install_location))
        if new_loc == 'y':
            loc = input('Please enter a new install_location > ')
            install_config.install_location = loc.strip()
            for module in install_config.get_module_list():
                module.abs_path = install_config.convert_path_abs(module.rel_path)
                if module.name == 'EPICS_BASE':
                    install_config.base_path = module.abs_path
                elif module.name == 'SUPPORT':
                    install_config.support_path = module.abs_path
                elif module.name == 'AREA_DETECTOR':
                    install_config.ad_path = module.abs_path
            loc_ok = False
        else:
            loc_ok = True
    else:
        loc_ok = True

# Loop until a valid location is selected
if not loc_ok:
    while install_config.is_install_valid() != 1:
        print('**ERROR - Given install location - {} - is not valid**'.format(install_config.install_location))
        if install_config.is_install_valid() == 0:
            print('**Path does not exist**')
        elif install_config.is_install_valid() == -1:
            print('**Permission Error**')
        new_path = input('Please enter a new install location > ')
        install_config.install_location = new_path.strip()
        for module in install_config.get_module_list():
            module.abs_path = install_config.convert_path_abs(module.rel_path)
            if module.name == 'EPICS_BASE':
                install_config.base_path = module.abs_path
            elif module.name == 'SUPPORT':
                install_config.support_path = module.abs_path
            elif module.name == 'AREA_DETECTOR':
                install_config.ad_path = module.abs_path


# Driver Objects for running through build process
cloner      = Driver.clone_driver.CloneDriver(install_config)
updater     = Driver.update_config_driver.UpdateConfigDriver(path_to_configure, install_config)
builder     = Driver.build_driver.BuildDriver(install_config, threads, one_thread=single_thread)
packager    = Driver.packager_driver.Packager(install_config)
autogenerator = IO.script_generator.ScriptGenerator(install_config)


# Check to make sure that all dependencies are found
status, message = builder.check_dependencies_in_path()

if not status:
    print("** ERROR - could not find {} in environment path - is a dependancy. **".format(message))
    print("Please install git, make, wget, and tar, and ensure that they are in the system path.")
    print("Critical dependancy error, abort.")
    exit()


# Ask useer to proceed
print("Ready to start build process with location: {}...".format(install_config.install_location))
if not yes:
    response = input("Proceed? (y/n) > ")
else:
    response = "y"

if response == "n":
    print("Skipping clone + build...")
else:
    print()

    if not yes:
        clone = input("Would you like to clone EPICS and synApps modules? (y/n) > ")
    else:
        clone = "y"

    # Run the clone process
    if clone == "y":
        print("Cloning EPICS and synApps into {}...".format(install_config.install_location))
        print("----------------------------------------------")
        unsuccessful = cloner.clone_and_checkout()
        if len(unsuccessful) > 0:
            for module in unsuccessful:
                print("Module {} was either unsuccessfully cloned or checked out.".format(module.name))
                if module.name == "EPICS_BASE" or module.name == "SUPPORT" or module.name == "ADSUPPORT" or module.name == "ADCORE":
                    print("Critical clone error... abort.")
                    exit()
            print("Check INSTALL_CONFIG file to make sure repositories and versions are valid")

    print("----------------------------------------------")
    if not yes:
        # Update configuration files
        update = input("Do you need installSynApps to update configuration files? (y/n) > ")
    else:
        update = "y"

    if update == "y":
        print("Updating all RELEASE and configuration files...")
        updater.run_update_config()

    print("----------------------------------------------")
    print("Ready to build EPICS base, support and areaDetector...")
    if not dep and not yes:
        d = input("Do you need installSynApps to now install dependency packages on this machine? (y/n) > ")
    elif dep:
        d = "y"
    elif yes:
        d = 'n'

    if d == "y":
        if platform == 'win32':
            print('Detected Windows platform... Currently no dependency script support.')
        else:
            print('Acquiring dependencies through dependency script...')
            builder.acquire_dependecies("scripts/dependencyInstall.sh")

    if not yes:
        # Inform user of number of CPU cores to use and prompt to build
        if builder.one_thread:
            num_cores = 'one CPU core'
        elif builder.threads == 0:
            num_cores = 'as many CPU cores as possible'
        else:
            num_cores = '{} CPU cores'.format(builder.threads)
        print("----------------------------------------------")
        print('Builder is configured to use {} during compilation...'.format(num_cores))
        build = input("Ready to build selected modules... Continue (y/n) > ")
    else:
        build = "y"

    if build == "y":
        print("Starting build...")
        # Build all
        ret, message, failed_list = builder.build_all()

        if ret < 0:
            print("**ERROR - Build failed - {}**".format(message))
            print("**Check the INSTALL_CONFIG file to make sure settings and paths are valid**")
            print('**Critical build error - abort...**')
            exit()
        elif len(failed_list) > 0:
            for admodule in failed_list:
                print("AD Module {} failed to build".format(admodule.name))
            print("Check for missing dependecies, and if INSTALL_CONFIG is valid.")


        print("----------------------------------------------")
        print("Autogenerating scripts and README file...")
        autogenerator.autogenerate_all()
        print("Done.")

    else:
        print("Build aborted... Exiting.")
        exit()

    print("Auto-Build of EPICS, synApps, and areaDetector completed successfully.")

print()
if not yes:
    create_tarball = input('Would you like to create a tarball binary bundle now? (y/n) > ')
else:
    create_tarball = 'y'
if create_tarball == 'y':
    output_filename = packager.create_bundle_name()
    print('Tarring...')
    ret = packager.create_package(output_filename)
    if ret >= 0:
        print('Done. Wrote bundle to {}'.format(packager.output_location))
        print('Name of bundle: {}.tgz'.format(output_filename))
        print('Tarring took {} seconds'.format(ret))
    else:
        print('ERROR - Failed to create binary bundle. Check install location to make sure it is valid')

print('Done.')

