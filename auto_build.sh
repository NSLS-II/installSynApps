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

OS_SPECIFIC=(
    "DEB7_CONFIG"
    "DEB8_CONFIG"
    "DEB9_CONFIG"
)


echo
echo "Would you like to proceed with the default auto-build configuration?"
read -p "(y/n) > " default
echo

if [ "$default" = "y" ];
then
echo "Proceeding with default build configuration"

else
echo "Would you like to specify a OS-Specific build configuration?"
echo "Current options are: ${OS_SPECIFIC[@]}"
read -p "(y/n) > " os_specific
echo

if [ "$os-specific" = "y" ];
then
read -p "Please specify OS from the list above: " os
echo
VALID="NO"
for i in "${OS_SPECIFIC[@]}"; do
if [ "$os" = "$i" ];
then
VALID="YES"
fi
done
if [ "$VALID" = "YES" ];
then
mv configure/INSTALL_CONFIG configure/INSTALL_OLD
mv configure/os_specific/$os configure/INSTALL_CONFIG
echo "Proceeding with $os as install config file"
echo
fi
fi
echo "Please enter the configure directory, and edit all configuration files"
read -p "Press any key to continue once editing is finished" next
fi

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

echo "Beginning auto_build process"
cd scripts
./installSynApps.sh
echo "Completed auto_build process"
echo "Done."
