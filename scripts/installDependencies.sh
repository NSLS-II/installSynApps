#!/bin/bash

# Script that installs all
# dependencies for modules being built.
# 
# For any custom dependencies, please add them here prior to running the buildSynApps.sh script
#

# Path variables, only used for adding custom dependencies (mostly for detector drivers)
INSTALL=/home/jwlodek/Documents/testCloneRun
EPICS_BASE=$INSTALL/base
SUPPORT=$INSTALL/support
AREA_DETECTOR=$SUPPORT/areaDetector

# Example custom dependency, we must build libuvc before compiling ADUVC
ADUVC=$AREA_DETECTOR/ADUVC

cd $INSTALL

sudo apt install gcc
sudo apt install g++
sudo apt install make
sudo apt install libxml2-dev
sudo apt install libboost-dev
sudo apt install libusb-dev
sudo apt install libpcre3-dev
sudo apt install re2c
sudo apt install libopencv-dev
sudo apt install libzbar-dev
sudo apt install libreadline-dev


if [[ $ADUVC ]]
then
echo "Installing ADUVC dependencies"
cd $ADUVC/adUVCSupport
./installlibuvc.sh
cd $INSTALL
fi