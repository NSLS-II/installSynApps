# Additional configure Dirs

This directory contains additional configure directories that can be loaded for use with `installSynApps`.
It allows users to quickly choose which build they are targeting, with minimal configure file editing.

### List of configure Dirs

Below is a list of additional `configure` directories included here:
* `configureWindows` - an install configuration edited to build on windows.
* `configureDeb7` - an install configuration known to build on Debian 7
* `configureDeb8` - an install configuration known to build on Debian 8
* `configureDeb9` - an install configuration known to build on Debian 9
* `minConfigureLinux` -  a minimum required install config for compiling EPICS base, support, areaDetector, and ADSimDetector on linux in the `/epics` default dir
* `minConfigureWindows` -  a minimum required install config for compiling EPICS base, support, areaDetector, and ADSimDetector on windows in the `C:\epics` default dir
* `visionPluginConfig` - a configure directory that adds all NSLS2 developed computer vision plugins as enabled by default. (Note that this config will build OpenCV from source, and so will take a significantly longer duration than most other configurations)
* `fullConfigureLinux` - a configure directory that contains AreaDetector and Motor modules
