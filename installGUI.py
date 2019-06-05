#!/usr/bin/python3

#
# A Graphical User Interface for installSynApps
#
# Author: Jakub Wlodek
#

import tkinter as tk
from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
from tkinter import font as tkFont
import tkinter.scrolledtext as ScrolledText

import os
import time
import datetime
import threading

import installSynApps.DataModel.install_config as Config
import installSynApps.IO.config_parser as Parser
import installSynApps.Driver.clone_driver as Cloner
import installSynApps.Driver.update_config_driver as Updater
import installSynApps.Driver.build_driver as Builder
import installSynApps.IO.script_generator as Autogenerator


class InstallSynAppsGUI:

    def __init__(self, master):
        self.master = master
        self.smallFont = tkFont.Font(family = "Helvetica", size = 14)
        self.largeFont = tkFont.Font(family = "Helvetica", size = 18)
        frame = Frame(self.master)
        frame.pack()
        self.msg = "Welcome to installSynApps!"

        self.topLabel       = Label(frame, text = self.msg, width = '50', height = '2', relief = SUNKEN, borderwidth = 1, bg = 'blue', fg = 'white', font = self.smallFont)
        self.topLabel.grid(row = 0, column = 0, padx = 10, pady = 10, columnspan = 2)

        self.loadButton     = Button(frame, font = self.smallFont, text = 'Load Config', command = self.loadConfig, height = '4', width = '30').grid(row = 1, column = 0, padx = 15, pady = 15, columnspan = 1)
        self.cloneButton    = Button(frame, font = self.smallFont, text = 'Clone Modules', command = self.cloneConfig, height = '4', width = '30').grid(row = 1, column = 1, padx = 15, pady = 15, columnspan = 1)
        self.injectButton   = Button(frame, font = self.smallFont, text = 'Inject Files', command = self.injectFiles, height = '4', width = '30').grid(row = 2, column = 0, padx = 15, pady = 15, columnspan = 1)
        self.updateButton   = Button(frame, font = self.smallFont, text = 'Update RELEASE', command = self.updateConfig, height = '4', width = '30').grid(row = 2, column = 1, padx = 15, pady = 15, columnspan = 1)
        self.buildButton    = Button(frame, font = self.smallFont, text = 'Build Modules', command = self.buildConfig, height = '4', width = '30').grid(row = 3, column = 0, padx = 15, pady = 15, columnspan = 1)
        self.autorunButton  = Button(frame, font = self.smallFont, text = 'Autorun', command = self.autorun, height = '4', width = '30').grid(row = 3, column = 1, padx = 15, pady = 15, columnspan = 1)
        self.helpButton     = Button(frame, font = self.smallFont, text = 'Help', command = self.loadHelp, height = '4', width = '30').grid(row = 4, column = 0, padx = 15, pady = 15, columnspan = 1)
        self.saveLog        = Button(frame, font = self.smallFont, text = 'Save Log', command = self.saveLog, height = '4', width = '30').grid(row = 4, column = 1, padx = 15, pady = 15, columnspan = 1)
        
        self.logLabel       = Label(frame, text = 'Log', font = self.smallFont, height = '2').grid(row = 0, column = 2, pady = 0, columnspan = 1)
        self.loadingLabel   = Label(frame, text = 'Process Thread Status: Done.', anchor = W, font = self.smallFont, height = '2')
        self.loadingLabel.grid(row = 0, column = 3, pady = 0, columnspan = 2)

        self.version = 'R2-0'

        self.showPopups = False

        self.configPanel = ScrolledText.ScrolledText(frame)
        self.configPanel.grid(row = 5, column = 0, padx = 15, pady = 15, columnspan = 2, rowspan = 2)

        self.log = ScrolledText.ScrolledText(frame, height = '55', width = '100')
        self.log.grid(row = 1, column = 2, padx = 15, pady = 15, columnspan = 3, rowspan = 6)
        self.writeToLog(self.initLogText())

        self.configure_path = 'configure'

        self.parser = Parser.ConfigParser(self.configure_path)

        self.install_config = self.parser.parse_install_config()
        self.updateConfigPanel()

        self.thread = threading.Thread()
        self.loadingIconThread = threading.Thread(target=self.loadingLoop)

        self.cloner         = Cloner.CloneDriver(self.install_config)
        self.updater        = Updater.UpdateConfigDriver(self.configure_path, self.install_config)
        self.builder        = Builder.BuildDriver(self.install_config)
        self.autogenerator  = Autogenerator.ScriptGenerator(self.install_config)



