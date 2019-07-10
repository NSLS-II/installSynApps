#!/usr/bin/python3

""" GUI class for the installSynApps module

This GUI solution allows for much easier use of the installSynApps module 
to clone, update, and build the EPICS and synApps software stack.
"""

__author__      = "Jakub Wlodek"
__copyright__   = "Copyright June 2019, Brookhaven Science Associates"
__credits__     = ["Jakub Wlodek", "Kazimierz Gofron"]
__license__     = "GPL"
__version__     = "R2-0"
__maintainer__  = "Jakub Wlodek"
__status__      = "Production"


# Tkinter imports
import tkinter as tk
from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
from tkinter import simpledialog
from tkinter import font as tkFont
import tkinter.scrolledtext as ScrolledText

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

        # version and popups toggle
        self.showPopups = tk.BooleanVar()
        self.showPopups.set(False)
        self.installDep = tk.BooleanVar()
        self.installDep.set(False)
        self.singleCore = tk.BooleanVar()
        self.singleCore.set(False)

        menubar = Menu(self.master)

        # File menu
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label='New',       command=self.newConfig)
        filemenu.add_command(label='Open',      command=self.loadConfig)
        filemenu.add_command(label='Save',      command=self.saveConfig)
        filemenu.add_command(label='Save As',   command=self.saveConfigAs)
        filemenu.add_command(label='Exit',      command=self.close_cleanup)
        menubar.add_cascade(label='File', menu=filemenu)

        # Edit Menu
        editmenu = Menu(menubar, tearoff=0)
        editmenu.add_command(label='Edit Config',               command=lambda : self.openEditWindow('edit_config'))
        editmenu.add_command(label='Add New Module',            command=lambda : self.openEditWindow('add_module'))
        editmenu.add_command(label='Edit Individual Module',    command=lambda : self.openEditWindow('edit_single_mod'))
        editmenu.add_command(label='Edit Injection Files',      command=lambda : self.openEditWindow('edit_injectors'))
        editmenu.add_command(label='Edit Build Flags',          command=lambda : self.openEditWindow('edit_build_flags'))
        editmenu.add_command(label='Edit Make Core Count',           command=self.editCoreCount)
        editmenu.add_checkbutton(label='Toggle Popups',         onvalue=True, offvalue=False, variable=self.showPopups)
        editmenu.add_checkbutton(label='Toggle Single Core',    onvalue=True, offvalue=False, variable=self.singleCore)
        self.singleCore.trace('w', self.setSingleCore)
        menubar.add_cascade(label='Edit', menu=editmenu)

        # Debug Menu
        debugmenu = Menu(menubar, tearoff = 0)
        debugmenu.add_command(label='Print Loaded Config Info', command=self.printLoadedConfigInfo)
        debugmenu.add_command(label='Clear Log',                command=self.resetLog)
        debugmenu.add_command(label='Recheck Dependancies',     command=self.recheckDeps)
        menubar.add_cascade(label='Debug', menu=debugmenu)

        # Build Menu
        buildmenu = Menu(menubar, tearoff=0)
        buildmenu.add_command(label='Autorun',              command=lambda : self.initBuildProcess('autorun'))
        buildmenu.add_command(label='Clone Modules',        command=lambda : self.initBuildProcess('clone'))
        buildmenu.add_command(label='Update Config Files',  command=lambda : self.initBuildProcess('update'))
        buildmenu.add_command(label='Inject into Files',    command=lambda : self.initBuildProcess('inject'))
        buildmenu.add_command(label='Build Modules',        command=lambda : self.initBuildProcess('build'))
        buildmenu.add_checkbutton(label='Toggle Install Dependencies', onvalue=True, offvalue=False, variable=self.installDep)
        menubar.add_cascade(label='Build', menu=buildmenu)

        # Package Menu
        packagemenu = Menu(menubar, tearoff=0)
        packagemenu.add_command(label='Select Package Destination', command=self.selectPackageDestination)
        packagemenu.add_command(label='Package Modules',            command=lambda : self.initBuildProcess('package'))
        menubar.add_cascade(label='Package', menu=packagemenu)

        # Help Menu
        helpmenu = Menu(menubar, tearoff=0)
        helpmenu.add_command(label='Quick Help',                command=self.loadHelp)
        helpmenu.add_command(label='Dependency Script Help',    command=self.depScriptHelp)
        helpmenu.add_command(label='Online Documentation',      command=self.openOnlineDocs)
        helpmenu.add_command(label='About',                     command=self.showAbout)
        menubar.add_cascade(label='Help', menu=helpmenu)

        self.master.config(menu=menubar)

        self.msg = "Welcome to installSynApps!"

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
        self.logLabel       = Label(frame, text = 'Log', font = self.smallFont, height = '1').grid(row = 0, column = 6, pady = 0, columnspan = 1)
        self.loadingLabel   = Label(frame, text = 'Process Thread Status: Done.', anchor = W, font = self.smallFont, height = '1')
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
        self.valid_install = False
        self.deps_found = True

        self.metacontroller = ViewModel.meta_pref_control.MetaDataController()
        if 'configure_path' in self.metacontroller.metadata.keys():
            self.configure_path = self.metacontroller.metadata['configure_path']
            self.writeToLog('Loading configure directory saved in location {}\n'.format(self.configure_path))

        self.metacontroller.metadata['isa_version'] = __version__
        self.metacontroller.metadata['platform'] = platform
        self.metacontroller.metadata['last_used'] = '{}'.format(datetime.datetime.now())

        # installSynApps options, initialzie + read default configure files
        self.parser = IO.config_parser.ConfigParser(self.configure_path)

        self.install_config, message = self.parser.parse_install_config(allow_illegal=True)
        self.install_loaded = False
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

        text = "+-----------------------------------------------------------------\n"
        text = text + "+ installSynApps, version: {}                                  +\n".format(__version__)
        text = text +"+ Author: Jakub Wlodek                                           +\n"
        text = text +"+ Copyright (c): Brookhaven National Laboratory 2018-2019        +\n"
        text = text +"+ This software comes with NO warranty!                          +\n"
        text = text +"+-----------------------------------------------------------------\n\n"
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
            self.writeToConfigPanel("# Currently Loaded Install Configuration:\n\n")
            self.writeToConfigPanel("Install Location: {}\n\n".format(self.install_config.install_location))
            self.writeToConfigPanel("Modules to auto-build:\n")
            for module in self.install_config.get_module_list():
                if module.build == "YES":
                    self.writeToConfigPanel("Name: {},\t\t\tVersion: {}\n".format(module.name, module.version))
            self.writeToConfigPanel("\nModules to clone but not build:\n")
            for module in self.install_config.get_module_list():
                if module.build == "NO" and module.clone == "YES":
                    self.writeToConfigPanel("Name: {},\t\t\t Version: {}\n".format(module.name, module.version))

            self.writeToConfigPanel("\nModules to package:\n")
            for module in self.install_config.get_module_list():
                if module.package == "YES":
                    self.writeToConfigPanel("Name: {},\t\t\t Version: {}\n".format(module.name, module.version))
            self.writeToLog("Done.\n")

            if os.path.exists(self.configure_path + "/macroFiles") and os.path.exists(self.configure_path + "/injectionFiles"):
                self.writeToConfigPanel("\nAdditional build flags will be taken from:\n")
                for mfile in os.listdir(self.configure_path + "/macroFiles"):
                    self.writeToConfigPanel(mfile + "\n")
                self.writeToConfigPanel("\nFile injections will be performed on the following:\n")
                for ifile in self.install_config.injector_files:
                    self.writeToConfigPanel("{} -> {}\n".format(ifile.name, ifile.target))
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
            #self.showErrorMessage('Error', 'ERROR- Could not find {} in system path.'.format(missing), force_popup=True)
            self.deps_found = False
        else:
            self.deps_found = True
        self.writeToLog('Done.\n')


    def close_cleanup(self):
        """ Function that asks user if he/she wants to close, and cleans up threads """

        if self.thread.is_alive():
            self.showWarningMessage('Warning', 'Qutting while process is running may result in invalid installation!', force_popup=True)
        if messagebox.askokcancel('Quit', 'Do you want to quit?'):
            self.master.destroy()
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


