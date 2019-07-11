""" 
Class for a window that allows editing of a single module
"""

__author__      = "Jakub Wlodek"


import os

# Tkinter imports
import tkinter as tk
from tkinter import *
from tkinter import font as tkFont
from tkinter import ttk

# installSynApps module imports
import installSynApps.DataModel.install_config as Config
import installSynApps.DataModel.install_module as Module


class EditSingleModuleGUI:
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
    url_type_var/edit_name_var : StringVar
        tied to url type and list of module names respectively
    legal_url_types/legal_names : list of str
        lists legal url types and list of module names
    clone_check/build_check : BooleanVar
        boolean variables that track whether or not to build the module
    module_dropdown : Checkbox
        A dropdown menu for selecting which module to edit
    applyButton/exitWindowButton : Button
        button that runs the apply method (and exits)
    name_box/version_box/rel_path_box/url_box/repository_box : Text
        Boxes for editing certain module features.
    url_type_dropdown : OptionMenu
        dropdown for url types
    clone_button/build_button : CheckButton
        toggles to clone/build
    
    Methods
    -------
    reloadPanelWrapper(*args)
        A wrapper function that just calls reloadPanel()
    reloadPanel()
        resets all text fields to blank
    applyChanges()
        Applies changes to the loaded config and updates all references
    exitWindow()
        exits from the window
    """


    def __init__(self, root, install_config):
        """
        Constructor for the EditSingleModuleGUI class

        Parameters
        ----------
        root : InstallSynAppsGUI
            The root opening window. Used to refresh references on apply
        install_config : InstallConfiguration
            The currently loaded install configuration
        """

        self.root = root
        self.install_config = install_config
        self.master = Toplevel()
        self.master.title('Edit Single Module')
        self.master.resizable(False, False)

        self.smallFont = tkFont.Font(family = "Helvetica", size = 10)
        self.largeFont = tkFont.Font(family = "Helvetica", size = 14)

        self.url_type_var = StringVar()
        self.url_type_var.set('GIT_URL')
        self.legal_url_types = ['GIT_URL', 'WGET_URL']
        
        self.edit_name_var = StringVar()
        self.edit_name_var.set(self.install_config.get_module_list()[0].name)
        self.legal_names = []

        for module in self.install_config.get_module_list():
            self.legal_names.append(module.name)

        self.clone_check = BooleanVar()
        self.clone_check.set(False)

        self.build_check = BooleanVar()
        self.clone_check.set(False)

        self.viewFrame = Frame(self.master, relief = GROOVE, padx = 10, pady = 10)
        self.viewFrame.pack()

        self.applyButton = Button(self.viewFrame, text='Save Changes', command = self.applyChanges).grid(row = 0, column = 0, columnspan = 1, padx = 5, pady = 5)
        self.exitWindowButton = Button(self.viewFrame, text='Return', command = self.exitWindow).grid(row = 0, column = 1, columnspan = 1, padx = 5, pady = 5)
        self.reloadButton = Button(self.viewFrame, text='Reload', command = self.reloadPanel).grid(row = 0, column = 2, columnspan = 1, padx = 5, pady = 5)

        self.title_label = Label(self.viewFrame, text='Edit individual module:').grid(row = 1, column = 0, columnspan = 1, padx = 5, pady = 5)
        #self.module_dropdown = OptionMenu(self.viewFrame, self.edit_name_var, *self.legal_names)
        self.module_dropdown = ttk.Combobox(self.viewFrame, textvariable=self.edit_name_var, values=self.legal_names)
        self.module_dropdown.grid(row = 1, column = 1)
        self.edit_name_var.trace('w', self.reloadPanelWrapper)

        self.name_label = Label(self.viewFrame, text='Name:').grid(row =3, column = 0, padx = 5, pady = 5)
        self.name_box = Text(self.viewFrame, height = 1, width = 40, padx = 3, pady = 3)
        self.name_box.grid(row = 3, column = 1, columnspan = 2)

        self.version_label = Label(self.viewFrame, text='Version:').grid(row =3, column = 0, padx = 5, pady = 5)
        self.version_box = Text(self.viewFrame, height = 1, width = 40, padx = 3, pady = 3)
        self.version_box.grid(row = 3, column = 1, columnspan = 2)
        
        self.rel_path_label = Label(self.viewFrame, text = 'Relative Install Path:').grid(row =4, column = 0, padx = 5, pady = 5)
        self.rel_path_box = Text(self.viewFrame, height = 1, width = 40, padx = 3, pady = 3)
        self.rel_path_box.grid(row = 4, column = 1, columnspan = 2)
        
        self.url_type_label = Label(self.viewFrame, text = 'Url Type:').grid(row =5, column = 0, padx = 5, pady = 5)
        self.url_type_dropdown = OptionMenu(self.viewFrame, self.url_type_var, *self.legal_url_types)
        self.url_type_dropdown.grid(row = 5, column = 1)
        
        self.url_label = Label(self.viewFrame, text = 'Url:').grid(row =6, column = 0, padx = 5, pady = 5)
        self.url_box = Text(self.viewFrame, height = 1, width = 40, padx = 3, pady = 3)
        self.url_box.grid(row = 6, column = 1, columnspan = 2)
        
        self.repository_label = Label(self.viewFrame, text = 'Repository:').grid(row =7, column = 0, padx = 5, pady = 5)
        self.repository_box = Text(self.viewFrame, height = 1, width = 40, padx = 3, pady = 3)
        self.repository_box.grid(row = 7, column = 1, columnspan = 2)

        self.clone_build_label = Label(self.viewFrame, text = 'Clone - Build:').grid(row = 8, column = 0, padx = 5, pady = 5)
        self.clone_button = Checkbutton(self.viewFrame, text= 'Clone', onvalue=True, offvalue=False, variable = self.clone_check)
        self.build_button = Checkbutton(self.viewFrame, text= 'Build', onvalue=True, offvalue=False, variable = self.build_check)
        self.clone_button.grid(row = 8, column = 1, padx = 3, pady = 3)
        self.build_button.grid(row = 8, column = 2, padx = 3, pady = 3)

        self.master.mainloop()


    def reloadPanelWrapper(self, *args):
        """ A wrapper function for reloading the panel """

        self.reloadPanel()


    def reloadPanel(self):
        """
        reloads Panel to defaults
        """

        self.name_box.delete('1.0', END)
        self.version_box.delete('1.0', END)
        self.rel_path_box.delete('1.0', END)
        self.url_box.delete('1.0', END)
        self.repository_box.delete('1.0', END)

        for module in self.install_config.get_module_list():
            if module.name == self.edit_name_var.get():
                self.name_box.insert(INSERT, module.name)
                self.version_box.insert(INSERT, module.version)
                self.rel_path_box.insert(INSERT, module.rel_path)
                self.url_type_var.set(module.url_type)
                self.url_box.insert(INSERT, module.url)
                self.repository_box.insert(INSERT, module.repository)
                clone_bool = False
                build_bool = False
                if module.clone == 'YES':
                    clone_bool = True
                if module.build == 'YES':
                    build_bool = True
                self.clone_check.set(clone_bool)
                self.build_check.set(build_bool)


    def applyChanges(self):
        """

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
        if clone:
            clone_str = 'YES'
        if build:
            build_str = 'YES'

        if len(name) == 0:
            self.root.showErrorMessage('Edit Module Error', 'ERROR - Please enter a valid name.', force_popup = True)
            return

        name = name.upper()

        if len(version) == 0:
            version = 'master'
        
        if len(rel_path) == 0:
            self.root.showErrorMessage('Edit Module Error', 'ERROR - Please enter a valid relative path.', force_popup = True)
            return

        if len(url) == 0  or len(repo) == 0:
            self.root.showErrorMessage('Edit Module Error', 'ERROR - Please enter a url and repository.', force_popup = True)

        if not url.endswith('/'):
            url = url + '/'

        existing_modules = self.install_config.get_module_list()
        for module in existing_modules:
            if module.name == self.edit_name_var.get():
                module.version = version
                module.rel_path = rel_path
                module.abs_path = self.install_config.convert_path_abs(rel_path)
                module.url_type = url_type
                module.url = url
                module.repository = repo
                module.clone = clone_str
                module.build = build_str

        self.root.updateAllRefs(self.install_config)
        self.root.updateConfigPanel()
        self.root.showMessage('Info', 'Upated module: {}'.format(name))


    def exitWindow(self):
        """ exits from the window """

        self.master.destroy()
