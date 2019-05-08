# Modification of the full adConfigSetup script for use with the installSynApps package
#
# Author: Jakub Wlodek
# Copyright (c): Brookhaven National Laboratory
# Created: 2-Feb-2019

import os
import shutil
import argparse


# Global variables. isLinux is necessary because of the .Linux file being univeral across Linux arches
isLinux = True
EPICS_ARCH = "linux-x86_64"


# Function that removes all whitespace in a string
# Used prior to splitting a macro/value pair on the '=' symbol.
def remove_whitespace(line):
    line.strip()
    no_whitespace = line.replace(" ", "")
    return no_whitespace


# function that takes in two open files and replaces the macros found in them with those in required pairs
def replace_macros(old_file, new_file, required_pairs):
    line = old_file.readline()
    while line:
        # check if the line contains a macro
        was_macro = False
        for pair in required_pairs:
            # check if we want to replace the commented macro
            if line.startswith(pair[0]):
                new_file.write("{}={}\n".format(pair[0],pair[1]))
                was_macro = True
        # Otherwise just write line as-is
        if was_macro == False:
            new_file.write(line)
        line = old_file.readline()


# Function that iterates over the configuration files that pertain to the current arch,
# identifies lines that contain the macros in the list, and replaces them. If not in the list 
# the line is copied as-is. upon completion, the old file is moved into a new "EXAMPLE_FILES"
# directory if it is needed again.
def copy_macro_replace(filename, path_to_configure, required_pairs):
    old_file = open(path_to_configure + filename, "r+")
    # Every example file starts with EXAMPLE_FILENAME, so we disregard the first 8 characters 'EXAMPLE_' for the new name
    new_path = path_to_configure + filename[8:]
    new_file = open(new_path, "w+")
    # Iterate over the lines in the old file, replacing macros as you go
    replace_macros(old_file, new_file, required_pairs)
    old_file.close()
    # Place the old file in a directory for future use.
    shutil.move(path_to_configure + filename, path_to_configure + "EXAMPLE_FILES/{}".format(filename))
    new_file.close()


# function that calls replace macros on any two paths.
def replace_macros_non_ad(old_path, new_path, required_pairs):
    old_file = open(old_path, "r+")
    new_file = open(new_path, "w+")
    replace_macros(old_file, new_file, required_pairs)
    old_file.close()
    new_file.close()
    



# Removes unnecessary example files i.e. vxworks, windows etc.
# This cleans up the configuration directory, and only leaves necessary files.
def remove_examples(path_to_configure):
    for file in os.listdir(path_to_configure):
        if os.path.isfile(path_to_configure+file):
            if file.startswith("EXAMPLE") and not file.endswith(".local") and not file.endswith(EPICS_ARCH):
                if not file.endswith(".Linux"):
                    os.remove(path_to_configure+file)
                else:
                    if not isLinux:
                        os.remove(path_to_configure+file)



# Basic function that iterates over all of the files and directories in the "configure" directory
# of area detector. If it detects "EXAMPLE" files, it passes them on to the macro replacing function
def process_examples(path_to_configure, required_pairs):
    for file in os.listdir(path_to_configure):
        if os.path.isfile(path_to_configure+file):
            if file.startswith("EXAMPLE"):
                copy_macro_replace(file, path_to_configure, required_pairs)


# Function that parses the Build flag config file for updating these values in in AD Configure
def add_build_flags(required_pairs):
    build_flags_file = open("../configure/BUILD_FLAG_CONFIG", "r+")

    line = build_flags_file.readline()
    while line:
        if "=" in line and not line.startswith('#'):
            line = remove_whitespace(line)
            pair = line.split('=')
            required_pairs.append(pair)
            print(pair)
        line = build_flags_file.readline()
    return required_pairs


