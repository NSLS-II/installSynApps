""" 
Class for a window that allows editing of loaded macros.
"""

__author__      = "Jakub Wlodek"

# Tkinter imports
import tkinter as tk
from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
from tkinter import font as tkFont
import tkinter.scrolledtext as ScrolledText

# installSynApps module imports
import installSynApps.DataModel.install_config as Config
import installSynApps.IO.config_parser as Parser
import installSynApps.IO.config_injector as Injector


class EditMacroGUI:
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
    
    Methods
    -------
    updateEditPanel(*args)
        updates the main edit panel based on current selection
    applyChanges()
        Applies changes to the loaded config
    applyAndExit()
        Applies changes and exits the window
    """

    def __init__(self, root, install_config):
        """
        Constructor for the EditMacroGUI class
        """

        self.root = root
        self.master = Toplevel()
        self.master.title('Edit Build Flags')
        self.master.resizable(False, False)
        sizex = 500
        sizey = 400
        posx = 100
        posy = 100
        #self.master.wm_geometry("%dx%d+%d+%d" % (sizex, sizey, posx, posy))

        self.smallFont = tkFont.Font(family = "Helvetica", size = 10)
        self.largeFont = tkFont.Font(family = "Helvetica", size = 14)

        self.install_config = install_config

        self.viewFrame = Frame(self.master, relief = GROOVE, padx = 10, pady = 10)
        self.viewFrame.pack()

        self.applyButton = Button(self.viewFrame, text='Apply Changes', command = self.applyChanges, width=12).grid(row = 0, column = 0, columnspan = 1, padx = 5, pady = 5)
        self.applyButton = Button(self.viewFrame, text='Apply and Exit', command = self.applyChangesExit, width=12).grid(row = 0, column = 1, columnspan = 1, padx = 5, pady = 5)
        self.refreshButton = Button(self.viewFrame, text='Reload', command = self.initEditPanel, width=12).grid(row = 0, column = 2, columnspan = 1, padx = 5, pady = 5)
        self.editPanel = ScrolledText.ScrolledText(self.viewFrame, height = 20, width = 55)
        self.editPanel.grid(row = 1, column = 0, columnspan = 3)

        self.initEditPanel()

        self.master.mainloop()


    def initEditPanel(self):
        """
        Function that initializes the edit panel text the currently loaded one.
        """

        self.editPanel.delete('1.0', END)
        self.editPanel.insert(INSERT, '# Below are currently loaded macros.\n# Please keep new macros in the format MACRO=VALUE.\n\n')
        for pair in self.install_config.build_flags:
            self.editPanel.insert(INSERT, '{}={}\n'.format(pair[0], pair[1]))
        
        self.editPanel.see(END)


    def applyChanges(self):
        """
        Method that reads the edit panel, and sets the macro file contents to whatever the user
        wrote. Note that there are no checks to see if the edited macros will be valid
        """

        new_list = []
        new_contents = self.editPanel.get('1.0', END)
        lines = new_contents.split('\n')
        for line in lines:
            if '=' in line and not line.startswith('#'):
                pair = line.strip().split('=')
                new_list.append(pair)

        self.install_config.build_flags = new_list
        self.root.writeToLog('Applied updated macro replace list.\n')


    def applyChangesExit(self):
        """ Applies changes and exits """

        self.applyChanges()
        self.master.destroy()