# -------------------------- Helper functions ----------------------------------


    def loadingLoop(self):
        icons = ['\\', '|', '/', '-']
        icon_counter = 0
        while self.thread.is_alive():
            self.loadingLabel.config(text = 'Process Thread Status: {}'.format(icons[icon_counter]))
            time.sleep(0.25)
            icon_counter = icon_counter + 1
            if icon_counter == len(icons):
                icon_counter = 0
        self.loadingLabel.config(text = 'Process Thread Status: Done.')

    def writeToLog(self, text):
        self.log.insert(INSERT, text)
        self.log.see(END)

    def writeToConfigPanel(self, text):
        self.configPanel.insert(INSERT, text)

    def showErrorMessage(self, title, text):
        if self.showPopups:
            messagebox.showerror(title, text)
        self.writeToLog(text + "\n")


    def showWarningMessage(self, title, text):
        if self.showPopups:
            messagebox.showwarning(title, text)
        self.writeToLog(text + "\n")

    def showMessage(self, title, text):
        if self.showPopups:
            messagebox.showinfo(title, text)
        self.writeToLog(text + '\n')


    def initLogText(self):
        text = "+-----------------------------------------------------------------\n"
        text = text + "+ installSynApps, version: {}                                  +\n".format(self.version)
        text = text +"+ Author: Jakub Wlodek                                           +\n"
        text = text +"+ Copyright (c): Brookhaven National Laboratory 2018-2019        +\n"
        text = text +"+ This software comes with NO warranty!                          +\n"
        text = text +"+-----------------------------------------------------------------\n\n"
        return text


    def updateConfigPanel(self):
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
            self.writeToLog("Done.\n")
        else:
            self.showErrorMessage("Config Error", "ERROR - Could not display Install Configuration: not loaded correctly")


