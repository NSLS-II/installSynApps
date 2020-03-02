"""Class for a window that allows writing/editing custom build scripts for individual modules.
"""

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


class EditDependencyScriptGUI:
    """Class representing a window for editing a currently loaded install config in the GUI.

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
        """Constructor for the EditDependencyScriptGUI class
        """

        self.root = root
        self.master = Toplevel()
        self.master.title('Edit Dependency Script')
        self.master.resizable(False, False)
        sizex = 850
        sizey = 700
        posx = 100
        posy = 100
        
        # Select the appropriate extension
        self.extension = '.sh'
        if platform == 'win32':
            self.extension = '.bat'

        self.smallFont = tkFont.Font(family = "Helvetica", size = 10)
        self.largeFont = tkFont.Font(family = "Helvetica", size = 14)

        self.install_config = install_config

        self.viewFrame = Frame(self.master, relief = GROOVE, padx = 10, pady = 10)
        self.viewFrame.pack()

        self.applyButton =      Button(self.viewFrame, text='Save Script',   command=self.applyChanges,      width=10).grid(row=0, column=0, columnspan=1, pady=5)
        self.applyExitButton =  Button(self.viewFrame, text='Exit',          command=self.exit,              width=10).grid(row=0, column=4, columnspan=1, pady=5)
        self.clearButton =      Button(self.viewFrame, text='Delete Script', command=self.deleteBuildScript, width=10).grid(row=0, column=2, columnspan=1, pady=5)

        self.editPanel = ScrolledText.ScrolledText(self.viewFrame, height = 37, width = 100)
        self.editPanel.grid(row = 1, column = 0, columnspan = 5)

        self.loadCustomBuild()

        self.master.mainloop()


    def deleteBuildScript(self):
        """Function that deletes the dependency Script
        """

        if self.root.configure_path is None:
            self.root.showErrorMessage('ERROR', 'ERROR - No configure directory loaded, please save the configuration first.', force_popup=True)
        elif not os.path.exists(os.path.join(self.root.configure_path, 'dependencyInstall' + self.extension)):
            self.root.showErrorMessage('ERROR', 'ERROR - No dependency script has been saved yet for this configuration.', force_popup=True)
        else:
            os.remove(os.path.join(self.root.configure_path, 'dependencyInstall' + self.extension))
            self.root.updateAllRefs(self.install_config)
            self.reloadPanel()
            


    def loadCustomBuild(self, *args):
        """Wrapper that reloads the panel with new info
        """

        self.reloadPanel()


    def reloadPanel(self):
        """Reloads panel based on selection
        """

        self.editPanel.delete('1.0', END)
        self.editPanel.insert(INSERT, '#\n')
        self.editPanel.insert(INSERT, '# Dependency script for building EPICS/synApps\n')
        self.editPanel.insert(INSERT, '# Script will be saved as {}\n'.format('$(CONFIGURE_PATH)/dependencyInstall' + self.extension))
        self.editPanel.insert(INSERT, '# To run the script before build, make sure to toggle install dependencies on.\n')
        self.editPanel.insert(INSERT, '#\n')
        if os.path.exists(os.path.join(self.root.configure_path, 'dependencyInstall' + self.extension)):
            dep_script = open(os.path.join(self.root.configure_path, 'dependencyInstall' + self.extension), 'r')
            script = dep_script.readlines()
            for line in script:
                self.editPanel.insert(INSERT, line)
            dep_script.close()


    def applyChanges(self):
        """Method that reads the edit panel, and writes the contents into a dependencyInstall script.
        
        Script is written to the configuration directory, with the appropriate extension based on current OS.
        """

        temp = self.editPanel.get('1.0', END).splitlines()


        if not self.root.install_loaded:
            self.root.showWarningMessage('Error', 'Currently loaded Install configuration has not been saved. Please save it first to be able to save dependency scripts.')
            return

        build_script_file = os.path.join(self.root.configure_path, 'dependencyInstall' + self.extension)
        if os.path.exists(build_script_file):
            os.remove(build_script_file)

        fp = open(build_script_file, 'w')
        for line in temp:
            if not line.startswith('#'):
                fp.write(line + '\n')
        fp.close()
        self.reloadPanel()
        self.root.updateAllRefs(self.install_config)


    def exit(self):
        """Applies changes and exits window
        """

        self.master.destroy()