# Function that inserts into RELEASE_PRODS.local the contents of the
# conigure/AD_RELEASE_CONFIG file
def update_release_prods(path_to_configure):
    os.rename(path_to_configure+"/RELEASE_PRODS.local", path_to_configure+"/RELEASE_PRODS_OLD.local")
    old_file = open(path_to_configure+"/RELEASE_PRODS_OLD.local", "r+")
    new_file = open(path_to_configure+"/RELEASE_PRODS.local", "w+")
    insert_file = open("../configure/AD_RELEASE_CONFIG", "r+")

    line = old_file.readline()
    while line:
        new_file.write(line)
        if "Optional modules" in line:
            new_file.write("\n")
            new_file.write("# The following was auto-inserted by installSynApps\n")
            new_file.write("\n")
            insert_line = insert_file.readline()
            while insert_line:
                if not insert_line.startswith('#'):
                    new_file.write(insert_line)
                insert_line = insert_file.readline()
            new_file.write("\n")
            new_file.write("# Auto-inserted end\n")
            new_file.write("\n")
        line = old_file.readline()

    insert_file.close()
    old_file.close()
    new_file.close()


# Function that renames the example iocStartup files to the appropriate names
def update_common_plugins(path_to_ad):
    if os.path.exists(path_to_ad+"/ADCore/iocBoot/EXAMPLE_commonPlugin_settings.req"):
        os.rename(path_to_ad+"/ADCore/iocBoot/EXAMPLE_commonPlugin_settings.req", path_to_ad+"/ADCore/iocBoot/commonPlugin_settings.req")
    if os.path.exists(path_to_ad+"/ADCore/iocBoot/EXAMPLE_commonPlugins.cmd"):
        os.rename(path_to_ad+"/ADCore/iocBoot/EXAMPLE_commonPlugins.cmd", path_to_ad+"/ADCore/iocBoot/commonPlugins.cmd")


# Function that inserts custom configuration options into the appropriate file
def inject_into_file(file_path, inject_file_path):
    old_file = open(file_path, "a+")
    insert_file = open(inject_file_path, "r+")

    old_file.write("\n")
    old_file.write("# The following was auto-inserted by installSynApps\n")

    line = insert_file.readline()
    while line:
        if not line.startswith('#'):
            old_file.write(line)
        line = insert_file.readline()
    
    old_file.write("\n")
    old_file.write("# Auto-Inserted end\n")

    insert_file.close()
    old_file.close()


# Function that calls all helper functions to update ad RELEASE and configure files
def update_ad_releases(path_to_ad, required_pairs):
    path_to_configure = path_to_ad +"/configure/"
    if not os.path.exists(path_to_configure+"EXAMPLE_FILES"):
        os.mkdir(path_to_configure+"EXAMPLE_FILES")
    required_pairs = add_build_flags(required_pairs)
    remove_examples(path_to_configure)
    process_examples(path_to_configure, required_pairs)
    update_release_prods(path_to_configure)
    update_common_plugins(path_to_ad)
    #update_driver_makefile(path_to_ad)
    inject_into_file(path_to_ad+"/ADCore/iocBoot/commonPlugins.cmd", "../configure/PLUGIN_CONFIG")
    inject_into_file(path_to_ad+"/ADCore/ADApp/commonDriverMakefile", "../configure/MAKEFILE_CONFIG")
    inject_into_file(path_to_ad+"/ADCore/iocBoot/commonPlugin_settings.req", "../configure/AUTOSAVE_CONFIG")


# function of updating configure release files for modules not in AD but also not set by make release
def update_non_ad_releases(path_to_support, module_list, required_pairs):
    for module in module_list:
        os.rename(path_to_support+"/"+module+"/configure/RELEASE", path_to_support+"/"+module+"/configure/RELEASE_OLD")
        replace_macros_non_ad(path_to_support+"/"+module+"/configure/RELEASE", path_to_support+"/"+module+"/configure/RELEASE_OLD", required_pairs)
    


#update_release_prods("/epics/support/areaDetector/configure")