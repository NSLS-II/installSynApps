""" 
Class for a window that allows writing/editing custom build scripts for individual modules.
"""

__author__      = "Jakub Wlodek"

import os
from sys import platform

# Tkinter imports
import tkinter as tk
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
from tkinter import font as tkFont
import tkinter.scrolledtext as ScrolledText

# installSynApps module imports
import installSynApps.DataModel.install_config as Config
import installSynApps.IO.config_parser as Parser
import installSynApps.IO.config_injector as Injector


class AddCustomBuildScriptGUI:
    """
    Class representing a window for editing a currently loaded install config in the GUI.

    Attributes
    ----------
    root : InstallSynAppsGUI
        The top TK instance that opened this window
    master : Toplevel
        The main container Tk object
    viewFrame
        Tk frame that contains all widgets
    dropdown : OptionMenu
        dropdown menu for selecting from injector files
    applyButton : Button
        button that runs the apply method
    editPanel : ScrolledText
        Panel for editing the loaded injector file.
    """

    def __init__(self, root, install_config):
        """
        Constructor for the AddCustomBuildScriptGUI class
        """

        self.root = root
        self.master = Toplevel()
        self.master.title('Edit Custom Build Scripts')
        self.master.resizable(False, False)
        sizex = 850
        sizey = 700
        posx = 100
        posy = 100
        #self.master.wm_geometry("%dx%d+%d+%d" % (sizex, sizey, posx, posy))

        self.smallFont = tkFont.Font(family = "Helvetica", size = 10)
        self.largeFont = tkFont.Font(family = "Helvetica", size = 14)

        self.install_config = install_config

        self.viewFrame = Frame(self.master, relief = GROOVE, padx = 10, pady = 10)
        self.viewFrame.pack()

        self.customBuildModuleVar = StringVar()
        self.customBuildModuleVar.set(self.install_config.get_module_list()[0].name)
        self.legal_names = []
        self.currentModule = self.install_config.get_module_list()[0]

        for module in self.install_config.get_module_list():
            self.legal_names.append(module.name)

        self.module_dropdown = ttk.Combobox(self.viewFrame, textvariable=self.customBuildModuleVar, values=self.legal_names, width='40')
        self.module_dropdown.grid(row = 0, column = 0, columnspan = 3, padx=10, pady=10)
        self.customBuildModuleVar.trace('w', self.loadCustomBuild)

        self.applyButton =      Button(self.viewFrame,  text='Save Build Script',   command = self.applyChanges).grid(row = 0, column = 3, columnspan = 1)
        self.applyExitButton =  Button(self.viewFrame,  text='Exit',                command = self.exit).grid(   row = 0, column = 5, columnspan = 1)
        self.clearButton =      Button(self.viewFrame,  text='Delete Build Script', command = self.deleteBuildScript).grid( row = 0, column = 4, columnspan = 1)

        self.editPanel = ScrolledText.ScrolledText(self.viewFrame, height = 37, width = 100)
        self.editPanel.grid(row = 1, column = 0, columnspan = 6)

        self.loadCustomBuild()

        self.master.mainloop()


    def deleteBuildScript(self):
        """ Function that deletes custom build script associated with module """

        if self.currentModule.custom_build_script_path is None:
            self.root.showErrorMessage('ERROR', 'ERROR - No build script associated with this module.', force_popup=True)
        else:
            os.remove(self.currentModule.custom_build_script_path)
            self.currentModule.custom_build_script_path = None
            self.root.updateAllRefs(self.install_config)
            self.reloadPanel(ifsame=True)
            


    def loadCustomBuild(self, *args):
        """ Wrapper that reloads the panel based on selection """

        self.reloadPanel()


    def reloadPanel(self, ifsame=False):
        """
        reloads Panel based on selection
        """

        found = False
        for module in self.install_config.get_module_list():
            if module.name == self.customBuildModuleVar.get():
                self.currentModule = module
                found = True

        if not found and not ifsame:
            return

        self.editPanel.delete('1.0', END)
        self.editPanel.insert(INSERT, '#\n')
        self.editPanel.insert(INSERT, '# Custom Build script for module {}\n'.format(self.currentModule.name))
        if self.currentModule.custom_build_script_path is None:
            self.editPanel.insert(INSERT, '# Currently, module {} will not apply a custom build script.\n'.format(self.currentModule.name))
        else:
            self.editPanel.insert(INSERT, '# Building {} will use script from {}/{}\n'.format(self.currentModule.name, '$CONFIGURE/customBuildScripts', os.path.basename(self.currentModule.custom_build_script_path)))
        self.editPanel.insert(INSERT, '#\n')
        if self.currentModule.custom_build_script_path is not None:
            custom_build = open(self.currentModule.custom_build_script_path, 'r')
            script = custom_build.readlines()
            for line in script:
                self.editPanel.insert(INSERT, line)
            custom_build.close()


    def applyChanges(self):
        """
        Method that reads the edit panel, and writes a custom build script with $MODULE_NAME as the name
        and an OS appropriate extension
        """

        temp = self.editPanel.get('1.0', END).splitlines()
        if platform == 'win32':
            script_ending = '.bat'
        else:
            script_ending = '.sh'

        if not self.root.install_loaded:
            self.root.showWarningMessage('Error', 'Currently loaded Install configuration has not been saved. Please save it first to be able to save build scripts.')
            return
        build_script_folder = os.path.join(self.root.configure_path, 'customBuildScripts')
        if not os.path.exists(build_script_folder):
            os.mkdir(build_script_folder)
        build_script_file = os.path.join(build_script_folder, '{}{}'.format(self.currentModule.name, script_ending))
        if os.path.exists(build_script_file):
            os.remove(build_script_file)
        for module in self.install_config.get_module_list():
            if module.name == self.currentModule.name:
                module.custom_build_script_path = build_script_file
        fp = open(build_script_file, 'w')
        for line in temp:
            if not line.startswith('#'):
                fp.write(line + '\n')
        fp.close()
        self.reloadPanel(ifsame=True)
        self.root.updateAllRefs(self.install_config)
        self.root.updateConfigPanel()


    def exit(self):
        """ applies changes and exits window """

        self.master.destroy()