# ----------------------- Loading/saving Functions -----------------------------


    def newConfig(self):
        """
        Will load a new blank config and allow user to edit/save it
        """

        self.writeToLog("Opening new install config dialog...\n")
        temp = simpledialog.askstring('New Install Config', 'Please enter a new desired install location.', parent = self.master)
        if temp is None:
            self.showWarningMessage('Warning', 'Operation cancelled')
        else:
            self.writeToLog("Trying to load new default config with install location {}...\n".format(temp))
            old_config = self.configure_path
            self.configure_path = 'resources'
            self.parser.configure_path = self.configure_path
            loaded_install_config, message = self.parser.parse_install_config(config_filename='NEW_CONFIG', force_location=temp, allow_illegal=True)
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
            self.writeToLog('Creating save directory...\n')
        else:
            ans = messagebox.askyesno('Confirm', 'Do you wish to overwrite existing install config with new changes?')
            if ans is None:
                return
            elif not ans:
                return
            dirpath = force_loc
            shutil.rmtree(dirpath)

        wrote, message = self.writer.write_install_config(filepath=dirpath)
        if not wrote:
            self.showErrorMessage('Write Error', 'Error saving install config: {}'.format(message), force_popup=True)
        else:
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
        if saveDir is not None and not os.path.exists(saveDir):
            self.showErrorMessage('Save Error', 'ERROR - Save directory does not exist')
            return
        time = datetime.datetime.now()
        log_file = open(location + "/installSynApps_log_" + time.strftime("%Y_%m_%d_%H_%M_%S"), "w")
        log_file.write(self.log.get('1.0', END))
        log_file.close()


    def selectPackageDestination(self):
        """ Function that asks the user to select an output destination for the created tarball """

        package_output = filedialog.askdirectory(initialdir = '.', title = 'Select output package directory', mustexist = True)
        if package_output is None:
            self.writeToLog('Operation Cancelled.\n')
        else:
            if os.path.exists(package_output):
                self.packager.output_location = package_output
                self.metacontroller.metadata['package_location'] = output_location


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


    def openOnlineDocs(self):
        """ Function that uses the webbrowser python module to open up the installSynApps online docs """

        webbrowser.open("https://epicsNSLS2-deploy.github.io/installSynApps", new=2)



    def loadHelp(self):
        """ Simple function that displays a help message """

        helpMessage = "---------------------------------------------\n"
        helpMessage = helpMessage + "Welcome to the installSynApps GUI.\nTo use this program, an install configuration is required.\n"
        helpMessage = helpMessage + "An example configuration directory has already been loaded, and can be seen in the ./configure dir.\n"
        helpMessage = helpMessage + "Using this program, you may inject options into EPICS\nand synApps config files, automatically set"
        helpMessage = helpMessage + " build flags,\nclone and checkout all modules and their versions, update RELEASE\nand configuration files,"
        helpMessage = helpMessage + " and auto-build all of EPICS and synApps.\nPlease look over the current config below, and if changes are\n"
        helpMessage = helpMessage + "required, edit it via the `Edit` tab, or load a new configure\ndirectory."
        self.showMessage("Help", helpMessage)


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

        self.writeToLog('When dependency install is enabled, installSynApps will attempt\nto run a dependency script')
        self.writeToLog('in the configure directory,\ncalled dependencyInstall.sh on Linux, and dependencyInstall.bat\non win32.')
        self.writeToLog('To add a script, simply write a shell/batch script,\nand place it in the configure directory.\n')

