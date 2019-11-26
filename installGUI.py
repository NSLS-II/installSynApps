#!/usr/bin/env python3

""" GUI class for the installSynApps module

This GUI solution allows for much easier use of the installSynApps module 
to clone, update, and build the EPICS and synApps software stack.
"""

__author__      = "Jakub Wlodek"
__copyright__   = "Copyright June 2019, Brookhaven Science Associates"
__version__     = "R2-3"


# Tkinter imports
import tkinter as tk
from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
from tkinter import simpledialog
from tkinter import font as tkFont
import tkinter.scrolledtext as ScrolledText

# pygithub for github autosync tags integration.
WITH_PYGITHUB=True
try:
    from github import Github
except ImportError:
    WITH_PYGITHUB=False

# Some python utility libs
import os
import time
import shutil
import datetime
import threading
import webbrowser
import subprocess
from sys import platform

# installSynApps module imports
import installSynApps.DataModel as DataModel
import installSynApps.IO as IO
import installSynApps.Driver as Driver
import installSynApps.ViewModel as ViewModel


class InstallSynAppsGUI:
    """
    Class representing GUI for using installSynApps

    Attributes
    ----------
    master : Tk
        the root frame of the GUI
    smallFont, largeFont
        tkfonts used by the application
    control buttons
        8 tk buttons linked to control operations
    log and configPanel
        scrollable panels that display current information
    thread and loadingIconThread
        threads used for asynchronous usage of the module
    installSynApps modules
        loaded instances of installSynApps objects that drive the process
    
    Methods
    -------
    loadingloop
        Method that creates a loading animation
    writeToLog
        Method that appends to the log
    showMessage, showWarningMessage, showErrorMessage
        Methods for displaying output messages
    initLogText
        returns initial log text
    updateConfigPanel
        Syncs the config panel with the currently loaded config
    updateAllRefs
        Updates references to install config so that build remains consistent
    recheckDeps
        Function that checks if dependancies are in the system path
    newConfig
        Function that asks user for an install location, and then loads a basic install config with that path.
    loadConfig
        event function that gives directory selection prompt and loads configure if dir is valid
    saveConfig
        overwrites the existing config path with whatever changes had been added
    saveConfigAs
        Opens dialog for file path, and saves to a specific directory
    openEditWindow
        Function that opens appropriate edit window depending on argument.
    injectFilesProcess
        process function for injecting into files
    updateConfigProcess
        process function for updating RELEASE and configuration files
    cloneConfigProcess
        process function for cloning all selected modules
    buildConfigProcess
        process function for building all selected modules
    autorunProcss
        process function for building all selected modules
    loadHelp
        prints help information
    saveLog
        prompts for save location of log file
    """

    def __init__(self, master):
        """ Constructor for InstallSynAppGUI """

        # Initialize the frame and window
        self.master = master
        self.master.protocol('WM_DELETE_WINDOW', self.close_cleanup)
        self.smallFont = tkFont.Font(family = "Helvetica", size = 10)
        self.largeFont = tkFont.Font(family = "Helvetica", size = 14)
        frame = Frame(self.master)
        frame.pack()

        IO.logger.assign_write_function(self.writeToLog)

        # core count, dependency install, and popups toggles
        self.showPopups = tk.BooleanVar()
        self.showPopups.set(False)
        self.installDep = tk.BooleanVar()
        self.installDep.set(False)
        self.singleCore = tk.BooleanVar()
        self.singleCore.set(False)

        # Debug togges
        self.showDebug = tk.BooleanVar()
        self.showDebug.set(False)
        self.showCommands = tk.BooleanVar()
        self.showCommands.set(False)
        self.generateLogFile = tk.BooleanVar()
        self.generateLogFile.set(False)

        self.binariesFlatToggle = tk.BooleanVar()
        self.binariesFlatToggle.set(True)

        menubar = Menu(self.master)

        # File menu
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label='New AD Config',         command=lambda : self.newConfig('AD'))
        filemenu.add_command(label='New Motor Config',      command=lambda : self.newConfig('Motor'))
        filemenu.add_command(label='New Full Config',       command=lambda: self.newConfig('All'))
        filemenu.add_command(label='Open',      command=self.loadConfig)
        filemenu.add_command(label='Save',      command=self.saveConfig)
        filemenu.add_command(label='Save As',   command=self.saveConfigAs)
        filemenu.add_command(label='Sync Tags', command=self.syncTags)
        filemenu.add_command(label='Exit',      command=self.close_cleanup)
        menubar.add_cascade(label='File', menu=filemenu)

        # Edit Menu
        editmenu = Menu(menubar, tearoff=0)
        editmenu.add_command(label='Edit Config',               command=lambda : self.openEditWindow('edit_config'))
        editmenu.add_command(label='Add New Module',            command=lambda : self.openEditWindow('add_module'))
        editmenu.add_command(label='Edit Individual Module',    command=lambda : self.openEditWindow('edit_single_mod'))
        editmenu.add_command(label='Edit Custom Build Scripts', command=lambda : self.openEditWindow('add_custom_build_script'))
        editmenu.add_command(label='Edit Injection Files',      command=lambda : self.openEditWindow('edit_injectors'))
        editmenu.add_command(label='Edit Build Flags',          command=lambda : self.openEditWindow('edit_build_flags'))
        editmenu.add_command(label='Edit Make Core Count',      command=self.editCoreCount)
        editmenu.add_checkbutton(label='Toggle Popups',         onvalue=True, offvalue=False, variable=self.showPopups)
        editmenu.add_checkbutton(label='Toggle Single Core',    onvalue=True, offvalue=False, variable=self.singleCore)
        self.singleCore.trace('w', self.setSingleCore)
        menubar.add_cascade(label='Edit', menu=editmenu)

        # Debug Menu
        debugmenu = Menu(menubar, tearoff = 0)
        debugmenu.add_command(label='Print Loaded Config Info', command=self.printLoadedConfigInfo)
        debugmenu.add_command(label='Clear Log',                command=self.resetLog)
        debugmenu.add_command(label='Recheck Dependancies',     command=self.recheckDeps)
        debugmenu.add_command(label='Print Path Information',   command=self.printPathInfo)
        debugmenu.add_checkbutton(label='Show Debug Messages',  onvalue=True, offvalue=False, variable=self.showDebug)
        debugmenu.add_checkbutton(label='Show Commands',        onvalue=True, offvalue=False, variable=self.showCommands)
        debugmenu.add_checkbutton(label='Auto-Generate Log File',    onvalue=True, offvalue=False, variable=self.generateLogFile)
        menubar.add_cascade(label='Debug', menu=debugmenu)

        # Build Menu
        buildmenu = Menu(menubar, tearoff=0)
        buildmenu.add_command(label='Autorun',                  command=lambda : self.initBuildProcess('autorun'))
        buildmenu.add_command(label='Run Dependency Script',    command=lambda : self.initBuildProcess('install-dependencies'))
        buildmenu.add_command(label='Clone Modules',            command=lambda : self.initBuildProcess('clone'))
        buildmenu.add_command(label='Update Config Files',      command=lambda : self.initBuildProcess('update'))
        buildmenu.add_command(label='Inject into Files',        command=lambda : self.initBuildProcess('inject'))
        buildmenu.add_command(label='Build Modules',            command=lambda : self.initBuildProcess('build'))
        buildmenu.add_command(label='Edit Dependency Script',   command=lambda : self.openEditWindow('edit_dependency_script'))
        buildmenu.add_checkbutton(label='Toggle Install Dependencies', onvalue=True, offvalue=False, variable=self.installDep)
        menubar.add_cascade(label='Build', menu=buildmenu)

        # Package Menu
        packagemenu = Menu(menubar, tearoff=0)
        packagemenu.add_command(label='Select Package Destination', command=self.selectPackageDestination)
        packagemenu.add_command(label='Package Modules',            command=lambda : self.initBuildProcess('package'))
        packagemenu.add_command(label='Copy and Unpack',            command=lambda : self.initBuildProcess('moveunpack'))
        packagemenu.add_command(label='Set Output Pacakge Name',    command=self.setOutputPackageName)
        packagemenu.add_checkbutton(label='Toggle Flat Binaries',   onvalue=True, offvalue=False, variable=self.binariesFlatToggle)
        menubar.add_cascade(label='Package', menu=packagemenu)

        # InitIOCs Menu
        iocmenu = Menu(menubar, tearoff=0)
        iocmenu.add_command(label='Get initIOCs', command=self.getInitIOCs)
        iocmenu.add_command(label='Launch initIOCs', command=self.launchInitIOCs)
        menubar.add_cascade(label='IOCs', menu=iocmenu)

        # Help Menu
        helpmenu = Menu(menubar, tearoff=0)
        helpmenu.add_command(label='Quick Help',                command=self.loadHelp)
        helpmenu.add_command(label='Required dependencies',     command=self.printDependencies)
        helpmenu.add_command(label='installSynApps on Github',  command=lambda : webbrowser.open("https://github.com/epicsNSLS2-deploy/installSynApps", new=2))
        helpmenu.add_command(label='Report an issue',           command=lambda : webbrowser.open("https://github.com/epicsNSLS2-deploy/installSynApps/issues", new=2))
        helpmenu.add_command(label='Custom Build Script Help',  command=self.depScriptHelp)
        helpmenu.add_command(label='Online Documentation',      command=lambda : webbrowser.open("https://epicsNSLS2-deploy.github.io/installSynApps", new=2))
        helpmenu.add_command(label='About',                     command=self.showAbout)
        menubar.add_cascade(label='Help', menu=helpmenu)

        self.master.config(menu=menubar)

        self.msg = "Welcome to installSynApps!"

        # Because EPICS versioning is not as standardized as it should be, certain modules cannot be properly auto updated.
        # Ex. Calc version R3-7-3 is most recent, but R5-* exists?
        self.update_tags_blacklist = ["SSCAN", "CALC", "STREAM"]

        # title label
        self.topLabel       = Label(frame, text = self.msg, width = '25', height = '1', relief = SUNKEN, borderwidth = 1, bg = 'blue', fg = 'white', font = self.largeFont)
        self.topLabel.grid(row = 0, column = 0, padx = 10, pady = 10, columnspan = 2)

        # Control buttons
        self.loadButton     = Button(frame, font=self.smallFont, text='Load Config',    command=self.loadConfig,                            height='3', width='20')
        self.cloneButton    = Button(frame, font=self.smallFont, text='Clone Modules',  command=lambda : self.initBuildProcess('clone'),    height='3', width='20')
        self.updateButton   = Button(frame, font=self.smallFont, text='Update RELEASE', command=lambda : self.initBuildProcess('update'),   height='3', width='20')
        self.injectButton   = Button(frame, font=self.smallFont, text='Inject Files',   command=lambda : self.initBuildProcess('inject'),   height='3', width='20')
        self.buildButton    = Button(frame, font=self.smallFont, text='Build Modules',  command=lambda : self.initBuildProcess('build'),    height='3', width='20')
        self.autorunButton  = Button(frame, font=self.smallFont, text='Autorun',        command=lambda : self.initBuildProcess('autorun'),  height='3', width='20')
        self.packageButton  = Button(frame, font=self.smallFont, text='Package',        command=lambda : self.initBuildProcess('package'),  height='3', width='20')
        self.saveLog        = Button(frame, font=self.smallFont, text='Save Log',       command=self.saveLog,                               height='3', width='20')

        self.loadButton.grid(   row = 1, column = 0, padx = 15, pady = 15, columnspan = 1)
        self.cloneButton.grid(  row = 1, column = 1, padx = 15, pady = 15, columnspan = 1)
        self.updateButton.grid( row = 2, column = 0, padx = 15, pady = 15, columnspan = 1)
        self.injectButton.grid( row = 2, column = 1, padx = 15, pady = 15, columnspan = 1)
        self.buildButton.grid(  row = 3, column = 0, padx = 15, pady = 15, columnspan = 1)
        self.autorunButton.grid(row = 3, column = 1, padx = 15, pady = 15, columnspan = 1)
        self.packageButton.grid(row = 4, column = 0, padx = 15, pady = 15, columnspan = 1)
        self.saveLog.grid(      row = 4, column = 1, padx = 15, pady = 15, columnspan = 1)


        # Log and loading label
        #self.logLabel       = Label(frame, text = 'Log', font = self.smallFont, height = '1').grid(row = 0, column = 6, pady = 0, columnspan = 1)
        self.logButton      = Button(frame, text='Clear Log', font=self.smallFont, height='1', command=self.resetLog).grid(row = 0, column = 7, pady = 0, columnspan = 1)
        self.loadingLabel   = Label(frame, text = 'Process Thread Status: Done.', anchor=W, font=self.smallFont, height = '1')
        self.loadingLabel.grid(row = 0, column = 2, pady = 0, columnspan = 2)

        # config panel
        self.configPanel = ScrolledText.ScrolledText(frame, width = '50', height = '20')
        self.configPanel.grid(row = 5, column = 0, padx = 15, pady = 15, columnspan = 2, rowspan = 2)

        # log panel + initialize text
        self.log = ScrolledText.ScrolledText(frame, height = '40', width = '70')
        self.log.grid(row = 1, column = 2, padx = 15, pady = 15, columnspan = 6, rowspan = 6)
        self.writeToLog(self.initLogText())

        # default configure path
        self.configure_path = 'configure'
        self.configure_path = os.path.abspath(self.configure_path)
        self.valid_install = False
        self.deps_found = True
        self.install_loaded = False

        self.metacontroller = ViewModel.meta_pref_control.MetaDataController()
        if 'configure_path' in self.metacontroller.metadata.keys():
            self.configure_path = self.metacontroller.metadata['configure_path']
            if self.configure_path != 'configure':
                self.install_loaded = True
            self.writeToLog('Loading configure directory saved in location {}\n'.format(self.configure_path))

        self.metacontroller.metadata['isa_version'] = __version__
        self.metacontroller.metadata['platform']    = platform
        self.metacontroller.metadata['last_used']   = '{}'.format(datetime.datetime.now())

        # installSynApps options, initialzie + read default configure files
        self.parser = IO.config_parser.ConfigParser(self.configure_path)

        self.install_config, message = self.parser.parse_install_config(allow_illegal=True)

        if message is not None:
            self.valid_install = False
            self.showWarningMessage('Warning', 'Illegal Install Config: {}'.format(message), force_popup=True)
        else:
            self.valid_install = True

        # Threads for async operation
        self.thread = threading.Thread()
        self.loadingIconThread = threading.Thread()

        # installSynApps drivers
        self.writer         = IO.config_writer.ConfigWriter(self.install_config)
        self.cloner         = Driver.clone_driver.CloneDriver(self.install_config)
        self.updater        = Driver.update_config_driver.UpdateConfigDriver(self.configure_path, self.install_config)
        self.builder        = Driver.build_driver.BuildDriver(self.install_config, 0)
        self.packager       = Driver.packager_driver.Packager(self.install_config)
        if 'package_location' in self.metacontroller.metadata.keys():
            self.packager.output_location = self.metacontroller.metadata['package_location']
            self.writeToLog('Loaded package output location: {}\n'.format(self.packager.output_location))
        self.package_output_filename = None
        if 'package_output_filename' in self.metacontroller.metadata.keys():
            self.package_output_filename = self.metacontroller.metadata['package_output_filename']

        self.autogenerator  = IO.script_generator.ScriptGenerator(self.install_config)

        self.recheckDeps()

        if self.install_config is not None:
            self.updateConfigPanel()
        else:
            self.showErrorMessage('Load error', 'Error loading default install config... {}'.format(message), force_popup=True)



