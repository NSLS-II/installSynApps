# installSynApps

![Build Status](https://github.com/jwlodek/installSynApps/workflows/test-build/badge.svg) ![Unit Tests](https://github.com/jwlodek/installSynApps/workflows/tests/badge.svg)

A python3 module meant for cloning, building, and packaging EPICS, synApps, and areaDetector with one command.

Author: Jakub Wlodek  
Corresponding author: Kazimierz Gofron

This development is based on bash EPICS distribution scripts developed primarly for building on the UNIX/Linux environment, and prior work related to synApps packaging which is utilized by `installSynApps` is currently hosted at https://github.com/EPICS-synApps

### Installation

installSynApps depends `python3`, and several helper libraries. It is tested with python 3.4+. To install `python3` on linux run:
```
sudo apt install python3
```
In order to use the GUI version of `installSynApps`, tkinter is required as well. This can be installed with:
```
sudo apt install python3-tk
```
on linux, while on windows it should be included in your python download.

Furthermore, install the python `pip` Python Package Installer. This can be installed with:
```
sudo apt install python3-pip
```
Next, clone the repository and install helper libraries with `pip`:
```
git clone https://github.com/epicsNSLS2-deploy/installSynApps
cd installSynApps
python3 -m pip install -r requirements.txt
```
In addition, several external tools are used by installSynApps that must also be installed and in the system path. This can be done with:
```
sudo apt install gcc g++ make git wget tar perl
```
on linux, while on windows each of these should be installed from the appropriate websites. To ensure that they are in the system path, run:
```
make --version
```
or something similar for each of the above dependencies and see if it displays version information. If not, and you see an error along the lines of `make command not found`, then the module is not in the system path. In addition, on windows it is required to install Visual Studio 2015+, along with the `MSVC` and `MSVC++` compilers for `C` and `C++` respectively.

If running on windows, make sure to run `installSynApps` from the Visual Studio developer command prompt, not from `cmd` or `powershell`.

Next, you may wish to install packages required by EPICS and areaDetector:
```
sudo apt install re2c libusb-1.0-0-dev
sudo apt install libx11-dev libxext-dev libzmq3-dev
```

Finally, if you wish, you may install the utility using `pip`, with:
```
pip3 install --upgrade .
```
This will allow you to run the CLI or GUI commands using `epics-install`, or `epics-install-gui` respectively.

### Usage

There are two recommended usage procedures for the module, through the use of `installCLI.py` and `installGUI.py`. The first will perform all operations through the terminal, while the other will display a GUI written in Tkinter. 

### installCLI

Before running the command line option, you must identify an install configuration to use with `installSynApps`. A default config is stored in the `configure` directory of this program, and several other configurations are housed in `addtlConfDirs`. To create a new config, use:
```
./installCLI.py -n -v
```
In your selected configuration, open the `INSTALL_CONFIG` file and you will see a large table representing all modules to clone/build/package. Make sure to set the install location as desired at the top of the file, along with any other changes.

In addition, in the configure directory, there should be several folders: 

Directory | Description
---------|-----------
`injectionFiles` | Files whose contents are injected into certain target configuration files (ex. `commonPlugins.cmd`)
`macroFiles` | Used to specify build macros. (ex. `JPEG_EXTERNAL=YES`)
`customBuildScripts` | Shell/Batch scripts to be run instead of `make` to build a module. (ex. `ADPOINTGREY.sh` would build `ADPointGrey` on Linux instead of `make`)

Once all of these configuration files are edited to your liking, you may run the script.

To see all available options run:
```
./installCLI.py -h
```

And then run with defaults with:
```
./installCLI.py
```
OR
```
python installCLI.py
```
or add any of the optional flags to further configure the build. A typical run will override the default configuration, and install location, along with setting some logging options, and will in some cases be automated with the `-y` flag:
```
./installCLI.py -c addtlConfDirs/configureDeb9 -i /epics/src -p -l -y
```

After executing the script, simply follow the instructions as they guide you through the build process, or if `-y` was used, wait for it to terminate.

### installGUI

The `installSynApps` GUI requires Tkinter to be installed for operation. Tkinter is a standard module included with python3, though if it is not it can be installed via `pip` or the package manager as `python3-tk`.

To start the GUI, run:
```
./installGUI.py
```
This should load the default configuration, or whatever configuration was previously loaded. You can create a new configuration with `File -> New`, or edit the existing one under the `Edit` tab. Make sure to use `File -> Save` to save any changes you make.

Once the configuration is finished, execute the build by pressing `Autorun`. You can then press `Package` to generate the binary bundle after the build terminates.

For further details on using `installGUI`, please check the [documentation](https://epicsNSLS2-deploy.github.io/installSynApps).

### Configuration Directories

`installSynApps` relies on data provided in a configuration directory to execute a build/bundle operation.
There are several configurations included by default with `installSynApps`, and more can be found in the [Install-Configurations](https://github.com/epicsNSLS2-deploy/Install-Configurations) repository.

An example structure of a configuration directory is as follows:
```
jwlodek@HP-Z6-G4-Workstation:/epics/utils/installSynApps/configure$ tree
.
├── customBuildScripts
│   └── ADUVC.sh
├── dependencyInstall.sh
├── injectionFiles
│   ├── AD_RELEASE_CONFIG
│   ├── AUTOSAVE_CONFIG
│   ├── MAKEFILE_CONFIG
│   ├── PLUGIN_CONFIG
│   └── QUADEM_RELEASE
├── INSTALL_CONFIG
└── macroFiles
    └── BUILD_FLAG_CONFIG

3 directories, 9 files
```

Below is a description of all files that are included with a config directory by default when a new one is created.

Configuration file      | Use 
-------------------------|--------------------
INSTALL_CONFIG      | The main configuration file for installSynApps. Use this file to decide which modules to clone and build
AD_RELEASE_CONFIG   | Adds paths to external plugins developed for area detector into the area detector build process.
MAKEFILE_CONFIG     | Injects contents into `ADCore/ADApp/commonDriverMakefile`. Used to build against additional libraries
PLUGIN_CONFIG       | Injects contents into `ADCore/iocBoot/commonPlugins.cmd`. Used to load additional plugins at IOC startup
AUTOSAVE_CONFIG     | Injects contents into `ADCore/iocBoot/commonPlugin_settings.req`. Used to configure IOC autosave feature
BUILD_FLAG_CONFIG   | Allows for manually setting Area Detector build flags ex. `JPEG_EXTERNAL=YES`.
