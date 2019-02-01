#!/bin/bash

# File that builds EPICS base and synApps from scratch with one call

# First we clone all of the modules
python3 clone_and_checkout.py
python3 updare_release_file.py

# first build the dependencies
./installDependencies.sh

python3 buildEPICS.py