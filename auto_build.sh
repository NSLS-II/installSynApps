#!/bin/bash

# Top Level bash script for using installSynApps, will walk user through the process
# Author: Jakub Wlodek
# Created on: 9-May-2019

echo "+---------------------------------------------------------"
echo "+ installSynApps, version R0-1"
echo "+ Author: Jakub Wlodek"
echo "+ Copyright (c): Brookhaven National Laboratory 2018-2019"
echo "+ This software comes with NO warranty!"
echo "+---------------------------------------------------------"
echo "\n\n"
echo "Welcome to the installSynApps module."
echo "It is designed to automate the build process for EPICS and areaDetector."
echo "The scripts included will automatically edit all configuration files required, and then build with make."

INSTALL_DIR=`grep INSTALL= configure/INSTALL_CONFIG`
INSTALL=${INSTALL_DIR/INSTALL=/}

echo "The current install directory is $INSTALL, is this ok?"
echo "(y/n)"
read response

if [ "$response" = "y" ];
then
echo "Proceeding with Install location $INSTALL"
else
echo "Please enter a custom install location:"
echo "INSTALL="
read INSTALL
fi

echo "Beginning auto_build process"
/scripts/installSynApps.sh

echo "Completed auto_build process"
