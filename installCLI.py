#!/usr/bin/env python3

""" Python script for running the installSynApps module through the CLI """

__author__      = "Jakub Wlodek"
__copyright__   = "Copyright June 2019, Brookhaven Science Associates"
__version__     = "R2-3"

# Support python modules
import os
import subprocess
import argparse
from sys import platform
import sys

# InstallSynAppsModules
import installSynApps.DataModel as DataModel
import installSynApps.Driver as Driver
import installSynApps.IO as IO


# pygithub for github autosync tags integration.
WITH_PYGITHUB=True
try:
    from github import Github
    import getpass
except ImportError:
    WITH_PYGITHUB=False


# -------------- Some helper functions ------------------

def print_welcome_message():
    # Welcome message
    print("+----------------------------------------------------------------+")
    print("+ installSynApps, version: {:<38}+".format(__version__))
    print("+ Author: Jakub Wlodek                                           +")
    print("+ Copyright (c): Brookhaven National Laboratory 2018-2019        +")
    print("+ This software comes with NO warranty!                          +")
    print("+----------------------------------------------------------------+")
    print()
    
    print("Welcome to the installSynApps module.")
    print("It is designed to automate the build process for EPICS and areaDetector.")
    print("The scripts included will automatically edit all configuration files")
    print("required, and then build with make.")
    print()


def clean_exit():
    IO.logger.close_logger()
    exit()

def create_new_install_config():
    print("You have selected to create a new install configuration.\n")
    install_type = input("Would you like a coprehensive config, an areaDetector config, or a motor config? (AD/Motor/All) > ")
    if install_type.lower() == 'ad':
        install_template = 'NEW_CONFIG_AD'
        print('AreaDetector config selected.\n')
    elif install_type.lower() == 'motor':
        install_template = 'NEW_CONFIG_MOTOR'
        print('Motor config selected.\n')
    else:
        install_template = 'NEW_CONFIG_ALL'
        print('Coprehensive config selected.\n')

    write_loc = input('Where would you like the install configuration to be written? > ')
    write_loc = os.path.abspath(write_loc)
    print('Target output location set to {}'.format(write_loc))
    install_loc = input('What should be the target install location for the config? > ')
    print('Attempting to load default config with install location {}...'.format(install_loc))
    parser = IO.config_parser.ConfigParser('resources')
    install_config, message = parser.parse_install_config(config_filename=install_template, force_location=install_loc, allow_illegal=True)
    if install_config is None:
        print('Parse Error - {}'.format(message))
    elif message is not None:
        print('Warning - {}'.format(message))
    else:
        print('Done.')
    print('Writing...')
    writer = IO.config_writer.ConfigWriter(install_config)
    ret, message = writer.write_install_config(filepath=write_loc)
    if not ret:
        print('Write Error - {}'.format(message))
    else:
        print()
        print('Wrote new install configuration to {}.'.format(write_loc))
        print('Please edit INSTALL_CONFIG file to specify build specifications.')
        print('Then run ./installCLI.py -c {} to run the install configuration.'.format(write_loc))


def sync_tags(user, passwd, install_config, save_path):
    try:
        update_tags_blacklist = ["SSCAN", "CALC", "STREAM"]
        print('Syncing...', 'Please wait while tags are synced - this may take a while...')
        g = Github(user, passwd)
        for module in install_config.get_module_list():
            if module.url_type == 'GIT_URL' and 'github' in module.url and module.version != 'master' and module.name not in update_tags_blacklist:
                account_repo = '{}/{}'.format(module.url.split('/')[-2], module.repository)
                repo = g.get_repo(account_repo)
                if repo is not None:
                    tags = repo.get_tags()
                    if tags.totalCount > 0 and module.name != 'EPICS_BASE':
                        tag_found = False
                        for tag in tags:
                            #print('{} - {}'.format(account_repo, tag))
                            if tag.name.startswith('R') and tag.name[1].isdigit():
                                if tag.name == module.version:
                                    tag_found = True
                                    break
                                print('Updating {} from version {} to version {}'.format(module.name, module.version, tag.name))
                                module.version = tag.name
                                tag_found = True
                                break
                        if not tag_found:
                            for tag in tags:
                                if tag.name[0].isdigit() and tag.name != module.version:
                                    print('Updating {} from version {} to version {}'.format(module.name, module.version, tag.name))
                                    module.version = tags[0].name
                                    break
                                elif tag.name[0].isdigit():
                                    break
                    elif module.name == 'EPICS_BASE':
                        for tag in tags:
                            if tag.name.startswith('R7'):
                                if tag.name != module.version:
                                    print('Updating {} from version {} to version {}'.format(module.name, module.version, tag.name))
                                    module.version = tag.name
                                    break
        writer = IO.config_writer.ConfigWriter(install_config)
        writer.write_install_config(save_path)
        print('Updated install config saved to {}'.format(save_path))
    except:
        print('ERROR - Invalid Github credentials.')


