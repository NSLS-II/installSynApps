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


import os

# Tkinter imports
import tkinter as tk
from tkinter import *
from tkinter import font as tkFont

# installSynApps module imports
import installSynApps.DataModel.install_config as Config
import installSynApps.DataModel.install_module as Module


class AddModuleGUI:
    """
    Class representing a window for adding a new install module to loaded config

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
        self.install_config = install_config
        self.master = Toplevel()
        self.master.title('Add New Module')
        self.master.resizable(False, False)
        sizex = 600
        sizey = 400
        posx = 100
        posy = 100
        #self.master.wm_geometry("%dx%d+%d+%d" % (sizex, sizey, posx, posy))

        self.smallFont = tkFont.Font(family = "Helvetica", size = 10)
        self.largeFont = tkFont.Font(family = "Helvetica", size = 14)

        self.url_type_var = StringVar()
        self.url_type_var.set('GIT_URL')
        self.legal_url_types = ['GIT_URL', 'WGET_URL']

        self.clone_check = BooleanVar()
        self.clone_check.set(False)

        self.build_check = BooleanVar()
        self.clone_check.set(False)

        self.viewFrame = Frame(self.master, relief = GROOVE, padx = 10, pady = 10)
        self.viewFrame.pack()


        self.applyButton = Button(self.viewFrame, text='Save Module', command = self.applyChanges).grid(row = 0, column = 0, columnspan = 1, padx = 5, pady = 5)
        self.applyExitButton = Button(self.viewFrame, text='Return', command = self.applyExit).grid(row = 0, column = 1, columnspan = 1, padx = 5, pady = 5)
        self.reloadButton = Button(self.viewFrame, text='Reset', command = self.reloadPanel).grid(row = 0, column = 2, columnspan = 1, padx = 5, pady = 5)

        self.name_label = Label(self.viewFrame, text='Name:').grid(row =1, column = 0, padx = 5, pady = 5)
        self.name_box = Text(self.viewFrame, height = 1, width = 40, padx = 3, pady = 3)
        self.name_box.grid(row = 1, column = 1, columnspan = 2)

        self.version_label = Label(self.viewFrame, text='Version:').grid(row =2, column = 0, padx = 5, pady = 5)
        self.version_box = Text(self.viewFrame, height = 1, width = 40, padx = 3, pady = 3)
        self.version_box.grid(row = 2, column = 1, columnspan = 2)
        
        self.rel_path_label = Label(self.viewFrame, text = 'Relative Install Path:').grid(row =3, column = 0, padx = 5, pady = 5)
        self.rel_path_box = Text(self.viewFrame, height = 1, width = 40, padx = 3, pady = 3)
        self.rel_path_box.grid(row = 3, column = 1, columnspan = 2)
        
        self.url_type_label = Label(self.viewFrame, text = 'Url Type:').grid(row =4, column = 0, padx = 5, pady = 5)
        self.url_type_dropdown = OptionMenu(self.viewFrame, self.url_type_var, *self.legal_url_types)
        self.url_type_dropdown.grid(row = 4, column = 1)
        
        self.url_label = Label(self.viewFrame, text = 'Url:').grid(row =5, column = 0, padx = 5, pady = 5)
        self.url_box = Text(self.viewFrame, height = 1, width = 40, padx = 3, pady = 3)
        self.url_box.grid(row = 5, column = 1, columnspan = 2)
        
        self.repository_label = Label(self.viewFrame, text = 'Repository:').grid(row =6, column = 0, padx = 5, pady = 5)
        self.repository_box = Text(self.viewFrame, height = 1, width = 40, padx = 3, pady = 3)
        self.repository_box.grid(row = 6, column = 1, columnspan = 2)

        self.clone_build_label = Label(self.viewFrame, text = 'Clone - Build:').grid(row = 7, column = 0, padx = 5, pady = 5)
        self.clone_button = Checkbutton(self.viewFrame, text= 'Clone', onvalue=True, offvalue=False, variable = self.clone_check)
        self.build_button = Checkbutton(self.viewFrame, text= 'Build', onvalue=True, offvalue=False, variable = self.build_check)
        self.clone_button.grid(row = 7, column = 1, padx = 3, pady = 3)
        self.build_button.grid(row = 7, column = 2, padx = 3, pady = 3)

        self.master.mainloop()


    def reloadPanel(self):
        """
        reloads Panel to defaults
        """

        self.name_box.delete('1.0', END)
        self.version_box.delete('1.0', END)
        self.rel_path_box.delete('1.0', END)
        self.url_box.delete('1.0', END)
        self.repository_box.delete('1.0', END)
        self.clone_check.set(False)
        self.build_check.set(False)
        self.url_type_var.set('GIT_URL')


    def applyChanges(self):
        """
        Method that reads the edit panel, and sets the injector contents to whatever the user
        wrote. Note that there are no checks to see if the injection will be valid.
        """

        name = self.name_box.get('1.0', END).strip()
        version = self.version_box.get('1.0', END).strip()
        rel_path = self.rel_path_box.get('1.0', END).strip()
        url_type = self.url_type_var.get()
        url = self.url_box.get('1.0', END).strip()
        repo = self.repository_box.get('1.0', END).strip()
        clone = self.clone_check.get()
        build = self.build_check.get()
        clone_str = 'NO'
        build_str = 'NO'

        if len(name) == 0:
            self.root.showErrorMessage('Add Module Error', 'ERROR - Please enter a valid name.', force_popup = True)
            return

        name = name.upper()

        if len(version) == 0:
            version = 'master'
        
        if len(rel_path) == 0:
            self.root.showErrorMessage('Add Module Error', 'ERROR - Please enter a valid relative path.', force_popup = True)
            return

        if len(url) == 0  or len(repo) == 0:
            self.root.showErrorMessage('Add Module Error', 'ERROR - Please enter a url and repository.', force_popup = True)

        if not url.endswith('/'):
            url = url + '/'

        existing_modules = self.install_config.get_module_list()
        for module in existing_modules:
            if module.name == name or module.rel_path == rel_path or (module.url + module.repository) == url + repo:
                self.root.showErrorMessage('Add Module Error', 'ERROR - Module already exists.', force_popup = True)
                return

        abs_path = self.install_config.convert_path_abs(rel_path)
        if '$(' in abs_path:
            self.root.showErrorMessage('Add Module Error', 'ERROR - Given path not valid or cannot be parsed' , force_popup = True)
            return
        if clone:
            clone_str = 'YES'
        if build:
            build_str = 'YES'
        new_module = Module.InstallModule(name, version, rel_path, url_type, url, repo, clone_str, build_str)
        self.install_config.add_module(new_module)
        self.root.updateAllRefs(self.install_config)
        self.root.showMessage('Info', 'Added module: {} with version {} to config'.format(name, version))


    def applyExit(self):
        """ applies changes and exits window """

        self.master.destroy()

