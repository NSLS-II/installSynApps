"""Module containing view model for creating new configurations
"""

# Tkinter imports
import tkinter as tk
from tkinter import Button, Label, Toplevel, Frame, BooleanVar, Checkbutton
from tkinter import GROOVE, Text, END, INSERT
from tkinter import messagebox
from tkinter import filedialog
from tkinter import font as tkFont
import tkinter.scrolledtext as ScrolledText

# Standard lib imports
import os


class NewConfigGUI:
    """Class for a window that allows editing of loaded macros.

    Attributes
    ----------
    root : Tk
        Main Tk root window
    master : TopLevel
        New window
    smallFont : ttkFont
        Smaller font size
    largeFont : ttkFont
        larger font size
    viewFrame : Frame
        main container frame
    config_type : IntVar
        selector for which config base to use
    config_types : dict of int->str
        maps config_type to string
    dir_box : Text
        Textfield for target directory
    update_tags_var : booleanVar
        variable that stores whether to auto-update tags
    update_tags_button : checkbutton
        toggles update_tags_var
    """

    def __init__(self, root):
        """Initializer for NewConfigGUI
        """

        self.root = root
        self.master = Toplevel()
        self.master.title('New Install Config')
        self.master.resizable(False, False)

        self.smallFont = tkFont.Font(family = "Helvetica", size = 10)
        self.largeFont = tkFont.Font(family = "Helvetica", size = 14)

        self.viewFrame = Frame(self.master, relief = GROOVE, padx = 10, pady = 10)
        self.viewFrame.pack()


        Label(self.viewFrame, text='Install Location:').grid(row=1, column=0, pady=5)
        Button(self.viewFrame, text='Browse', command=self.selectInstallLoc).grid(row=1, column=3, padx=5, pady=5)
        self.dir_box = Text(self.viewFrame, height=1, width=45, padx=3, pady=3)
        self.dir_box.grid(row=1, column=1, columnspan=2)

        Label(self.viewFrame, text='').grid(row=4)

        self.update_tags_var = BooleanVar()
        self.update_tags_var.set(True)
        self.update_tags_button = Checkbutton(self.viewFrame, text='Auto-Update Tags', onvalue=True, offvalue=False, variable=self.update_tags_var)
        self.update_tags_button.grid(row=4, column=0, padx=3, pady=3)

        Button(self.viewFrame, text='Create', command = self.applyChanges, width=12).grid(row = 4, column = 2, columnspan = 1, padx = 5, pady = 5)
        Button(self.viewFrame, text='Cancel', command = self.cancel, width=12).grid(row = 4, column = 3, columnspan = 1, padx = 5, pady = 5)

        self.master.mainloop()


    def reloadPanel(self):
        """Refreshes the current window
        """

        self.dir_box.delete('1.0', END)


    def applyChanges(self):
        """Creates new install configuration given properties
        """

        u = self.update_tags_var.get()
        i = self.dir_box.get('1.0', END).strip()
        if not os.path.exists(i) or not os.path.isdir(i):
            self.root.showErrorMessage('Error', 'ERROR - Path: {} does not exist or is not a directory!'.format(i), force_popup=True)
            return
        self.root.newConfig(i, update_tags=u)
        self.cancel()


    def cancel(self):
        """Closes window
        """

        self.master.destroy()


    def selectInstallLoc(self): 
        """Shows file selection popup
        """

        dir = filedialog.askdirectory(initialdir='.')
        if dir is not None:
            self.dir_box.delete('1.0', END)
            self.dir_box.insert(INSERT, dir)