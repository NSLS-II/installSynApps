# Additional configure Dirs

This directory contains additional configure directories that can be loaded for use with `installSynApps`.
It allows users to quickly choose which build they are targeting, with minimal configure file editing.

### List of configure Dirs

Below is a list of additional `configure` directories included here:
* `configureWindows` - an install configuration edited to build on windows.
* `minConfigureLinux` -  a minimum required install config for compiling EPICS base, support, areaDetector, and ADSimDetector on linux in the `/epics` default dir
* `minConfigureWindows` -  a minimum required install config for compiling EPICS base, support, areaDetector, and ADSimDetector on windows in the `C:\epics` default dir
* `testConfigWindows` - a configure dir for setting up a test build environment on windows for ADCompVision and ADUVC development.
* `visionPluginConfig` - a configure directory that adds all NSLS2 developed computer vision plugins as enabled by default.