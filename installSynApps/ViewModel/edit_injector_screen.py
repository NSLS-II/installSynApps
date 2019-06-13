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
    installModuleLines : dict of str to dict
        Dictionary containing links to each module's edit line. Used to apply changes
    install_config : InstallConfiguration
        The loaded install configuration instance
    canvas : Canvas
        object for drawing scrollable pane
    viewFrame : Frame
        Tk frame that contains all widgets
    installTextBox : Text
        Tk text box for editing install location
    applyButton : Button
        button that runs the apply method
    
    Methods
    -------
    writeToPanel(text : str)
        writes to the main edit panel
    readFromPanel(text : str)
        reads from main edit panel
    applyChanges()
        Applies changes to the loaded config
    """

    def __init__(self, root, config_injector):

        self.root = root
        self.master = Toplevel()
        self.master.title('Edit Injector Files')
        self.master.resizable(False, False)
        sizex = 850
        sizey = 700
        posx = 100
        posy = 100
        self.master.wm_geometry("%dx%d+%d+%d" % (sizex, sizey, posx, posy))

        self.smallFont = tkFont.Font(family = "Helvetica", size = 10)
        self.largeFont = tkFont.Font(family = "Helvetica", size = 14)

        self.config_injector = config_injector

        self.viewFrame = Frame(self.master, relief = GROOVE)
        self.viewFrame.pack()

        self.injectorList = []
        for file in self.config_injector.injector_file_contents:
            self.injectorList.append(file)

        self.currentEditVar = StringVar()
        self.currentEditVar.set(self.injectorList[0])

        self.dropdown = OptionMenu(self.viewFrame, self.currentEditVar, *self.injectorList)
        self.dropdown.grid(row = 0, column = 0, columnspan = 2, padx = 5, pady = 5)
        self.currentEditVar.trace('w', self.updateEditPanel)

        self.applyButton = Button(self.viewFrame, text='Apply Changes', command = self.applyChanges).grid(row = 0, column = 5, columnspan = 1)

        self.editPanel = ScrolledText.ScrolledText(self.viewFrame, height = 37, width = 100)
        self.editPanel.grid(row = 1, column = 0, columnspan = 6)

        self.updateEditPanel()

        self.master.mainloop()


    def updateEditPanel(self, *args):
        target_file = self.currentEditVar.get()
        self.editPanel.delete('1.0', END)
        self.editPanel.insert(INSERT, self.config_injector.injector_file_contents[target_file])
        self.editPanel.see(END)


    def applyChanges(self):
        new_contents = self.editPanel.get('1.0', END)
        target = self.currentEditVar.get()
        self.config_injector.injector_file_contents[target] = new_contents