# -------------------------- Helper functions ----------------------------------


    def loadingLoop(self):
        """
        Simple function for playing animation when main process thread is executing
        """

        icons = ['\\', '|', '/', '-']
        icon_counter = 0
        while self.thread.is_alive():
            self.loadingLabel.config(text = 'Process Thread Status: {}'.format(icons[icon_counter]))
            time.sleep(0.25)
            icon_counter = icon_counter + 1
            if icon_counter == len(icons):
                icon_counter = 0
        self.loadingLabel.config(text = 'Process Thread Status: Done.')


    def initLogText(self):
        """ Function that initializes log text """

        text = "+----------------------------------------------------------------+\n"
        text = text + "+ installSynApps, version: {:<38}+\n".format(__version__)
        text = text +"+ Author: Jakub Wlodek                                           +\n"
        text = text +"+ Copyright (c): Brookhaven National Laboratory 2018-2019        +\n"
        text = text +"+ This software comes with NO warranty!                          +\n"
        text = text +"+----------------------------------------------------------------+\n\n"
        return text


    def resetLog(self):
        """ Function that resets the log """

        self.log.delete('1.0', END)
        self.writeToLog(self.initLogText())


    def updateConfigPanel(self):
        """
        Function that refreshes the config panel contents if a new InstallConfiguration is loaded
        """

        self.configPanel.delete('1.0', END)
        self.writeToLog("Writing Install Configuration to info panel...\n")
        if self.install_config is not None:
            self.writeToConfigPanel("Currently Loaded Install Configuration:\n\n")
            self.writeToConfigPanel("Install Location: {}\n\n".format(self.install_config.install_location))
            self.writeToConfigPanel("Modules to auto-build:\n-------------------------------\n")
            for module in self.install_config.get_module_list():
                if module.build == "YES":
                    self.writeToConfigPanel("Name: {},\t\t\tVersion: {}\n".format(module.name, module.version))
            self.writeToConfigPanel("\nModules with detected custom build scripts:\n----------------------------\n")
            for module in self.install_config.get_module_list():
                if module.custom_build_script_path is not None:
                    self.writeToConfigPanel("Name: {},\t\t\t Version: {}\n".format(module.name, module.version))

            self.writeToConfigPanel("\nModules to clone but not build:\n----------------------------\n")
            for module in self.install_config.get_module_list():
                if module.build == "NO" and module.clone == "YES":
                    self.writeToConfigPanel("Name: {},\t\t\t Version: {}\n".format(module.name, module.version))

            self.writeToConfigPanel("\nModules to package:\n-----------------------------\n")
            for module in self.install_config.get_module_list():
                if module.package == "YES":
                    self.writeToConfigPanel("Name: {},\t\t\t Version: {}\n".format(module.name, module.version))

            self.writeToLog("Done.\n")
        else:
            self.showErrorMessage("Config Error", "ERROR - Could not display Install Configuration: not loaded correctly")


    def updateAllRefs(self, install_config):
        """ Function that updates all references to install config and configure path """

        self.install_config = install_config
        self.writer.install_config = self.install_config
        self.cloner.install_config = self.install_config
        self.updater.install_config = self.install_config
        self.updater.path_to_configure = self.configure_path
        self.updater.config_injector.install_config = self.install_config
        self.builder.install_config = self.install_config
        self.packager.install_config = self.install_config
        self.autogenerator.install_config = self.install_config


    def recheckDeps(self):
        """ Wrapper function for checking for installed dependancies """

        self.writeToLog('Checking for installed dependancies...\n')
        inPath, missing = self.builder.check_dependencies_in_path()
        if not inPath:
            self.showErrorMessage('Error', 'ERROR- Could not find {} in system path.'.format(missing), force_popup=True)
            self.deps_found = False
        else:
            self.deps_found = True
        if not self.packager.found_distro:
            self.writeToLog('Distro python package not found.\nTarball names will be generic and not distribution specific.\n')
            self.writeToLog('To install distro, use pip: pip install distro\n')
        self.writeToLog('Done.\n')


    def close_cleanup(self):
        """ Function that asks user if he/she wants to close, and cleans up threads """

        if self.thread.is_alive():
            self.showWarningMessage('Warning', 'Qutting while process is running may result in invalid installation!', force_popup=True)
        if messagebox.askokcancel('Quit', 'Do you want to quit?'):
            self.master.destroy()
        IO.logger.close_logger()
        self.metacontroller.save_metadata()