def parse_user_input():
    # Default path to configure
    path_to_configure = "configure"

    parser = argparse.ArgumentParser(description="installSynApps for CLI EPICS and synApps auto-compilation.")

    config_group    = parser.add_argument_group('configuration options')
    build_group     = parser.add_argument_group('build options')
    debug_group     = parser.add_argument_group('logging options')

    config_group.add_argument('-i', '--installpath',      help='Define an override install location to use instead of the one read from INSTALL_CONFIG.')
    config_group.add_argument('-c', '--customconfigure',  help='Use an external configuration directory. Note that it must have the same structure as the default one.')
    config_group.add_argument('-n', '--newconfig',        action='store_true', help='Add this flag to use installCLI to create a new install configuration.')
    config_group.add_argument('-v', '--updateversions',   action='store_true', help='Add this flag to update module versions based on github tags. Must be used with -c flag.')

    build_group.add_argument('-y', '--forceyes',         action='store_true', help='Add this flag to automatically go through all of the installation steps without prompts.')
    build_group.add_argument('-d', '--dependency',       action='store_true', help='Add this flag to install dependencies via a dependency script.')
    build_group.add_argument('-s', '--singlethread',     action='store_true', help='Flag that forces make to run on only one thread. Use this for low power devices.')
    build_group.add_argument('-f', '--flatbinaries',     action='store_true', help='Add this flag if you wish for output binary bundles to have a flat format.')
    build_group.add_argument('-t', '--threads',          help='Define a limit on the number of threads that make is allowed to use.', type=int)
    
    debug_group.add_argument('-l', '--savelog',          action='store_true', help='Add this flag to save the build log to a file in the logs/ directory.')
    debug_group.add_argument('-m', '--debugmessages',    action='store_true', help='Add this flag to enable printing verbose debug messages.')
    debug_group.add_argument('-p', '--printcommands',    action='store_true', help='Add this flag to print bash/batch commands run by installSynApps.')

    
    arguments = vars(parser.parse_args())

    print_welcome_message()

    # Two cases where build will not happen, creating new config, and updating versions.
    if arguments['newconfig']:
        create_new_install_config()
        clean_exit()
    if arguments['customconfigure'] is not None:
        path_to_configure = arguments['customconfigure']
        if arguments['updateversions']:
            print('Updating module versions for configuration {}'.format(path_to_configure))
            if not os.path.exists(os.path.join(path_to_configure, 'INSTALL_CONFIG')):
                print("**INSTALL_CONFIG file not found in specified directory!**\nAborting...")
                clean_exit()
            if not WITH_PYGITHUB:
                print("**PyGithub module required for version updates.**")
                print("**Install with pip install pygithub**")
                print("Exiting...")
                clean_exit()
            parser = IO.config_parser.ConfigParser(path_to_configure)
            install_config, message = parser.parse_install_config(allow_illegal=True)
            print('Please enter your github credentials.')
            user = input('Username: ')
            passwd = getpass.getpass()
            sync_tags(user, passwd, install_config, path_to_configure)
            print('Done.')
            clean_exit()

    elif arguments['updateversions']:
        print('ERROR - Update versions flag selected but no configure directory given.')
        print('Rerun with the -c flag')
        print('Aborting...')
        clean_exit()

    return path_to_configure, arguments['installpath'], arguments


# ----------------- Run the build script ------------------------

path_to_configure, force_install_path, args = parse_user_input()
path_to_configure = os.path.abspath(path_to_configure)
yes             = args['forceyes']
single_thread   = args['singlethread']
dep             = args['dependency']
save_log        = args['savelog']
show_debug      = args['debugmessages']

if args['printcommands']:
    IO.logger.toggle_command_printing()

# For a CLI client, we just pass the sys.stdout.write function for logging
IO.logger.assign_write_function(sys.stdout.write)
if save_log:
    IO.logger.initialize_logger()


if show_debug:
    IO.logger.toggle_debug_logging()


threads         = args['threads']
if threads is None:
    threads = 0


print('Reading install configuration directory located at: {}...'.format(path_to_configure))
print()