#--------------------------------- Build Process Functions ------------------------------------------#
#                                                                                                    #
# Note that each of the build process functions has a wrapper that quickly returns, after starting   #
# thread for running the process itself in the background.                                           #
#----------------------------------------------------------------------------------------------------#


    def initBuildProcess(self, action):
        """
        Event function that starts a thread on the appropriate build process function
        """

        if self.install_config is None:
            self.showErrorMessage("Start Error", "ERROR - No loaded install config.", force_popup=True)
        elif not self.valid_install:
            self.showErrorMessage("Start Error", "ERROR - Loaded install config not valid.", force_popup=True)
        elif not self.deps_found:
            self.showErrorMessage("Start Error", "ERROR - Missing dependancies detected. Run Debug -> Recheck.", force_popup=True)
        elif not self.thread.is_alive():
            if action == 'autorun':
                self.thread = threading.Thread(target=self.autorunProcess)
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
            else:
                self.showErrorMessage('Start Error', 'ERROR - Illegal init process call', force_popup=True)
            self.loadingIconThread = threading.Thread(target=self.loadingLoop)
            self.thread.start()
            self.loadingIconThread.start()
        else:
            self.showErrorMessage("Start Error", "ERROR - Process thread is already active.")


    def cloneConfigProcess(self):
        """ Function that clones all specified modules """

        status = 0
        self.writeToLog('-----------------------------------\n')
        self.writeToLog('Beginning module cloning process...\n')
        if self.install_config is not None:
            for module in self.install_config.get_module_list():
                if module.clone == 'YES':
                    self.writeToLog('Cloning module: {}, to location: {}.\n'.format(module.name, module.rel_path))
                    if module.name in self.cloner.recursive_modules:
                        ret = self.cloner.clone_module(module, recursive=True)
                    else:
                        ret = self.cloner.clone_module(module)
                    
                    if ret == -2:
                        self.showErrorMessage('Clone Error' 'ERROR - Module {} has an invaild absolute path.'.format(module.name))
                        status = -1
                    elif ret == -1:
                        self.showErrorMessage('Clone Error', 'ERROR - Module {} was not cloned successfully.'.format(module.name))
                        status = -1

                    self.writeToLog('Checking out version {}\n'.format(module.version))
                    self.cloner.checkout_module(module)
            self.writeToLog('Cleaning up clone directories\n')
            self.cloner.cleanup_modules()
            self.showMessage('Success', 'Finished Cloning process')
        else:
            self.showErrorMessage('Load Error', 'ERROR - Install Config is not loaded correctly')
            status = -1

        return status


    def updateConfigProcess(self):
        """ Function that updates RELEASE and configuration files """
        
        self.writeToLog('-----------------------------------\n')
        self.writeToLog('Fixing any modules that require specific RELEASE files...\n')
        for target in self.updater.fix_release_list:
            self.writeToLog('Fixing {} RELEASE file\n'.format(target))
            self.updater.fix_target_release(target)
        self.writeToLog('Updating all macros and paths for areaDetector...\n')
        self.updater.update_ad_macros()
        self.writeToLog('Updating all paths in support...\n')
        self.updater.update_support_macros()
        self.writeToLog('Adding any additional support paths...\n')
        self.updater.add_missing_support_macros()
        self.writeToLog('Commenting non-auto-build paths...\n')
        self.updater.comment_non_build_macros()
        #self.injectFilesProcess()
        self.showMessage('Update RELEASE', 'Finished update RELEASE + configure process.')
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
        if not platform == "win32" and self.installDep.get():
            self.writeToLog('Running dependency script...\n')
            if os.path.exists(self.configure_path + '/dependencyInstall.sh'):
                self.writeToLog('Please enter your sudo password into the terminal...\n')
                self.builder.acquire_dependecies(self.configure_path + '/dependencyInstall.sh')
                self.writeToLog('Dependencies have been installed.\n')
            else:
                self.writeToLog('No dependency script found.\n')
        elif platform == "win32" and self.installDep.get():
            if os.path.exists(self.configure_path + '/dependencyInstall.bat'):
                self.builder.acquire_dependecies(self.configure_path + '/dependencyInstall.bat')
                self.writeToLog('Dependencies have been installed.\n')
            else:
                self.writeToLog('No dependency script found.\n')
        else:
            self.writeToLog("Auto install dependencies toggled off.\n")
        self.writeToLog('Compiling EPICS base at location {}...\n'.format(self.install_config.base_path))
        status = self.builder.build_base()
        if status < 0:
            self.showErrorMessage('Build Error', 'ERROR - Failed to build base, aborting...\nCheck dependencies or INSTALL_CONFIG file.')
            return status
        self.writeToLog('Done.\n')
        self.writeToLog('Compiling EPICS support modules at location {}...\n'.format(self.install_config.support_path))
        status = self.builder.build_support()
        if status < 0:
            self.showErrorMessage('Build Error', 'ERROR - Failed to build support modules, aborting...\nCheck dependencies or INSTALL_CONFIG file.')
            return status
        self.writeToLog('Done.\n')
        self.writeToLog('Compiling selected areaDetector modules at location {}...\n'.format(self.install_config.ad_path))
        self.writeToLog('Compiling ADSupport...\n')
        status = self.builder.build_ad_support()
        if status != 0:
            self.showErrorMessage('Build Error', 'ERROR - Failed to build ADSupport, aborting...\nCheck dependencies or INSTALL_CONFIG file.')
            return status
        self.writeToLog('Compiling ADCore...\n')
        status = self.builder.build_ad_core()
        if status != 0:
            self.showErrorMessage('Build Error', 'ERROR - Failed to build ADCore, aborting...\nCheck dependencies or INSTALL_CONFIG file.')
            return status
        for module in self.install_config.get_module_list():
            if module.build == 'YES':
                status, was_ad = self.builder.build_ad_module(module)
                if was_ad and status == 0:
                    self.writeToLog("Built AD module {}\n".format(module.name))
                elif was_ad and status != 0:
                    self.writeToLog("Failed to build AD module {}\n".format(module.name))
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

        self.showMessage('Start Autorun', 'Start Autorun - Clone -> Checkout -> Update -> Build -> Generate')
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
        self.writeToLog('Autorun completed.')


    def packageConfigProcess(self):
        """ Function that packages the specified modules into a tarball """

        self.writeToLog('Starting packaging...\n')
        output_filename = self.packager.create_bundle_name()
        self.writeToLog('Tarring...\n')
        output = self.packager.create_package(output_filename)
        if output < 0:
            self.showErrorMessage('Package Error', 'ERROR - Was unable to package areaDetector successfully. Aborting.', force_popup=True)
        else:
            self.writeToLog('Package saved to {}\n'.format(self.packager.output_location))
            self.writeToLog('Bundle Name: {}\n'.format(output_filename))
            self.writeToLog('Done. Completed in {} seconds.\n'.format(output))


# ---------------- Start the GUI ---------------

root = Tk()
root.title("installSynApps")
root.resizable(False, False)
gui = InstallSynAppsGUI(root)

root.mainloop()