# -------------------------- Functions for writing/displaying information ----------------------------------


    def writeToLog(self, text):
        """ Function that writes to log """

        self.log.insert(INSERT, text)
        self.log.see(END)


    def writeToConfigPanel(self, text):
        """ Function that writes to the config panel """

        self.configPanel.insert(INSERT, text)


    def showErrorMessage(self, title, text, force_popup = False):
        """ Function that displays error popup and log message """

        if self.showPopups.get() or force_popup:
            messagebox.showerror(title, text)
        self.writeToLog(text + "\n")


    def showWarningMessage(self, title, text, force_popup = False):
        """ Function that displays warning popup and log message """

        if self.showPopups.get() or force_popup:
            messagebox.showwarning(title, text)
        self.writeToLog(text + "\n")


    def showMessage(self, title, text, force_popup = False):
        """ Function that displays info popup and log message """

        if self.showPopups.get() or force_popup:
            messagebox.showinfo(title, text)
        self.writeToLog(text + '\n')


# ----------------------- Version Sync Functions -----------------------------



    def syncTags(self):
        """ Function that automatically updates all of the github tags for the install configuration git modules """

        global WITH_PYGITHUB
        if not WITH_PYGITHUB:
            self.showErrorMessage('Error', 'ERROR - PyGithub not found. Install with pip install pygithub, and restart', force_popup=True)
        else:
            user = simpledialog.askstring('Please enter your github username.', 'Username')
            if user is None or len(user) == 0:
                return
            passwd = simpledialog.askstring('Please enter your github password.', 'Password', show='*')
            if passwd is None or len(passwd) == 0:
                return
            if user is not None and passwd is not None:
                if not self.thread.is_alive():
                    self.thread = threading.Thread(target=lambda : self.syncTagsProcess(user, passwd))
                    self.loadingIconThread = threading.Thread(target=self.loadingLoop)
                    self.thread.start()
                    self.loadingIconThread.start()
                else:
                    self.showErrorMessage('Error', 'ERROR - Process thread already running', force_popup=True)


    def syncTagsProcess(self, user, passwd):
        """
        Function meant to synchronize tags for each github based module.
    
        Parameters
        ----------
        user : str
            github username
        passwd : str
            github password
        """
    
        try:
            self.showMessage('Syncing...', 'Please wait while tags are synced - this may take a while...', force_popup=True)
            g = Github(user, passwd)
            for module in self.install_config.get_module_list():
                if module.url_type == 'GIT_URL' and 'github' in module.url and module.version != 'master' and module.name not in self.update_tags_blacklist:
                    account_repo = '{}/{}'.format(module.url.split('/')[-2], module.repository)
                    repo = g.get_repo(account_repo)
                    if repo is not None:
                        tags = repo.get_tags()
                        if tags.totalCount > 0 and module.name != 'EPICS_BASE':
                            tag_found = False
                            for tag in tags:
                                #print('{} - {}'.format(account_repo, tag))
                                if tag.name.startswith('R') and tag.name[1].isdigit():
                                    if tag.name == module.version:
                                        tag_found = True
                                        break
                                    self.writeToLog('Updating {} from version {} to version {}\n'.format(module.name, module.version, tag.name))
                                    module.version = tag.name
                                    tag_found = True
                                    break
                            if not tag_found:
                                for tag in tags:
                                    if tag.name[0].isdigit() and tag.name != module.version:
                                        self.writeToLog('Updating {} from version {} to version {}\n'.format(module.name, module.version, tag.name))
                                        module.version = tags[0].name
                                        break
                                    elif tag.name[0].isdigit():
                                        break
                        elif module.name == 'EPICS_BASE':
                            for tag in tags:
                                if tag.name.startswith('R7'):
                                    if tag.name != module.version:
                                        self.writeToLog('Updating {} from version {} to version {}\n'.format(module.name, module.version, tag.name))
                                        module.version = tag.name
                                        break
            self.updateAllRefs(self.install_config)
            self.updateConfigPanel()
        except:
            self.showErrorMessage('Error', 'ERROR - Invalid Github credentials.', force_popup=True)