# Parse base config file, make sure that it is valid - ask for user input until it is valid
parser = IO.config_parser.ConfigParser(path_to_configure)
install_config, message = parser.parse_install_config(allow_illegal=True, force_location=force_install_path)

if install_config is None:
    print('Error parsing Install Config... {}'.format(message))
    clean_exit()
elif message is not None:
    loc_ok = False
else:
    if not yes and force_install_path is None:
        new_loc = input('Install location {} OK. Do you wish to continue with this location? (y/n) > '.format(install_config.install_location))
        if new_loc == 'n':
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
                elif module.name == 'MOTOR':
                    install_config.motor_path = module.abs_path
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
if not packager.found_distro and platform != 'win32':
    print("WARNING - couldn't import distro pip package. This package is used for better identifying your linux distribution.")
    print("Note that the output tarball will use the generic 'linux-x86_64' name if packaging on linux.")
    if not yes:
        custom_output = input('Would you like to manually input a name to replace the generic one? (y/n) > ')
        if custom_output == 'y':
            custom_os = input('Please enter a suitable output package name: > ')
            packager.OS = custom_os
autogenerator = IO.script_generator.ScriptGenerator(install_config)


# Check to make sure that all dependencies are found
status, message = builder.check_dependencies_in_path()

if not status:
    print("** ERROR - could not find {} in environment path - is a dependancy. **".format(message))
    print("Please install git, make, wget, and tar, and ensure that they are in the system path.")
    print("Critical dependancy error, abort.")
    clean_exit()


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
                if module.name in builder.critical_modules:
                    print("Critical clone error... abort.")
                    clean_exit()
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


    dep_errors = updater.perform_dependency_valid_check()
    for dep_error in dep_errors:
        print(dep_error)

    # Here the update driver will reorder build to make sure all modules are being built after their dependencies.
    print('Reordering module build order to account for intra-module dependencies...')
    updater.perform_fix_out_of_order_dependencies()

    print("----------------------------------------------")
    print("Ready to build EPICS base, support and areaDetector...")
    if not dep and not yes:
        d = input("Do you need installSynApps to now install dependency packages on this machine? (y/n) > ")
    elif dep:
        d = "y"
    elif yes:
        d = 'n'

    if d == "y":
        print('Acquiring dependencies through dependency script...')
        if platform == 'win32':
            dep_script_path = os.path.join(path_to_configure, "dependencyInstall.bat")
        else:
            dep_script_path = os.path.join(path_to_configure, "dependencyInstall.sh")
        if not os.path.exists(dep_script_path):
            print('Could not find script at {}, skipping...'.format(dep_script_path))
        else:
            builder.acquire_dependecies(dep_script_path)

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
        ret, failed_list = builder.build_all()

        if ret != 0:
            for failed in failed_list:
                print('Module {} failed to build, will not package'.format(failed))
                if failed in builder.critical_modules:
                    print("**ERROR - Build failed - {}**".format(message))
                    print("**Check the INSTALL_CONFIG file to make sure settings and paths are valid**")
                    print('**Critical build error - abort...**')
                    clean_exit()
                else:
                    install_config.get_module_by_name(failed).package = "NO"


        print("----------------------------------------------")
        print("Autogenerating scripts and README file...")
        autogenerator.autogenerate_all()
        print("Done.")
        if ret == 0:
            print("Auto-Build of EPICS, synApps, and areaDetector completed successfully.")
        else:
            print("Auto-Build of EPICS, synApps, and areaDetector completed with some non-critical errors.")

    else:
        print("Build cancelled...\nDone.")
        clean_exit()


print()
if not yes:
    create_tarball = input('Would you like to create a tarball binary bundle now? (y/n) > ')
else:
    create_tarball = 'y'
if create_tarball == 'y':
    output_filename = packager.create_bundle_name()
    ret = packager.create_package(output_filename, flat_format=args['flatbinaries'])
    if ret != 0:
        print('ERROR - Failed to create binary bundle. Check install location to make sure it is valid')
        clean_exit()
    else:
        print('Bundle generated at: {}'.format(output_filename))

print()
if not yes:
    create_opi_dir = input('Whould you like to create opi_dir now? (y/n) >')
else:
    create_opi_dir = 'y'
if create_opi_dir == 'y':
    ret = packager.create_opi_folder(install_config.install_location)
    if ret != 0:
        print('ERROR - Failed to create opi bundle.')
        clean_exit()
    else:
        print('OPI screen tarball generated.')

print('Done.')
clean_exit()

