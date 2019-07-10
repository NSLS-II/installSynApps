""" 
Class for a window that allows editing of a loaded install config.
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

# Helper python modules
import os

# installSynApps module imports
import installSynApps.DataModel.install_config as Config


class EditConfigGUI:
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
    readInstallModules()
        Function that parses an InstallConfiguration Object into a series of Tk widgets
    scrollFunction(event)
        Function used to achieve scrolling in the canvas
    applyChanges()
        converts the widget information back into install configuration information, and then applies it to the loaded info
    """


    def __init__(self, root, install_config):
        """
        Constructor for the EditConfigGUI class

        Parameters
        ----------
        root : InstallSynAppsGUI
            The root opening window. Used to refresh references on apply
        install_config : InstallConfiguration
            The currently loaded install configuration
        """

        self.root = root
        self.master = Toplevel()
        self.master.title('Edit Install Config')
        self.master.resizable(False, False)
        sizex = 875
        sizey = 600
        self.installModuleLines = {}
        self.individualEditButtons = {}
        self.master.wm_geometry("%dx%d" % (sizex, sizey))

        self.smallFont = tkFont.Font(family = "Helvetica", size = 10)
        self.largeFont = tkFont.Font(family = "Helvetica", size = 14)

        self.install_config = install_config

        topFrame = Frame(self.master, width = 100, height = 100)
        topFrame.place(x=10, y= 10)

        self.canvas = Canvas(topFrame)

        self.viewFrame = Frame(self.canvas)
        scrollbar = Scrollbar(topFrame, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side='right', fill='y')
        self.canvas.pack(side='left')
        self.canvas.create_window((0,0), window=self.viewFrame, anchor='nw')
        self.viewFrame.bind('<Configure>', self.scrollFunction)
        Label(self.viewFrame, text='    Edit Loaded Install Configuration', anchor=W, justify=LEFT).grid(row = 0, column = 0, columnspan = 1, pady = 5)
        self.applyButton = Button(self.viewFrame, text = 'Apply Changes', justify = LEFT, command=self.applyChanges).grid(row = 0, column = 3)
        self.applyExitButton = Button(self.viewFrame, text = 'Apply and Exit', justify = LEFT, command=self.applyExit).grid(row = 0, column = 5)
        temp = ''
        for i in range(0, 150):
            temp = temp + '-'
        self.splitter = Label(self.viewFrame, text=temp)
        self.splitter.grid(row = 1, column = 0, columnspan = 6)

        Label(self.viewFrame, text='Install Location: ').grid(row=2, column = 0)
        self.installTextBox = Text(self.viewFrame, height = 1, width = 32, padx = 3, pady = 3)
        self.installTextBox.grid(row=2, column = 1, columnspan = 2)
        self.installTextBox.insert(INSERT, self.install_config.install_location)
        self.readInstallModules()

        self.master.mainloop()


    def readInstallModules(self):
        """ Function that parses the install configuration into Tk widgets """

        counter = 3
        for module in self.install_config.get_module_list():
            self.installModuleLines[module.name] = {}
            modLabel = Label(self.viewFrame, text=module.name).grid(row=counter, column = 0, columnspan = 1)
            self.installModuleLines[module.name]['Label'] = modLabel
            vTextBox = Text(self.viewFrame, height = 1, width = 32, padx = 3, pady = 3)
            vTextBox.grid(row=counter, column = 1, columnspan = 2)
            vTextBox.insert(INSERT, module.version)
            self.installModuleLines[module.name]['versionTextBox'] = vTextBox
            self.installModuleLines[module.name]['cloneVar'] = BooleanVar()
            if module.clone == 'YES':
                self.installModuleLines[module.name]['cloneVar'].set(True)
            self.installModuleLines[module.name]['cloneCheck'] = Checkbutton(self.viewFrame, text='Clone', onvalue = True, offvalue = False, variable = self.installModuleLines[module.name]['cloneVar'])
            self.installModuleLines[module.name]['cloneCheck'].grid(row = counter, column = 3, columnspan = 1)
            self.installModuleLines[module.name]['buildVar'] = BooleanVar()
            if module.build == 'YES':
                self.installModuleLines[module.name]['buildVar'].set(True)
            self.installModuleLines[module.name]['buildCheck'] = Checkbutton(self.viewFrame, text='Build', onvalue = True, offvalue = False, variable = self.installModuleLines[module.name]['buildVar'])
            self.installModuleLines[module.name]['buildCheck'].grid(row = counter, column = 4, columnspan = 1)
            self.installModuleLines[module.name]['packageVar'] = BooleanVar()
            if module.package == 'YES':
                self.installModuleLines[module.name]['packageVar'].set(True)
            self.installModuleLines[module.name]['packageCheck'] = Checkbutton(self.viewFrame, text='Package', onvalue = True, offvalue = False, variable = self.installModuleLines[module.name]['packageVar'])
            self.installModuleLines[module.name]['packageCheck'].grid(row = counter, column = 5, columnspan = 1)

            counter = counter + 1


    def scrollFunction(self, event):
        """ Function used for achieving scrolling """
        
        self.canvas.configure(scrollregion=self.canvas.bbox("all"), width=850,height=575)


    def applyChanges(self):
        """ Function that applies changes made to the install configuration to the currently loaded one. """

        old_loc = self.install_config.install_location
        new_install_loc = self.installTextBox.get('1.0', END)
        new_install_loc = new_install_loc.strip()
        self.install_config.install_location = new_install_loc
        res = self.install_config.is_install_valid()
        if res < 0:
            self.root.showWarningMessage('Edit Error', 'WARNING - Permission Error for selected install location', force_popup=True)
            self.root.valid_install = False
        elif res == 0:
            try:
                os.mkdir(self.install_config.install_location)
            except FileNotFoundError:
                self.root.showWarningMessage('Edit Error', 'WARNING - Edited path does not exist', force_popup=True)
                self.root.valid_install = False
        else:
            self.root.valid_install = True

        for module in self.install_config.get_module_list():
            if self.installModuleLines[module.name] is not None:
                if self.installModuleLines[module.name]['cloneVar'].get():
                    module.clone = 'YES'
                else:
                    module.clone = 'NO'
                if self.installModuleLines[module.name]['buildVar'].get():
                    module.build = 'YES'
                else:
                    module.build = 'NO'
                if self.installModuleLines[module.name]['packageVar'].get():
                    module.package = 'YES'
                else:
                    module.package = 'NO'
                module.version = self.installModuleLines[module.name]['versionTextBox'].get('1.0', END).strip()

            module.abs_path = self.install_config.convert_path_abs(module.rel_path)

            if module.name == 'EPICS_BASE':
                self.install_config.base_path = module.abs_path
            elif module.name == 'SUPPORT':
                self.install_config.support_path = module.abs_path
            elif module.name == 'AREA_DETECTOR':
                self.install_config.ad_path = module.abs_path

        self.root.updateConfigPanel()
        self.root.updateAllRefs(self.install_config)
        if self.install_config.is_install_valid():
            self.root.valid_install = True
        else:
            self.root.valid_install = False
        self.root.writeToLog('Applied updated install configuration.\n')


    def applyExit(self):
        """ Function that runs apply changes and then exits the window """

        self.applyChanges()
        self.master.destroy()