# ----------------------- Loading/saving Functions -----------------------------

    def newConfig(self, template_type):
        """
        Will load a new blank config and allow user to edit/save it
        """

        template_filename = 'NEW_CONFIG_ALL'
        if template_type == 'AD':
            template_filename = 'NEW_CONFIG_AD'
        elif template_type == 'Motor':
            template_filename = 'NEW_CONFIG_MOTOR'

        self.writeToLog("Opening new install config dialog...\n")
        temp = simpledialog.askstring('New Install Config', 'Please enter a new desired install location.', parent = self.master)
        if temp is None:
            self.showWarningMessage('Warning', 'Operation cancelled')
        else:
            self.writeToLog("Trying to load new default config with install location {}...\n".format(temp))
            old_config = self.configure_path
            self.configure_path = 'resources'
            self.parser.configure_path = self.configure_path
            loaded_install_config, message = self.parser.parse_install_config(config_filename=template_filename, force_location=temp, allow_illegal=True)
            if message is not None:
                self.valid_install = False
            else:
                self.valid_install = True

            if loaded_install_config is None:
                self.showErrorMessage('Error', 'ERROR - {}.'.format(message), force_popup=True)
                self.parser.configure_path = old_config
                self.configure_path = old_config
            elif not self.valid_install:
                self.showWarningMessage('Warning', 'WARNING - {}.'.format(message), force_popup=True)
                self.updateAllRefs(loaded_install_config)
                self.updateConfigPanel()
            else:
                self.updateAllRefs(loaded_install_config)
                self.updateConfigPanel()
        self.install_loaded = False


    def loadConfig(self):
        """
        Function that opens file dialog asking for configure directory,
        then if it is valid, loads it into an InstallConfiguration object,
        and updates the config panel.
        """

        self.writeToLog("Opening load install config file dialog...\n")
        temp = self.configure_path
        self.configure_path = filedialog.askdirectory(initialdir = '.')
        if len(self.configure_path) == 0:
            self.writeToLog('Operation cancelled.\n')
            self.configure_path = temp
            return
        valid = True
        if not os.path.exists(self.configure_path + "/INSTALL_CONFIG"):
            valid = False
            self.showErrorMessage("Config Error", "ERROR - No INSTALL_CONFIG file found in selected directory.")
        elif not os.path.exists(self.configure_path + "/injectionFiles") or not os.path.exists(self.configure_path + "/macroFiles"):
            self.showWarningMessage('Load Warning', "WARNING - Could not find injection files or macro files.")
        if not valid:
            self.configure_path = temp
            return
        self.writeToLog('Loaded configure directory at {}.\n'.format(self.configure_path))
        self.parser.configure_path = self.configure_path
        self.metacontroller.metadata['configure_path'] = self.configure_path
        self.install_config, message = self.parser.parse_install_config(allow_illegal=True)
        if message is not None:
            self.valid_install = False
            self.showWarningMessage('Warning', 'WARNING - {}.'.format(message), force_popup=True)
        else:
            self.valid_install = True
        if self.install_config is not None:
            self.updateConfigPanel()
        else:
            self.showErrorMessage('Load error', 'Error loading install config... {}'.format(message), force_popup=True)
        self.updateAllRefs(self.install_config)
        self.install_loaded = True
        if self.configure_path == 'configure':
            self.install_loaded = False


    def saveConfig(self):
        """ Function that saves an existing config, or opens save as if it was not previously saved. """

        self.writeToLog("Saving...\n")
        if not self.install_loaded:
            self.saveConfigAs()
        else:
            self.saveConfigAs(force_loc = self.configure_path)


    def saveConfigAs(self, force_loc = None):
        """ Function that opens a save as Dialog for saving currently loaded confguration """

        if self.install_config is None:
            self.showErrorMessage('Save error', 'No loaded install config to save.', force_popup=True)
            return
        
        if force_loc is None:
            dirpath = filedialog.asksaveasfilename(initialdir = '.')
            if len(dirpath) < 1:
                self.writeToLog('Operation Cancelled.\n')
                return
            self.writeToLog('Creating save directory...\n')
        else:
            ans = messagebox.askyesno('Confirm', 'Do you wish to overwrite existing install config with new changes?')
            if ans is None:
                return
            elif not ans:
                return
            dirpath = force_loc
            shutil.rmtree(os.path.join(dirpath, 'injectionFiles'))
            shutil.rmtree(os.path.join(dirpath, 'macroFiles'))
            os.remove(os.path.join(dirpath, 'INSTALL_CONFIG'))

        wrote, message = self.writer.write_install_config(filepath=dirpath)
        if not wrote:
            self.showErrorMessage('Write Error', 'Error saving install config: {}'.format(message), force_popup=True)
        else:
            if self.install_loaded:
                try:
                    shutil.copytree(self.configure_path + '/customBuildScripts', dirpath + '/customBuildScripts')
                except:
                    pass
            self.configure_path = dirpath
            self.install_loaded = True
            self.updateAllRefs(self.install_config)
            self.metacontroller.metadata['configure_path'] = self.configure_path
            self.writeToLog('Saved currently loaded install configuration to {}.\n'.format(dirpath))


    def saveLog(self, saveDir = None):
        """
        Function that saves the contents of the log to a file.

        Parameters
        ----------
        saveDir = None
            if None, opens file dialog to select save location, otherwise, saves in saveDir passed in
        """

        location = saveDir
        if location == None:
            location = filedialog.askdirectory(initialdir = '.')
            if len(location) == 0:
                return
        if location is not None and not os.path.exists(location):
            self.showErrorMessage('Save Error', 'ERROR - Save directory does not exist')
            return
        time = datetime.datetime.now()
        log_file = open(location + "/installSynApps_log_" + time.strftime("%Y_%m_%d_%H_%M_%S"), "w")
        log_file.write(self.log.get('1.0', END))
        log_file.close()


    def selectPackageDestination(self):
        """ Function that asks the user to select an output destination for the created tarball """

        package_output = filedialog.askdirectory(initialdir = '.', title = 'Select output package directory')
        if len(package_output) < 1:
            self.writeToLog('Operation Cancelled.\n')
        else:
            if os.path.exists(package_output):
                self.packager.output_location = package_output
                self.metacontroller.metadata['package_location'] = self.packager.output_location
                self.writeToLog('New package output location set to: {}\n'.format(package_output))
            else:
                self.showErrorMessage('Path Error', 'ERROR - Output path does not exist.')


    def setOutputPackageName(self):
        """ Function that sets the output package name """

        self.writeToLog('Setting output package name...\n')
        package_name = simpledialog.askstring('Enter an output name', 'Output Package Name - typically OS/Distro.')
        if package_name is not None and len(package_name) > 0:
            self.packager.OS = package_name
            self.writeToLog('Done.\n')
        else:
            self.writeToLog('Operation Cancelled.\n')


    def getInitIOCs(self):
        """ Function that gets initIOCs from github. """

        self.writeToLog('Fetching the initIOC script...\n')
        out = subprocess.Popen(['git', 'clone', 'https://github.com/epicsNSLS2-deploy/initIOC'])
        self.writeToLog('Done.\n')


    def launchInitIOCs(self):
        """ Function that launches the GUI version of initIOCs """

        if os.path.exists('./initIOC/initIOCs.py'):
            self.writeToLog('Launching initIOC GUI...\n')
            current = os.getcwd()
            os.chdir('initIOC')
            if platform == 'win32':
                p = subprocess.Popen(['py', 'initIOCs.py', '-g'])
            else:
                p = subprocess.Popen(['./initIOCs.py', '-g'])
            os.chdir(current)
            self.writeToLog('Done.\n')
        else:
            self.showErrorMessage('Error', 'ERROR - Could not find initIOCs. Run the Get initIOCs command first.')


