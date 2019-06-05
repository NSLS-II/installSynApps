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
        
        self.logLabel       = Label(frame, text = 'Log', font = self.smallFont, height = '2').grid(row = 0, column = 2, pady = 0, columnspan = 3)
        self.version = 'R2-0'

        self.configPanel = ScrolledText.ScrolledText(frame)
        self.configPanel.grid(row = 5, column = 0, padx = 15, pady = 15, columnspan = 2, rowspan = 2)

        self.log = ScrolledText.ScrolledText(frame, height = '55')
        self.log.grid(row = 1, column = 2, padx = 15, pady = 15, columnspan = 3, rowspan = 6)
        self.writeToLog(self.initLogText())

        self.configure_path = 'configure'

        self.parser = Parser.ConfigParser(self.configure_path)

        self.install_config = self.parser.parse_install_config()
        self.updateConfigPanel()


        self.cloner         = Cloner.CloneDriver(self.install_config)
        self.updater        = Updater.UpdateConfigDriver(self.configure_path, self.install_config)
        self.builder        = Builder.BuildDriver(self.install_config)
        self.autogenerator  = Autogenerator.ScriptGenerator(self.install_config)



# -------------------------- Helper functions ----------------------------------


    def writeToLog(self, text):
        self.log.insert(INSERT, text)

    def writeToConfigPanel(self, text):
        self.configPanel.insert(INSERT, text)

    def showErrorMessage(self, intitle, intext):
        messagebox.showerror(title=intitle, text=intext)
        self.writeToLog(text + "\n")


    def showWarningMessage(self, title, text):
        messagebox.showwarning(title=title, text=text)
        self.writeToLog(text + "\n")

    def showMessage(self, title, text):
        messagebox.showinfo(title = title, text = text)
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
        try:
            self.configure_path = filedialog.askdirectory(initialdir = '.')
        except:
            self.writeToLog('Operation cancelled.\n')
        valid = True
        print(self.configure_path)
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
        self.builder.install_config = self.install_config
        self.autogenerator.install_config = self.install_config


    def injectFiles(self):
        self.writeToLog('Starting file injection process.\n')
        self.updater.perform_injection_updates()




    def updateConfig(self):
        print("Unimplemented")


    
    def buildConfig(self):
        print("Unimplemented")


    
    def cloneConfig(self, popup = True):
        self.writeToLog('Beginning module cloning process...\n')
        if self.install_config is not None:
            for module in self.install_config.get_module_list():
                if module.clone == 'YES':
                    self.writeToLog('Cloning module: {}, to location: {}.\n'.format(module.name, module.abs_path))
                    if module.name == 'EPICS_BASE':
                        ret = self.cloner.clone_module(module, recursive=True)
                    else:
                        ret = self.cloner.clone_module(module)
                    
                    if ret == -2:
                        self.showErrorMessage('ERROR - Module {} has an invaild absolute path.'.format(module.name))
                    elif ret == -1:
                        self.showErrorMessage('ERROR - Module {} was not cloned successfully.'.format(module.name))

                    self.writeToLog('Checking out version {}\n'.format(module.version))
                    self.cloner.checkout_module(module)
            if popup:
                self.showMessage('Finished Cloning process')
            else:
                self.writeToLog('Finished Cloning process\n')
        else:
            self.showErrorMessage('ERROR - Install Config is not loaded correctly')

    
    def loadHelp(self):
        print("Unimplemented")


    
    def autorun(self):
        print("Unimplemented")


    def saveLog(self):
        print("Unimplemented")



root = Tk()
root.title("installSynApps")
gui = InstallSynAppsGUI(root)

root.mainloop()