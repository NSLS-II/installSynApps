#!/usr/bin/env python3

"""Python script for running the installSynApps module through the CLI

usage: installCLI.py [-h] [-i INSTALLPATH] [-c CUSTOMCONFIGURE] [-n] [-v] [-y]
                     [-d] [-f] [-t THREADS] [-l] [-m] [-p]

installSynApps for CLI EPICS and synApps auto-compilation

optional arguments:
  -h, --help            show this help message and exit

configuration options:
  -i INSTALLPATH, --installpath INSTALLPATH
                        Define an override install location to use instead of
                        the one read from INSTALL_CONFIG.
  -c CUSTOMCONFIGURE, --customconfigure CUSTOMCONFIGURE
                        Use an external configuration directory. Note that it
                        must have the same structure as the default one.
  -n, --newconfig       Add this flag to use installCLI to create a new
                        install configuration.
  -v, --updateversions  Add this flag to update module versions based on
                        github tags. Must be used with -c flag.

build options:
  -y, --forceyes        Add this flag to automatically go through all of the
                        installation steps without prompts.
  -d, --dependency      Add this flag to install dependencies via a dependency
                        script.
  -f, --flatbinaries    Add this flag if you wish for output binary bundles to
                        have a flat format.
  -t THREADS, --threads THREADS
                        Define a limit on the number of threads that make is
                        allowed to use.

logging options:
  -l, --savelog         Add this flag to save the build log to a file in the
                        logs/ directory.
  -m, --debugmessages   Add this flag to enable printing verbose debug
                        messages.
  -p, --printcommands   Add this flag to print bash/batch commands run by
                        installSynApps.
"""

# Support python modules
import os
import subprocess
import argparse
import getpass
import sys
import time
from sys import platform

# InstallSynAppsModules
import installSynApps
import installSynApps.data_model as DATA_MODEL
import installSynApps.driver as DRIVER
import installSynApps.io as IO

# -------------- Some helper functions ------------------


def print_welcome_message():
    """Returns welcome message
    """

    print(installSynApps.get_welcome_text())

    IO.logger.debug(installSynApps.get_debug_version_info())

    print("Welcome to the installSynApps module.")
    print("It is designed to automate the build process for EPICS and areaDetector.")
    print("The scripts included will automatically edit all configuration files")
    print("required, and then build with make.")
    print()


# Make sure we close logger before exiting
def clean_exit():
    """Shuts down logger and exits script
    """

    IO.logger.close_logger()
    exit()


# Exit with an error code
def err_exit(error_code):
    """Shuts down logger, exits script with error code
    """

    IO.logger.close_logger()
    exit(error_code)


def create_new_install_config():
    """Creates new install configuration
    """

    print("You have selected to create a new install configuration.\n")
    install_type = input("Would you like a coprehensive config, "
                         "an areaDetector config, or a motor config? "
                         "(AD/Motor/All) > ")

    if install_type.lower() == 'ad':
        print('AreaDetector config selected.\n')
    elif install_type.lower() == 'motor':
        print('Motor config selected.\n')
    else:
        print('Coprehensive config selected.\n')

    write_loc = input(
        'Where would you like the install configuration to be written? > ')
    install_loc = input(
        'What should be the target install location for the config? > ')
    update_ver = input('\nWould you like installSynApps to automatically sync version '
                       'tags for new config?\nRequires git and network connection. (y/n) > ')

    vers = False
    if update_ver.lower() == 'y':
        vers = True

    installSynApps.create_new_install_config(install_loc,
                                             install_type,
                                             update_versions=vers,
                                             save_path=write_loc)