#---------------------------- Editing Functions --------------------------------


    def openEditWindow(self, edit_window_str):
        """ Function that opens up an Edit Config window """

        window = None

        if self.install_config is None:
            self.showErrorMessage('Edit Error', 'Error - no loaded install config', force_popup=True)
            return

        if edit_window_str == 'edit_config':
            window = ViewModel.edit_install_screen.EditConfigGUI(self, self.install_config)
        elif edit_window_str == 'add_module':
            window = ViewModel.add_module_screen.AddModuleGUI(self, self.install_config)
        elif edit_window_str == 'edit_single_mod':
            window = ViewModel.edit_individual_module.EditSingleModuleGUI(self, self.install_config)
        elif edit_window_str == 'edit_injectors':
            window = ViewModel.edit_injector_screen.EditInjectorGUI(self, self.install_config)
        elif edit_window_str == 'edit_build_flags':
            window = ViewModel.edit_macro_screen.EditMacroGUI(self, self.install_config)
        elif edit_window_str == 'add_custom_build_script':
            window = ViewModel.add_custom_build_screen.AddCustomBuildScriptGUI(self, self.install_config)
        elif edit_window_str == 'edit_dependency_script':
            window = ViewModel.edit_dependency_script.EditDependencyScriptGUI(self, self.install_config)
        else:
            self.showErrorMessage('Open Error', 'ERROR - Illegal Edit Window selection')

        if window is None:
            self.showErrorMessage('Open Error', 'ERROR - Unable to open Edit Window')


    def editCoreCount(self):
        """ Function that prompts the user to enter a core count """

        if self.singleCore.get():
            self.showMessage('Message', 'Currently single core mode is enabled, please toggle off to set core count', force_popup=True)
            return

        cores = simpledialog.askinteger('Set Core Count', 'Please enter a core count, or 0 to use all cores', parent = self.master)
        if cores is None:
            self.writeToLog('Operation Cancelled.\n')
            return
        if cores < 0 or cores > 16:
            self.showErrorMessage('Core Count Error', 'ERROR - You have entered an illegal core count, try again.', force_popup=True)
        current_count = self.builder.threads
        new_count = cores
        if self.builder.threads == 0:
            current_count = 'Max core count'
        if cores == 0:
            new_count = 'Max core count'
        self.writeToLog('New core count to use: {}, old core count to use: {}\n'.format(new_count, current_count))
        self.builder.threads = cores


    def setSingleCore(self, *args):
        """ Function that sets the single core option if toggle is pressed """

        self.builder.one_thread = self.singleCore.get()


