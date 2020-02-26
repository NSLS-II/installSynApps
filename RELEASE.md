# installSynApps Releases

<!--RELEASE START-->

## R2-5 (26-Febuary-2020)

* Features Added
    * Utilize improved `README` file format for source bundles
    * New Screen for creating new configurations.
    * `setup.py` file worked on. Can install both scripts, but need external configuration
    * `regenerateSources.sh` script is now generated during build. Can be used to recreate sources.

* Bug Fixes/Improvements
    * Fixed several minor issues causing failed module building with default `configure` directory
    * New configs should now have populated `injectionFiles` and `macroFiles` directories.
    * Fix issue with building `QuadEM` on certain distributions. 
    * Remove some unnecessary prompts from `installCLI`
    * Fix minor issues found by linter in `installGUI`
    * Refactor `installCLI` for more modularity
    * Fix sync-tags auto overwrite in GUI
    * Add injection and macro files to resources (were missing from new configs)
    * More robust debug options
    * Renamed submodules for consistency

* Future Plans
    * Improve documentation - Use sphinx for auto-building docs from source code
    * Include better handling of module by module dependency packages
    * Work on improving support for auto-building motion IOCs.
    * Add more support for running `installSynApps` in an automated environment (`ansible`)

## R2-4 (10-January-2020)

* Features Added
    * OPI directory generation - Creates OPI bundle from all modules in configuration
    * Add-On Generation. Create an add on package to add new modules to existing bundles.
    * Parser now can update module path macros in macro files prior to configure update step.

* Bug Fixes/Improvements
    * Removed pygithub dependancy. Versions are now updated using `git ls-remote`
    * Improved version detection. Tags are now better analyzed to avoid false positives.
    * Fix bug on version sync in `installCLI` where updated versions wouldn't save
    * Moved printing of commands to logging module
    * Reorganize packager to remove redundant code
    * In-code documentation improved for `installGUI`

* Future Plans
    * Improve automation for version updates (So Docker-Builder can perform these itself)
    * Add error handling for an expanded set of edge-cases

## R2-3 (12-November-2019)

* Features Added
    * Automatic dependency detection. Modules are now reordered prior to building to account for dependencies
    * Improved logging. Dedicated module that gives for several degrees of granularity
    * Ability to select between flat/non-flat binaries
    * Ability to print bash/batch commands as they are printed

* Bug Fixes/Improvements
    * Greatly simplified build_driver module code.
    * Simplified packager. Packager now pulls from module.version for wget modules
    * Improved failure conditions. installSynApps should now better respond to non-critical errors.

* Future Plans
    * Improve documentation
    * Integrate with database for install configuration storage.

## R2-2 (21-August-2019)

* Features Added
    * Integration with the github api via PyGithub to allow for version sync
    * Custom build script support - can now specify a custom build script for each non-core module
    * Option to manually set package output name
    * Option to manually specify install location in installCLI.py
    * Custom dependency script is now run before clone if selected.

* Bug Fixes/Improvements
    * Install location changes automatically whether on windows or linux
    * import guards now allow the program to run even if certain optional dependencies are missing
    * Improved error conditions should allow build to run smoother if issues are encountered.

* Future Plans
    * Improve log messages
    * Module reordering.

## R2-1 (09-August-2019)

* Features Added
    * Integrated Packager - Can now create AD binary bundles directly from installSynApps
    * Metadata - Settings are now saved accross uses, so you don't need to keep loading configs
    * Core count regulation - Regulate maximum core count used by installSynApps
        * Useful for lower power devices
    * ConfigWriter - dedicated module for saving install configurations
    * installCLI automation - installCLI can now run fully automated without any user input
        * Can Clone, Update, Compile, and Package with one command
    * TravisCI automated testing added

* Bug Fixes
    * Removed unneccessary print statements in installCLI
    * Fixed issue where editing the configuration would not refresh any modules aside from builder
    * Expanded error checking - should fail more gracefully

* Future Plans
    * Add support for custom build scripts for each module
    * Add improved support for custom dependency scripts

## R2-0 (10-July-2019)

* Features Added
    * Rework of installSynApps with code readability and cross-platform support in mind.
    * Legacy scripts still included, with slight edits  to support new configure format
    * New installSynApps python module - allows for importing into other code.
    * Modular solution - Easy port to CLI and GUI versions
        * DataModel/ViewModel
    * New GUI version, with ability to edit almost all config options.
    * Tested an working on windows systems as well as linux - bash dependencies removed.
    * Changed License 
    * Added unit testing and CI integration
    * Split `initIOCs` to separate module

* Bug Fixes
    * Numerous edge case error checking fixes
    * Thread cleanup fixes
    * Improved reliablility of auto-configuration
    * Fixes bugs that were caused from unexpected formats in Install configuration

* Future Plans
    * Integrate packager from `ioc_deploy`
    * Add support for metadata and saving settings from session to session


## R1-0 (30-May-2019)

* Features Added
    * Initial release of installSynApps
    * Based around a series of scripts
    * Included scripts
        * auto_build.sh - guided process through running remaining scripts
        * installSynApps.sh - top level script that ran the remaining ones sequentially
        * dependencyInstall.sh - Script for installing dependency packages
        * read_install_config.py - Script for reading provided configure folder
        * clone_and_checkout.py - script for cloning and checking out all modules
        * ad_config_setup.py - port of adConfigSetup module - allowed for auto-config of areaDetector files
        * update_release_file.py - top level script for updating configuration options
        * buildEPICS.py - script for calling build commands
        * script_generator.py - autogenerates some helpful information about build

* Limitations:
    * Reliant on bash - only ran on Linux-based systems
    * Required constant edits of configure/INSTALL_CONFIG file.
    * No support for multiple configure directories
    * Code readability issues - arrays used to represent installation modules
    * Limited customizability
    * Issues when running scripts individually
