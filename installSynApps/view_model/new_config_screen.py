""" Class for a window that allows editing of loaded macros.
"""

__author__      = "Jakub Wlodek"


# Tkinter imports
import tkinter as tk
from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
from tkinter import font as tkFont
import tkinter.scrolledtext as ScrolledText


import os

# installSynApps module imports
import installSynApps.DataModel.install_config as Config
import installSynApps.IO.config_parser as Parser
import installSynApps.IO.config_injector as Injector


class NewConfigGUI:


    def __init__(self, root):

        self.root = root
        self.master = Toplevel()
        self.master.title('New Install Config')
        self.master.resizable(False, False)

        self.smallFont = tkFont.Font(family = "Helvetica", size = 10)
        self.largeFont = tkFont.Font(family = "Helvetica", size = 14)

        self.viewFrame = Frame(self.master, relief = GROOVE, padx = 10, pady = 10)
        self.viewFrame.pack()

        self.config_type = tk.IntVar()
        self.config_types = {
            1 : 'AreaDetector',
            2 : 'Motor',
            3 : 'All'
        }
        self.config_type.set(1)


        self.config_type_label = Label(self.viewFrame, text='Select Config Type:').grid(row=0, column=0, padx=5, pady=5)
        for val in self.config_types.keys():
            tk.Radiobutton(self.viewFrame, text=self.config_types[val], variable=self.config_type, value=val).grid(row=0, column=val, padx=5, pady=5)

        #Label(self.viewFrame, text='').grid(row=1, pady=3)

        self.install_loc_label = Label(self.viewFrame, text='Install Location:').grid(row=2, column=0, pady=5)
        self.browse_button = Button(self.viewFrame, text='Browse', command=self.selectInstallLoc).grid(row=2, column=3, padx=5, pady=5)
        self.dir_box = Text(self.viewFrame, height=1, width=45, padx=3, pady=3)
        self.dir_box.grid(row=2, column=1, columnspan=2)

        Label(self.viewFrame, text='').grid(row=4)


        self.update_tags_var = BooleanVar()
        self.update_tags_var.set(True)
        self.update_tags_button = Checkbutton(self.viewFrame, text='Auto-Update Tags', onvalue=True, offvalue=False, variable=self.update_tags_var)
        self.update_tags_button.grid(row=5, column=0, padx=3, pady=3)

        self.applyButton = Button(self.viewFrame, text='Create', command = self.applyChanges, width=12).grid(row = 5, column = 2, columnspan = 1, padx = 5, pady = 5)
        self.exitButton = Button(self.viewFrame, text='Cancel', command = self.cancel, width=12).grid(row = 5, column = 3, columnspan = 1, padx = 5, pady = 5)

        self.master.mainloop()


    def reloadPanel(self):
        self.dir_box.delete('1.0', END)


    def applyChanges(self):
        t = self.config_types[self.config_type.get()]
        u = self.update_tags_var.get()
        i = self.dir_box.get('1.0', END).strip()
        if not os.path.exists(i) or not os.path.isdir(i):
            self.root.showErrorMessage('Error', 'ERROR - Path: {} does not exist or is not a directory!'.format(i), force_popup=True)
            return
        self.root.newConfig(t, i, update_tags=u)
        self.cancel()

    def cancel(self):
        self.master.destroy()


    def selectInstallLoc(self):
        dir = filedialog.askdirectory(initialdir='.')
        if dir is not None:
            self.dir_box.delete('1.0', END)
            self.dir_box.insert(INSERT, dir)