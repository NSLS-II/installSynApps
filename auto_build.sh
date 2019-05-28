#!/bin/bash

# Top Level bash script for using installSynApps, will walk user through the process
# Author: Jakub Wlodek
# Created on: 9-May-2019
echo
echo "+-----------------------------------------------------------------"
echo "+ installSynApps, version R0-1                                   +"
echo "+ Author: Jakub Wlodek                                           +"
echo "+ Copyright (c): Brookhaven National Laboratory 2018-2019        +"
echo "+ This software comes with NO warranty!                          +"
echo "+-----------------------------------------------------------------"
echo
echo "Welcome to the installSynApps module."
echo "It is designed to automate the build process for EPICS and areaDetector."
echo "The scripts included will automatically edit all configuration files"
echo "required, and then build with make."

INSTALL_DIR=`grep INSTALL= configure/INSTALL_CONFIG`
INSTALL=${INSTALL_DIR/INSTALL=/}

INSTALL_OK="NO"

while [ "$INSTALL_OK" != "YES" ]
do
echo
echo "The current install directory is $INSTALL, is this ok?"
read -p "(y/n) > " response
echo

if [ "$response" = "y" ];
then
INSTALL_OK="YES"
echo "Proceeding with Install location $INSTALL"
else
echo "Please enter a custom install location:"
read -p "INSTALL=" INSTALL
fi

done

sed -i "s+INSTALL=.*+INSTALL=$INSTALL+g" configure/INSTALL_CONFIG

echo 
echo "Would you like to proceed with the default auto-build configuration?"
read -p "(y/n) > " default

echo "Beginning auto_build process"
#/scripts/installSynApps.sh

echo "Completed auto_build process"