# ----------------------- Button action functions -----------------------------

    def loadConfig(self):
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
            self.showWarningMessage("WARNING - Could not find injection files or macro files.")
        if not valid:
            self.configure_path = temp
            return
        self.writeToLog('Loaded configure directory at {}.\n'.format(self.configure_path))
        self.parser.configure_path = self.configure_path
        self.install_config = self.parser.parse_install_config()
        self.updateConfigPanel()
        self.cloner.install_config = self.install_config
        self.updater.install_config = self.install_config
        self.updater.path_to_configure = self.configure_path
        self.builder.install_config = self.install_config
        self.autogenerator.install_config = self.install_config


    def injectFiles(self):
        if not self.thread.is_alive():
            self.thread = threading.Thread(target=self.injectFilesProcess)
            self.thread.start()
            self.loadingIconThread.start()
        else:
            self.showErrorMessage("Start Error", "ERROR - Process thread is already active.")


    def injectFilesProcess(self):
        self.writeToLog('Starting file injection process.\n')
        self.updater.perform_injection_updates()
        self.writeToLog('Done.\n')


    def updateConfig(self):
        if not self.thread.is_alive():
            self.thread = threading.Thread(target=self.updateConfigProcess)
            self.thread.start()
            self.loadingIconThread.start()
        else:
            self.showErrorMessage("Start Error", "ERROR - Process thread is already active.")


    def updateConfigProcess(self):
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
        self.injectFiles()
        self.showMessage('Update RELEASE', 'Finished update RELEASE + configure process.')
        return 0


    def buildConfig(self):
        if not self.thread.is_alive():
            self.thread = threading.Thread(target=self.buildConfigProcess)
            self.thread.start()
            self.loadingIconThread.start()
        else:
            self.showErrorMessage("Start Error", "ERROR - Process thread is already active.")


    def buildConfigProcess(self):
        status = 0
        self.writeToLog('-----------------------------------\n')
        self.writeToLog('Beginning build process...\n')
        #self.writeToLog('Running dependency script...\n')

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
        status, failedModules = self.builder.build_ad()
        if status < 0:
            self.showErrorMessage('Build Error', 'ERROR - Failed to ADCore or ADSupport, aborting...\nCheck dependencies or INSTALL_CONFIG file.')
            return status
        elif len(failedModules) > 0:
            for module in failedModules:
                self.writeToLog('areaDetector module {} failed to auto-build\n'.format(module.name))
        self.writeToLog('Done.\n')
        self.writeToLog('Autogenerating install/uninstall scripts...\n')
        self.autogenerator.initialize_dir()
        self.autogenerator.generate_install()
        self.autogenerator.generate_uninstall()
        self.writeToLog('Autogenerating README file in {}...\n'.format(self.install_config.install_location))
        self.autogenerator.generate_readme()
        self.writeToLog('Done.\n')
        return status


    def cloneConfig(self):
        if not self.thread.is_alive():
            self.thread = threading.Thread(target=self.cloneConfigProcess)
            self.thread.start()
            self.loadingIconThread.start()
        else:
            self.showErrorMessage("Start Error", "ERROR - Process thread is already active.")


    def cloneConfigProcess(self):
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
            self.showMessage('Success', 'Finished Cloning process')
        else:
            self.showErrorMessage('Load Error', 'ERROR - Install Config is not loaded correctly')
            status = -1

        return status


    def loadHelp(self):
        helpMessage = "---------------------------------------------\n"
        helpMessage = helpMessage + "Welcome to the installSynApps GUI.\nTo use this program, an install configuration is required.\n"
        helpMessage = helpMessage + "An example configuration directory has already been loaded, and can be seen in the ./configure dir.\n"
        helpMessage = helpMessage + "Using this program, you may inject options into EPICS\nand synApps config files, automatically set"
        helpMessage = helpMessage + " build flags,\nclone and checkout all modules and their versions, update RELEASE\nand configuration files,"
        helpMessage = helpMessage + " and auto-build all of EPICS and synApps.\nPlease look over the current config below, and if changes are\n"
        helpMessage = helpMessage + "required, edit the configure/INSTALL_CONFIG file, or load a new configure\ndirectory."
        self.showMessage("Help", helpMessage)



    def autorun(self):
        if not self.thread.is_alive():
            self.thread = threading.Thread(target=self.autorunProcess)
            self.thread.start()
            self.loadingIconThread.start()
        else:
            self.showErrorMessage("Start Error", "ERROR - Process thread is already active.")



    def autorunProcess(self):
        self.showMessage('Start Autorun', 'Start Autorun - Clone -> Checkout -> Update -> Build -> Generate')
        current_status = self.cloneConfigProcess()
        if current_status < 0:
            self.showErrorMessage('Clone Error', 'ERROR - Cloning error occurred, aborting...')
        else:
            current_status = self.updateConfigProcess()
            if current_status < 0:
                self.showErrorMessage('Update Error', 'ERROR - Update error occurred, aborting...')
            else:
                current_status = self.buildConfigProcess()
                if current_status < 0:
                    self.showErrorMessage('Build Error', 'ERROR - Build error occurred, aborting...')

        self.saveLog(saveDir = '.')



    def saveLog(self, saveDir = None):
        location = saveDir
        if location == None:
            location = filedialog.askdirectory(initialdir = '.')
            if len(location) == 0:
                return
        time = datetime.datetime.now()
        log_file = open(location + "/installSynApps_log_" + time.strftime("%Y_%m_%d_%H_%M_%S"), "w")
        log_file.write(self.log.get('1.0', END))
        log_file.close()



# ---------------- Start the GUI ---------------

root = Tk()
root.title("installSynApps")
root.resizable(False, False)
gui = InstallSynAppsGUI(root)

root.mainloop()