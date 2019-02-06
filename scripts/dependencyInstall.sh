#!/bin/bash

# Script that installs all
# dependencies for modules being built.
# 
# For any custom dependencies, please add them here prior to running the buildSynApps.sh script
#

# Path variables, only used for adding custom dependencies (mostly for detector drivers)
INSTALL=/epics
EPICS_BASE=$INSTALL/base
SUPPORT=$INSTALL/support
AREA_DETECTOR=$SUPPORT/areaDetector

# Example custom dependency, we must build libuvc before compiling ADUVC
ADUVC=$AREA_DETECTOR/ADUVC
ADEIGER=$AREA_DETECTOR/ADEiger

cd $INSTALL

sudo apt -y install gcc
sudo apt -y install g++
sudo apt -y install make
sudo apt -y install libxml2-dev
sudo apt -y install libboost-dev
sudo apt -y install libboost-test-dev
sudo apt -y install libusb-dev
sudo apt -y install libpcre3-dev
sudo apt -y install re2c
sudo apt -y install libx11-dev
sudo apt -y install libxext-dev
sudo apt -y install libopencv-dev
sudo apt -y install libzbar-dev
sudo apt -y install libreadline-dev
sudo apt -y install libusb-dev
sudo apt -y install libusb-1.0-0-dev

if [[ $ADUVC ]]
then
echo "Installing ADUVC dependencies"
sudo apt -y install cmake
cd $ADUVC/adUVCSupport
./installlibuvc.sh
cd $INSTALL
fi

if [[ $ADEIGER ]]
then
echo "Installing ADEiger dependencies"
sudo apt -y install libzmq3-dev
fi
