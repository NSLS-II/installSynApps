#!/bin/bash

# File that builds EPICS base and synApps from scratch with one call

# First we clone all of the modules
python3 clone_and_checkout.py

# first build the dependencies
./installDependencies.sh

python3 buildEPICS.py