def parse_user_input():
    """Parses user's command line flags
    """

    path_to_configure = os.path.join(os.path.dirname(
        os.path.dirname(installSynApps.__file__)), 'configure')

    parser = argparse.ArgumentParser(
        description="installSynApps for CLI EPICS and synApps auto-compilation")

    config_group = parser.add_argument_group('configuration options')
    build_group = parser.add_argument_group('build options')
    debug_group = parser.add_argument_group('logging options')

    config_group.add_argument(
        '-i', '--installpath', help='Define an override install location to use instead of the one read from INSTALL_CONFIG.')
    config_group.add_argument('-c', '--customconfigure',
                              help='Use an external configuration directory. Note that it must have the same structure as the default one.')
    config_group.add_argument('-n', '--newconfig', action='store_true',
                              help='Add this flag to use installCLI to create a new install configuration.')
    config_group.add_argument('-v', '--updateversions', action='store_true',
                              help='Add this flag to update module versions based on github tags. Must be used with -c flag.')

    build_group.add_argument('-y', '--forceyes', action='store_true',
                             help='Add this flag to automatically go through all of the installation steps without prompts.')
    build_group.add_argument('-d', '--dependency', action='store_true',
                             help='Add this flag to install dependencies via a dependency script.')
    build_group.add_argument('-f', '--flatbinaries', action='store_true',
                             help='Add this flag if you wish for output binary bundles to have a flat format.')
    build_group.add_argument('-s', '--includesources', action='store_true',
                             help='Add this flag for output bundles to include the full source tree.')
    build_group.add_argument('-t', '--threads',
                             help='Define a limit on the number of threads that make is allowed to use.', type=int)

    debug_group.add_argument('-l', '--savelog', action='store_true',
                             help='Add this flag to save the build log to a file in the logs/ directory.')
    debug_group.add_argument('-m', '--debugmessages', action='store_true',
                             help='Add this flag to enable printing verbose debug messages.')
    debug_group.add_argument('-p', '--printcommands', action='store_true',
                             help='Add this flag to print bash/batch commands run by installSynApps.')

    arguments = vars(parser.parse_args())

    if arguments['customconfigure'] is not None:
        path_to_configure = arguments['customconfigure']

    # Initialize logging first
    if arguments['printcommands']:
        IO.logger.toggle_command_printing()

    # For a CLI client, we simply sys.stdout.write for logging.
    IO.logger.assign_write_function(sys.stdout.write)
    if arguments['savelog']:
        IO.logger.initialize_logger()

    if arguments['debugmessages']:
        IO.logger.toggle_debug_logging()

    print_welcome_message()

    # Two cases where build will not happen, creating new config, and updating versions.
    if arguments['newconfig']:
        create_new_install_config()
        clean_exit()

    elif arguments['customconfigure'] is not None and arguments['updateversions']:
        print('Updating module versions for configuration {}'.format(
            path_to_configure))
        if not os.path.exists(os.path.join(path_to_configure, 'INSTALL_CONFIG')):
            print(
                "**INSTALL_CONFIG file not found in specified directory!**\nAborting...")
            clean_exit()
        parser = IO.config_parser.ConfigParser(path_to_configure)
        install_config, _ = parser.parse_install_config(allow_illegal=True)
        installSynApps.sync_all_module_tags(install_config, path_to_configure)
        print('Done.')
        clean_exit()

    elif arguments['updateversions']:
        print('ERROR - Update versions flag selected but no configure directory given.')
        print('Rerun with the -c INSTALL_CONFIG_PATH flag')
        print('Aborting...')
        err_exit(1)

    return path_to_configure, arguments['installpath'], arguments


# ----------------- Run the script ------------------------


#########################################################################
#                                                                       #
# Parse install configuration directory                                 #
#                                                                       #
#########################################################################

def parse_configuration():

    # Parse base config file, make sure that it is valid - ask for user input until it is valid
    parser = IO.config_parser.ConfigParser(path_to_configure)
    install_config, message = parser.parse_install_config(
        allow_illegal=True, force_location=force_install_path)
    
    if install_config is None:
        print('Error parsing Install Config... {}'.format(message))
        exit()
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

    return install_config


def check_deps(builder):

    # Check to make sure that all dependencies are found
    status, message = builder.check_dependencies_in_path()

    if not status:
        print("** ERROR - could not find {} in environment path - is a dependancy. **".format(message))
        print("Please install git, make, wget, and tar, and ensure that they are in the system path.")
        print("Critical dependancy error, abort.")
        err_exit(2)


#########################################################################
#                                                                       #
# Execute Build Process Here                                            #
#                                                                       #
#########################################################################

def execute_build(yes, grab_deps, install_config, cloner, updater, builder, autogenerator):

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
            print("-" * 45)
            
            unsuccessful = cloner.clone_and_checkout()
            
            if len(unsuccessful) > 0:
                for module in unsuccessful:
                    print("Module {} was either unsuccessfully cloned or checked out.".format(module))
                    if module in builder.critical_modules:
                        print("Critical clone error... abort.")
                        err_exit(3)
                print("Check INSTALL_CONFIG file to make sure repositories and versions are valid")

        # Update our CONFIG and RELEASE files
        print("-" * 45)
        print("Updating all RELEASE and configuration files...")
        updater.run_update_config()

        # Check to make sure we have our dependencies selected
        dep_errors = updater.perform_dependency_valid_check()
        for dep_error in dep_errors:
            print(dep_error)

        # Here the update driver will reorder build to make sure all modules are being built after their dependencies.
        print('Reordering module build order to account for intra-module dependencies...')
        updater.perform_fix_out_of_order_dependencies()

        print("-" * 45)
        print("Ready to build EPICS base, support and areaDetector...")

        install_deps = 'n'
        if not grab_deps and not yes:
            install_deps = input('Would you like to run dependency script to grab dependency packages? (y/n) > ')
        
        # Run external dependency install script.
        if install_deps == 'y' or (grab_deps):
            print('Attempting to grab external dependencies...')
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
            
            print("-" * 45)
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
                        print("**ERROR - Build failed - {} is a critical module**".format(failed))
                        print("**Check the INSTALL_CONFIG file to make sure settings and paths are valid**")
                        print('**Critical build error - abort...**')
                        err_exit(4)
                    else:
                        install_config.get_module_by_name(failed).package = "NO"


            print("-" * 45)
            print("Autogenerating scripts and README file...")
            autogenerator.autogenerate_all(create_simple_readme=False)
            autogenerator.generate_readme('{}'.format(install_config.install_location))
            print("Done.")
            
            if ret == 0:
                print("Auto-Build of EPICS, synApps, and areaDetector completed successfully.")
            else:
                print("Auto-Build of EPICS, synApps, and areaDetector completed with some non-critical errors.")
            
            print('Build step completed in {} seconds'.format(time.time() - script_start_time))

        else:
            print("Build aborted... Exiting.")
            err_exit(5)


