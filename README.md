# installSynApps

A python3 module meant for cloning and building EPICS, synApps, and areaDetector with one command.

Author: Jakub Wlodek  
Corresponding author: Kazimierz Gofron

This development is based on bash EPICS distribution scripts developed primarly for building on the UNIX/Linux environment, and prior work related to synApps packaging which is utilized by installSynApps is currently hosted at https://github.com/EPICS-synApps

### Usage

There are two recommended usage procedures for the module, through the use of `installCLI.py` and `installGUI.py`. The first will perform all operations through the terminal, while the other will display a GUI written in Tkinter. 

### installCLI

Before running the command line option, you must edit the install configuration stored in the `configure` directory of this program. Open the `INSTALL_CONFIG` file and you will see a large table representing all modules to clone and or build. Make sure to set the install location as desired at the top of the file, along with any other changes. Note that the file is structured so that packages must be below their dependacies. For example, an ADDriver depends on ADCore, which means it has to be below it in the table.

In addition, in the configure directory, there are two folders: `injectionFiles`, and `macroFiles`. In the `injectionFiles` directory, you will find files whose contents are injected into `commonPlugins.cmd`, `RELEASE_PRODS.local`, `commonPlugin_settings.req`, and `commonDriverMakefile`. These injections allow for customizing the areaDetector build past the defaults. In the `macroFiles` directory, all files located there are read and parsed for macro values, which are then used to update the areaDetector configuration. For example writing `JPEG_EXTERNAL=YES` will set the `JPEG_EXTERNAL` macro in the `CONFIG_SITE.local` file in the areaDetector configuration.

Once all of these configuration files are edited to your liking, you may run the script.

To use the command line option, simply run this file either with:
```
./installCLI.py
```
OR
```
python installCLI.py
```
**Note that python 3.* is required for this script to run**

For information on the available options, run with the `-h` flag. After running the file, simply follow the instructions as they guide you through the build process.

### installGUI

The GUI requires Tkinter to be installed for operation. Tkinter is a standard module included with python3, though if it is not it can be installed via `pip` or the package manager as `python3-tk`.

Similar to `installCLI.py`, to use the GUI, simply run it with python3. You will then see the option for each individual operation, along with an autorun that will perform them all sequentially. You may also load another configuration directory, provided that it follows the same file format as the given default configure directory.

The GUI version also allowes finer control of install configurations. In the open window, select the `Edit` menu, then choose an edit option. From there, a window will open allowing you to edit any portion of the install process. You may also save the install configuration with it's edits by selecting the File -> Save As option. When you select File -> Save, the currently loaded config will overwrite whereever it was previously saved.

In addition, the GUI keeps a log of the operations completed, which can be saved to an arbitrary location. Note that if a process is running (as indicated by the animated process status message), you will be unable to run another process.

For further details on using `installGUI`, please check the [documentation](https://epicsNSLS2-deploy.github.io/installSynApps).

### Running on Linux vs. Windows

The installSynApps module requires the following to be in the environment PATH in the terminal in which it is running for proper execution:
* git
* make
* wget
* tar

If these packages are available, then the script should be able to run through the entirety of the build process.

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

**For information regarding the usage of the Legacy scripts of installSynApps, please check the LEGACY.md file in this repo**