#--------------------------------- Help/Documentation Functions -----------------------------

    def loadHelp(self):
        """ Simple function that displays a help message """

        helpMessage = "---------------------------------------------\n"
        helpMessage = helpMessage + "Welcome to the installSynApps GUI.\nThis program is designed to help you rapidly build EPICS and synApps.\n\n"
        helpMessage = helpMessage + "To begin, take a look at the panel on the bottom left.\nThis is the currently loaded install configuration.\n"
        helpMessage = helpMessage + "Note the modules listed to be auto-built and their versions.\n\nTo edit these, check the Edit -> Edit Config tab in the menubar.\n"
        helpMessage = helpMessage + "A second window should open and allow you to edit the version\nof each module, as well as to select modules to clone/build/package.\n"
        helpMessage = helpMessage + "This window also allows you to edit the install location.\n\n"
        helpMessage = helpMessage + "Once you have edited the configuration to your specifications,\nyou may press the autorun button on the side, to trigger the build.\n"
        helpMessage = helpMessage + "For more detailed documentation on installSynApps, please\nvisit the documentation online."
        self.showMessage("Help", helpMessage)


    def printDependencies(self):
        """ Prints some information regarding required dependencies for installSynApps """

        self.writeToLog('---------------------------------------------------\n')
        self.writeToLog('Dependencies required for installSynApps:\n')
        self.writeToLog(' * git\n * wget\n * tar\n * make\n * perl\n\n')
        self.writeToLog('Also required are a C/C++ compiler:\n')
        self.writeToLog(' * Linux - gcc/g++ (install with package manager)\n')
        self.writeToLog(' * Windows - MSVC/MSVC++ (install with Visual Studio 2015+)\n\n')
        self.writeToLog('Additional optional python3 modules used, install with pip:\n')
        self.writeToLog(' * distro\n') 
        self.writeToLog(' * pygithub\n\n')
        self.writeToLog('All dependencies must be in system path during build time.\n')
        self.writeToLog('---------------------------------------------------\n')


    def showAbout(self):
        """ Simple function that shows about message """

        self.showMessage('About', self.initLogText())


    def printLoadedConfigInfo(self):
        """ Simple function that prints all info about a loaded configuration """

        if self.install_config is None:
            self.showErrorMessage('Error', 'ERROR - No loaded install config found', force_popup=True)

        self.writeToLog(self.install_config.get_printable_string())


    def depScriptHelp(self):
        """ Function that displays help message for adding dependancy script """

        self.writeToLog('Use the Edit -> Edit Custom Build Scripts menu to add/remove\n')
        self.writeToLog('custom build scripts for each module.\nOn windows they will be saved as')
        self.writeToLog('.bat files, on linux as .sh files,\nand they will be run from the module')
        self.writeToLog(' root directory.\nIf no custom script is found, the module will just be\n')
        self.writeToLog('built with make. If you have a sudo call in your script,\nnote that you')
        self.writeToLog('will need to enter it in the terminal to proceed.\n')


    def printPathInfo(self):
        """ Function that prints a series of paths that are currently loaded. """

        self.writeToLog('-----------------------------------------\n')
        self.writeToLog('Install Location: {}\n'.format(self.install_config.install_location))
        self.writeToLog('Install config directory: {}\n'.format(self.configure_path))
        self.writeToLog('Package output path: {}\n'.format(self.packager.output_location))

