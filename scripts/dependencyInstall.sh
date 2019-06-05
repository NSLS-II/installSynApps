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

apt-get -y install gcc
apt-get -y install g++
apt-get -y install make
apt-get -y install libxml2-dev
apt-get -y install libboost-dev
apt-get -y install libboost-test-dev
apt-get -y install libboost-system-dev
apt-get -y install libusb-dev
apt-get -y install libpcre3-dev
apt-get -y install re2c
apt-get -y install libx11-dev
apt-get -y install libxext-dev
apt-get -y install libopencv-dev
apt-get -y install libzbar-dev
apt-get -y install libreadline-dev
apt-get -y install libusb-dev
apt-get -y install libusb-1.0-0-dev
apt-get -y install libdmtx-dev


if [[ $ADUVC ]]
then
echo "Installing ADUVC dependencies"
apt-get -y install cmake
cd $ADUVC/adUVCSupport
./installlibuvc.sh
cd $INSTALL
fi


if [[ $ADEIGER ]]
then
echo "Installing ADEiger dependencies"
apt-get -y install libzmq3-dev
fi
