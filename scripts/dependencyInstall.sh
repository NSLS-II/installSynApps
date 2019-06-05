#!/bin/bash

# Script that installs all
# dependencies for modules being built.
# 
# For any custom dependencies, please add them here prior to running the installSynApps.sh script
#

cd $(dirname $0)

# Path variables, only used for adding custom dependencies (mostly for detector drivers)
#INSTALL=/eApps/epics
INSTALL_DIR=`grep INSTALL= ../configure/INSTALL_CONFIG`
INSTALL=${INSTALL_DIR/INSTALL=/}

EPICS_BASE=$INSTALL/base
SUPPORT=$INSTALL/support
AREA_DETECTOR=$SUPPORT/areaDetector

# Example custom dependency, we must build libuvc before compiling ADUVC
ADUVC=$AREA_DETECTOR/ADUVC
#ADEIGER=$AREA_DETECTOR/ADEiger

cd $INSTALL

sudo apt-get -y install gcc
sudo apt-get -y install g++
sudo apt-get -y install make
sudo apt-get -y install libxml2-dev
sudo apt-get -y install libboost-dev
sudo apt-get -y install libboost-test-dev
sudo apt-get -y install libboost-system-dev
sudo apt-get -y install libusb-dev
sudo apt-get -y install libpcre3-dev
sudo apt-get -y install re2c
sudo apt-get -y install libx11-dev
sudo apt-get -y install libxext-dev
sudo apt-get -y install libopencv-dev
sudo apt-get -y install libzbar-dev
sudo apt-get -y install libreadline-dev
sudo apt-get -y install libusb-dev
sudo apt-get -y install libusb-1.0-0-dev
sudo apt-get -y install libdmtx-dev


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