#--------------------------------- Build Process Functions ------------------------------------------#
#                                                                                                    #
# Note that each of the build process functions has a wrapper that quickly returns, after starting   #
# thread for running the process itself in the background.                                           #
#----------------------------------------------------------------------------------------------------#


    def initBuildProcess(self, action):
        """Event function that starts a thread on the appropriate build process function

        Parameters
        ----------
        action : str
            a string key on the async action to perform
        """

        if self.generateLogFile.get() and IO.logger._LOG_FILE is None:
            IO.logger.initialize_logger()

        if self.showCommands.get() != IO.logger._PRINT_COMMANDS:
            IO.logger.toggle_command_printing()

        if self.showDebug.get() != IO.logger._DEBUG:
            IO.logger.toggle_debug_logging()

        if self.install_config is None:
            self.showErrorMessage("Start Error", "ERROR - No loaded install config.", force_popup=True)
        elif not self.valid_install:
            self.showErrorMessage("Start Error", "ERROR - Loaded install config not valid.", force_popup=True)
        elif not self.deps_found:
            self.showErrorMessage("Start Error", "ERROR - Missing dependancies detected. See Help -> Required Dependencies.", force_popup=True)
        elif not self.thread.is_alive():
            if action == 'autorun':
                self.thread = threading.Thread(target=self.autorunProcess)
            elif action == 'install-dependencies':
                self.thread = threading.Thread(target=self.installDependenciesProcess)
            elif action == 'clone':
                self.thread = threading.Thread(target=self.cloneConfigProcess)
            elif action == 'update':
                self.thread = threading.Thread(target=self.updateConfigProcess)
            elif action == 'inject':
                self.thread = threading.Thread(target=self.injectFilesProcess)
            elif action == 'build':
                self.thread = threading.Thread(target=self.buildConfigProcess)
            elif action == 'package':
                self.thread = threading.Thread(target=self.packageConfigProcess)
            elif action == 'moveunpack':
                self.thread = threading.Thread(target=self.copyAndUnpackProcess)
            else:
                self.showErrorMessage('Start Error', 'ERROR - Illegal init process call', force_popup=True)
            self.loadingIconThread = threading.Thread(target=self.loadingLoop)
            self.thread.start()
            self.loadingIconThread.start()
        else:
            self.showErrorMessage("Start Error", "ERROR - Process thread is already active.")


    def installDependenciesProcess(self):
        """ Function that calls a dependency script if required """

        self.writeToLog('Running dependency script...\n')
        if platform == 'win32':
            if os.path.exists(self.configure_path + '/dependencyInstall.bat'):
                self.builder.acquire_dependecies(self.configure_path + '/dependencyInstall.bat')
            else:
                self.writeToLog('No dependency script found.\n')
        else:
            if os.path.exists(self.configure_path + '/dependencyInstall.sh'):
                self.builder.acquire_dependecies(self.configure_path + '/dependencyInstall.sh')
            else:
                self.writeToLog('No dependency script found.\n')
        self.writeToLog('Done.\n')


    def cloneConfigProcess(self):
        """ Function that clones all specified modules """

        failed = self.cloner.clone_and_checkout()
        if len(failed) > 0:
            for elem in failed:
                self.writeToLog('Module {} was not cloned successfully.\n'.format(elem))
            return -1
        return 0


    def updateConfigProcess(self):
        """ Function that updates RELEASE and configuration files """
        
        self.writeToLog('----------------------------\n')
        self.writeToLog('Updating all RELEASE and configuration files...')
        self.updater.run_update_config(with_injection=False)
        dep_errors = self.updater.perform_dependency_valid_check()
        for error in dep_errors:
            self.writeToLog('{}\n'.format(error))
        self.writeToLog('Reordering module build order to account for intra-module dependencies...\n')
        self.updater.perform_fix_out_of_order_dependencies()
        self.writeToLog('Done.\n')
        return 0


    def injectFilesProcess(self):
        """ Function that injects settings into configuration files """

        self.writeToLog('Starting file injection process.\n')
        self.updater.perform_injection_updates()
        self.writeToLog('Done.\n')
        return 0


    def buildConfigProcess(self):
        """ Function that builds all specified modules """

        status = 0
        self.writeToLog('-----------------------------------\n')
        self.writeToLog('Beginning build process...\n')
        status, failed = self.builder.build_all()
        if status != 0:
            for module in failed:
                self.writeToLog('Failed building module {}\n'.format(module))
            self.showErrorMessage('Build Error', 'Some modules failed to build.')
        else:
            self.writeToLog('Auto-Build completed successfully.')
        self.writeToLog('Done.\n')
        self.writeToLog('Autogenerating install/uninstall scripts...\n')
        self.autogenerator.initialize_dir()
        self.autogenerator.generate_install()
        self.autogenerator.generate_uninstall()
        self.writeToLog('Autogenerating README file in {}...\n'.format(self.install_config.install_location))
        self.autogenerator.generate_readme()
        self.writeToLog('Done.\n')
        return status


    def autorunProcess(self):
        """ Function that performs all other processes sequentially """

        self.showMessage('Start Autorun', 'Start Autorun - Deps -> Clone -> Checkout -> Update -> Build -> Generate')
        if self.installDep.get():
            self.installDependenciesProcess()
        else:
            self.writeToLog("Auto install dependencies toggled off.\n")

        current_status = self.cloneConfigProcess()
        if current_status < 0:
            self.showErrorMessage('Clone Error', 'ERROR - Cloning error occurred, aborting...')
        else:
            current_status = self.updateConfigProcess()
            if current_status < 0:
                self.showErrorMessage('Update Error', 'ERROR - Update error occurred, aborting...')
            else:
                current_status = self.injectFilesProcess()
                if current_status < 0:
                    self.showErrorMessage('File Inject Error', 'ERROR - Unable to inject files, check Permissions...')
                else:
                    current_status = self.buildConfigProcess()
                    if current_status < 0:
                        self.showErrorMessage('Build Error', 'ERROR - Build error occurred, aborting...')

        self.showMessage('Alert', 'You may wish to save a copy of this log file for later use.')
        self.writeToLog('To generate a bundle from the build, select the Package option.\n')
        self.writeToLog('Autorun completed.\n')


    def packageConfigProcess(self):
        """ Function that packages the specified modules into a tarball """

        self.writeToLog('Starting packaging...\n')
        self.package_output_filename = self.packager.create_bundle_name()
        output = self.packager.create_package(self.package_output_filename, flat_format=self.binariesFlatToggle.get())
        self.package_output_filename = self.package_output_filename + '.tgz'
        self.metacontroller.metadata['package_output_filename'] = self.package_output_filename
        if output != 0:
            self.showErrorMessage('Package Error', 'ERROR - Was unable to package areaDetector successfully. Aborting.', force_popup=True)
        else:
            self.writeToLog('Done.\n')


    def copyAndUnpackProcess(self):
        """ Function that allows user to move their packaged tarball and unpack it. """

        self.writeToLog('Starting move + unpack operation...\n')
        if self.package_output_filename is None:
            self.showErrorMessage('Error', 'ERROR - No tarball package has yet been created.')
        elif not os.path.exists(self.packager.output_location + '/' + self.package_output_filename):
            self.showErrorMessage('Error', 'ERROR - tarball was generated but could not be found. Possibly moved.')
        else:
            target = filedialog.askdirectory(initialdir='.')
            if target is None:
                self.writeToLog('Operation cancelled.\n')
            else:
                self.writeToLog('Moving and unpacking to: {}\n'.format(target))
                shutil.move(os.path.join(self.packager.output_location, self.package_output_filename), os.path.join(target, self.package_output_filename))
                current = os.getcwd()
                os.chdir(target)
                subprocess.call(['tar', '-xzf', self.package_output_filename])
                os.remove(self.package_output_filename)
                os.chdir(current)
                self.writeToLog('Done.')
        


# ---------------- Start the GUI ---------------

root = Tk()
root.title("installSynApps")
try:
    root.iconbitmap('docs/assets/isaIcon.ico')
except:
    pass
root.resizable(False, False)
gui = InstallSynAppsGUI(root)

root.mainloop()
