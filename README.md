# installSynApps

A python3 module meant for cloning and building EPICS, synApps, and areaDetector with one command.

Author: Jakub Wlodek
Corresponding author: Kazimierz Gofron

###
This development is based on bash EPICS distribution scripts developed primarly for UNIX/Linux environment
     https://github.com/epicsNSLS2-deploy/synAppsRelease
and prior work related to synApps packaging currently hosted
    https://github.com/EPICS-synApps
### Usage

There are two recommended usage procedures for the module, through the use of `installCLI.py` and `installGUI.py`. The first will perform all operations through the terminal, while the other will display a GUI written in Tkinter. 

### installCLI

To use the command line option, simply run this file either with:
```
./installCLI.py
```
OR
```
python3 installCLI.py
```
For information on the available options, run with the `-h` flag. After running the file, simply follow the instructions as they guide you through the build process.

### installGUI

Similar to `installCLI.py`, to use the GUI, simply run it with python3. You will then see the option for each individual operation, along with an autorun that will perform them all sequentially. You may also load another configuration directory, provided that it follows the same file format as the given default configure directory.

In addition, the GUI keeps a log of the operations completed, which can be saved to an arbitrary location. Note that if a process is running (as indicated by the animated process status message), you will be unable to run another process.

### Running on Linux vs. Windows

The installSynApps module requires the following to be in the environment PATH in the terminal in which it is running for proper execution:
* git
* make
* wget

If those three packages are available, then the script should be able to run through the entirety of the build process. The only caveat is that when building on windows, the dependency install script (which uses `apt` and `bash`) will not be able to run. This means that modules requiring external packages as dependencies will need these to be compiled and placed in the system path prior to compilation.

In addition, it is possible that on windows the downloaded python 3 .exe file will actually simply be called python. Thus, the scripts must be executed with

```
python installCLI.py
python installGUI.py
```

### Included Configuration files

Configuration file      | Use 
-------------------------|--------------------
INSTALL_CONFIG      | The main configuration file for installSynApps. Use this file to decide which modules to clone and build
AD_RELEASE_CONFIG   | Adds paths to external plugins developed for area detector into the area detector build process.
MAKEFILE_CONFIG     | Injects contents into `ADCore/ADApp/commonDriverMakefile`. Used to build against additional libraries
PLUGIN_CONFIG       | Injects contents into `ADCore/iocBoot/commonPlugins.cmd`. Used to load additional plugins at IOC startup
AUTOSAVE_CONFIG     | Injects contents into `ADCore/iocBoot/commonPlugin_settings.req`. Used to configure IOC autosave feature
BUILD_FLAG_CONFIG   | Allows for manually setting Area Detector build flags ex. `JPEG_EXTERNAL=YES`.

### External Configure

It is possible to use different `configure` directories when using `installSynApps`. To do so, it is required that there is an `INSTALL_CONFIG` file within the selected directory. Additionally, the `fixedRELEASEFiles` directory should be copied as well. The remaining two directories are optional, though a warning will be displayed on load if they are missing.

**BELOW ARE INSTRUCTIONS FOR RUNNING THE LEGACY VERSION OF INSTALLSYNAPPS**

### Auto Build

For most purposes, it is simplest to run the auto-build script, which will give you a guided process through building the modules.
To do this, run:
```
./auto_build.sh
```
The script will first ask if you wish to keep the default build config, which in most cases is yes. Next, it will ask if
the curret install location is OK. If no, simply enter the new install location.

### Included scripts

Script name                    | Script Function
------------------- | ------------------------------------------------------
auto_build.sh | Recommended script that gives a guided build process
installSynApps.sh | top level bash script that runs the remaining scripts sequentially
clone_and_checkout.py | Clones all required repositories and checks out correct versions
read_install_config.py | Script that reads the data in the INSTALL_CONFIG file
update_release_file.py | Script that updates the release files in support and area detector
ad_config_setup.py | Script based on adConfigSetup, that replaces area detector configuration files
dependencyInstall.sh | bash script that installs all required packages for EPICS and synApps
script_generator.py | script that creates bash scripts for installing and uninstalling, so that compilation for other operating systems is simplified.

### Usage

For more granular control over the build process, do the following:  

There are only 2 locations with files that need to be edited before running the script. These are the `configure/*` files, and the `scripts/dependencyInstall.sh` file. In the first, edit the install configurations for your installation. In most cases, you may simply change the `MODULE_INSTALL` tag  in the `INSTALL_CONFIG` file for the modules you wish to build and those you don't wish to build, and you must also edit the line
```
INSTALL=/epics
```
to point to the top level directory in which you wish to install EPICS and synApps. The other files in the `configure/` directory contain other configurations, with each one being inserted into a different Area Detector build file. Details can be found in comments in the files themselves.

In the only other file that you must edit (`scripts/dependencyInstall.sh`). In addition, if there are any other dependencies for your build of EPICS and synApps, add them here. For example, to auto-build the ADUVC driver, libuvc must be built, so I added a condition for building and installing libuvc.

From here, you are ready to run the script, and this is done simply by running:
```
./installSynApps.sh
```
from the /scripts directory. Note that you will be prompted for a sudo password to install the dependency packages. Once the script completes, a new directory `autogenerated` is created, and `install.sh` and `uninstall.sh` files are placed within each. Run the appropriate file to uninstall or recompile the packages appropriately. This should simplify building the same sources on multiple operating systems.
