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



# Function that prints macro value pairs. Used to test external config file support.
def print_pair_list(macro_value_pairs):
    for pair in macro_value_pairs:
        print("A value of '{}' will be assigned to the '{}' macro.\n".format(pair[1], pair[0]))



# Function that iterates over the configuration files that pertain to the current arch,
# identifies lines that contain the macros in the list, and replaces them. If not in the list 
# the line is copied as-is. upon completion, the old file is moved into a new "EXAMPLE_FILES"
# directory if it is needed again.
#
# @params: old_path                 -> path to the example configuration file
# @params: required_pairs           -> pairs macros and values that are guaranteed to be replaced
# @params: optional_pairs           -> pairs macros and values that can optionally be replaced
# @params: replace_optional_macros  -> flag to see if optional macros will be replaced
# @params: replace_commented        -> flag that decides if commented macros are to be replaced as well
# @return: void
#
def copy_macro_replace(filename, path_to_configure, required_pairs, replace_commented = False):
    old_file = open(path_to_configure + filename, "r+")
    # Every example file starts with EXAMPLE_FILENAME, so we disregard the first 8 characters 'EXAMPLE_' for the new name
    new_path = path_to_configure + filename[8:]
    new_file = open(new_path, "w+")
    # Iterate over the lines in the old file, replacing macros as you go
    line = old_file.readline()
    while line:
        # check if the line contains a macro
        was_macro = False
        for pair in required_pairs:
            # check if we want to replace the commented macro
            if replace_commented and line[0] == '#':
                line = line[1:]
            if line.startswith(pair[0]):
                new_file.write("{}={}\n".format(pair[0],pair[1]))
                was_macro = True
        # Otherwise just write line as-is
        if was_macro == False:
            new_file.write(line)
        line = old_file.readline()
    old_file.close()
    # Place the old file in a directory for future use.
    shutil.move(path_to_configure + filename, path_to_configure + "EXAMPLE_FILES/{}".format(filename))
    new_file.close()



# Removes unnecessary example files i.e. vxworks, windows etc.
# This cleans up the configuration directory, and only leaves necessary files.
#
# If building for multilple architectures, do not use the -r flag enabling this.
# In the future, a toggle between arches will be looked at.
#
# @return: void
#
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
#
# @params: path_to_configure        -> path to the configure directory of area detector
# @params: required_pairs           -> recquired macro/value pairs
# @return: void
#
def process_examples(path_to_configure, required_pairs):
    for file in os.listdir(path_to_configure):
        if os.path.isfile(path_to_configure+file):
            if file.startswith("EXAMPLE"):
                copy_macro_replace(file, path_to_configure, required_pairs)


# Function that inserts into RELEASE_PRODS.local the contents of the
# conigure/AD_RELEASE_CONFIG file
#
# @params: path to configure
# @return: void
#
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
                if not line.startswith('#'):
                    new_file.write(insert_line)
                insert_line = insert_file.readline()
            new_file.write("\n")
            new_file.write("# Auto-inserted end\n")
            new_file.write("\n")
        line = old_file.readline()

    insert_file.close()
    old_file.close()
    new_file.close()


def update_common_plugins(path_to_ad):
    os.rename(path_to_ad+"/ADCore/iocBoot/EXAMPLE_commonPlugins.cmd", path_to_ad+"/ADCore/iocBoot/commonPlugins.cmd")
    os.rename(path_to_ad+"/ADCore/iocBoot/EXAMPLE_commonPlugin_settings.req", path_to_ad+"/ADCore/iocBoot/commonPlugin_settings.req")
    old_file = open(path_to_ad+"/ADCore/iocBoot/commonPlugins.cmd", "a+")
    insert_file = open("../configure/PLUGIN_CONFIG", "r+")

    old_file.write("\n")
    old_file.write("# The following was auto-inserted by installSynApps\n")
    old_file.write("\n")

    line = insert_file.readline()
    while line:
        if not line.startswith('#'):
            old_file.write(line)
        line = insert_file.readline()
    
    old_file.write("\n")
    old_file.write("# Auto-Inserted end\n")
    old_file.write("\n")

    insert_file.close()
    old_file.close()

    
def update_driver_makefile(path_to_ad):
    old_file = open(path_to_ad+"/ADCore/ADApp/commonDriverMakefile", "a+")
    insert_file = open("../configure/MAKEFILE_CONFIG", "r+")

    old_file.write("\n")
    old_file.write("# The following was auto-inserted by installSynApps\n")
    old_file.write("\n")

    line = insert_file.readline()
    while line:
        if not line.startswith('#'):
            old_file.write(line)
        line = insert_file.readline()
    
    old_file.write("\n")
    old_file.write("# Auto-Inserted end\n")
    old_file.write("\n")

    insert_file.close()
    old_file.close()


def update_ad_releases(path_to_ad, required_pairs):
    path_to_configure = path_to_ad +"/configure/"
    if not os.path.exists(path_to_configure+"EXAMPLE_FILES"):
        os.mkdir(path_to_configure+"EXAMPLE_FILES")
    remove_examples(path_to_configure)
    process_examples(path_to_configure, required_pairs)
    update_release_prods(path_to_configure)
    update_common_plugins(path_to_ad)
    update_driver_makefile(path_to_ad)