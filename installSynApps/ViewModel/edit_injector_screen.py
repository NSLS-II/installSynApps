""" 
Class for a window that allows editing of a loaded injector files.
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
from tkinter import font as tkFont
import tkinter.scrolledtext as ScrolledText

# installSynApps module imports
import installSynApps.DataModel.install_config as Config
import installSynApps.IO.config_parser as Parser
import installSynApps.IO.config_injector as Injector


class EditInjectorGUI:
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
    """

    def __init__(self, root, install_config):
        """
        Constructor for the EditInjectoGUI class
        """

        self.root = root
        self.master = Toplevel()
        self.master.title('Edit Injector Files')
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

        self.injectorList = []
        for file in self.install_config.injector_files:
            self.injectorList.append(file.name)

        self.currentEditVar = StringVar()
        self.currentEditVar.set(self.injectorList[0])

        self.dropdown = OptionMenu(self.viewFrame, self.currentEditVar, *self.injectorList)
        self.dropdown.grid(row = 0, column = 0, columnspan = 2, padx = 5, pady = 5)
        self.currentEditVar.trace('w', self.updateEditPanel)

        self.applyButton = Button(self.viewFrame, text='Apply Changes', command = self.applyChanges).grid(row = 0, column = 3, columnspan = 1)
        self.applyExitButton = Button(self.viewFrame, text='Apply and Exit', command = self.applyExit).grid(row = 0, column = 4, columnspan = 1)
        self.reloadButton = Button(self.viewFrame, text='Reload', command = self.reloadPanel).grid(row = 0, column = 5, columnspan = 1)

        self.editPanel = ScrolledText.ScrolledText(self.viewFrame, height = 37, width = 100)
        self.editPanel.grid(row = 1, column = 0, columnspan = 6)

        self.updateEditPanel()

        self.master.mainloop()


    def updateEditPanel(self, *args):
        """ Wrapper that reloads the panel based on selection """

        self.reloadPanel()


    def reloadPanel(self):
        """
        reloads Panel based on selection
        """

        target_file = self.currentEditVar.get()
        contents = ''
        link = ''
        for file in self.install_config.injector_files:
            if file.name == target_file:
                contents = file.contents
                link = file.target
        self.editPanel.delete('1.0', END)
        self.editPanel.insert(INSERT, '#\n')
        self.editPanel.insert(INSERT, '# The below contents will be injected into:\n')
        self.editPanel.insert(INSERT, '# {}\n'.format(link))
        self.editPanel.insert(INSERT, '#\n\n')
        self.editPanel.insert(INSERT, contents)


    def applyChanges(self):
        """
        Method that reads the edit panel, and sets the injector contents to whatever the user
        wrote. Note that there are no checks to see if the injection will be valid.
        """

        temp = self.editPanel.get('1.0', END).splitlines()
        new_contents = ''
        for line in temp:
            if not line.startswith('#'):
                new_contents = new_contents + line + '\n'
        target = self.currentEditVar.get()
        for file in self.install_config.injector_files:
            if file.name == target:
                file.contents = new_contents
        self.root.writeToLog('Applied updated injector file contents.\n')


    def applyExit(self):
        """ applies changes and exits window """

        self.applyChanges()
        self.master.destroy()