#########################################################################
#                                                                       #
# Bundle Generation Process Here                                        #
#                                                                       #
#########################################################################

def generate_bundles(yes, install_config, packager, flat_output, include_src):

    print()
    if not yes:
        create_tarball = input('Would you like to create a tarball binary bundle now? (y/n) > ')
    else:
        create_tarball = 'y'
    if create_tarball == 'y':
        ret_src = 0
        # If we want to, include debug bundles
        if include_src:
            output_filename_src = packager.create_bundle_name(source_bundle=include_src)
            ret_src = packager.create_package(output_filename_src, flat_format=flat_output, with_sources=include_src)
        # Always generate a production bundle.
        output_filename = packager.create_bundle_name(source_bundle=False)
        ret = packager.create_package(output_filename, flat_format=flat_output, with_sources=False)
        if ret_src != 0 or ret != 0:
            print('ERROR - Failed to create binary bundle. Check install location to make sure it is valid')
            err_exit(6)
        else:
            print('Bundle generated at: {}'.format(output_filename))

    ask_create_add_on_tarball = True
    while ask_create_add_on_tarball:
        if not yes:
            print()
            create_add_on_tarball = input('Would you like to create an add-on tarball to add a module to an existing bundle? (y/n) > ')
        else:
            create_add_on_tarball = 'n'
            ask_create_add_on_tarball = False
        if create_add_on_tarball == 'y':
            module_name = input('Please enter name of the module you want packaged (All capitals - Ex. ADPROSILICA) > ')
            if install_config.get_module_by_name(module_name) is None or install_config.get_module_by_name(module_name).build == 'NO':
                print('ERROR - Selected module not built, cannot create add on tarball!')
                err_exit(7)
            output_filename = packager.create_bundle_name(module_name=module_name, source_bundle=include_src)
            if output_filename is None:
                print('ERROR - No module named {} could be found in current configuration, abort.'.format(module_name))
                err_exit(7)
            ret = packager.create_add_on_package(output_filename, module_name, with_sources=include_src)
            make_another_tarball = input('Would you like to create another add on tarball? (y/n) > ')
            if make_another_tarball != 'y':
                ask_create_add_on_tarball = False
        else:
            ask_create_add_on_tarball = False

    print()
    if not yes:
        create_opi_dir = input('Would you like to create opi_dir now? (y/n) > ')
    else:
        create_opi_dir = 'n'
    if create_opi_dir == 'y':
        ret = packager.create_opi_package()
        if ret != 0:
            print('ERROR - Failed to create opi bundle.')
            err_exit(8)
        else:
            print('OPI screen tarball generated.')


def main(yes, grab_deps, flat_output, include_src):

    try:
        install_config = parse_configuration()

        # Driver Objects for running through build process
        cloner      = DRIVER.clone_driver.CloneDriver(install_config)
        updater     = DRIVER.update_config_driver.UpdateConfigDriver(path_to_configure, install_config)
        builder     = DRIVER.build_driver.BuildDriver(install_config, threads, one_thread=single_thread)
        packager    = DRIVER.packager_driver.Packager(install_config)
        
        if not packager.found_distro and platform != 'win32':
            print("WARNING - couldn't import distro pip package. This package is used for better identifying your linux distribution.")
            print("Note that the output tarball will use the generic 'linux-x86_64' name if packaging on linux.")
            
            if not yes:
                custom_output = input('Would you like to manually input a name to replace the generic one? (y/n) > ')
                if custom_output == 'y':
                    custom_os = input('Please enter a suitable output package name: > ')
                    packager.OS = custom_os

        autogenerator = IO.file_generator.FileGenerator(install_config)

        # Run the build
        execute_build(yes, grab_deps, install_config, cloner, updater, builder, autogenerator)

        # Generate output bundles
        generate_bundles(yes, install_config, packager, flat_output, include_src)

        # Finished
        print('Done.')
        clean_exit()

    except KeyboardInterrupt:
        print('\n\nAborting installSynApps execution...\nGoodbye.')
        clean_exit()


if __name__ == '__main__':
    script_start_time = time.time()

    path_to_configure, force_install_path, args = parse_user_input()
    force_install_path = os.path.abspath(force_install_path)
    path_to_configure = os.path.abspath(path_to_configure)
    yes = args['forceyes']
    dep = args['dependency']
    flat_output = args['flatbinaries']
    include_src = args['includesources']
    # Inclusion of sources only supported in non-flat output mode
    if include_src:
        flat_output = False

    single_thread = False
    threads = args['threads']
    if threads is None:
        threads = 0
    elif threads == 1:
        single_thread = True


    print('Reading install configuration directory located at: {}...'.format(path_to_configure))
    print()
    main(yes, dep, flat_output, include_src)
