#
# Class for a window that allows editing of a loaded install config.
#
# Author: Jakub Wlodek
#


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


class EditConfigGUI:

    def __init__(self, root, install_config):

        self.root = root
        self.master=Tk()
        self.master.title('Edit Install Config')
        self.master.resizable(False, False)
        sizex = 750
        sizey = 600
        posx  = 100
        posy  = 100
        self.installModuleLines = {}
        self.master.wm_geometry("%dx%d+%d+%d" % (sizex, sizey, posx, posy))

        self.smallFont = tkFont.Font(family = "Helvetica", size = 10)
        self.largeFont = tkFont.Font(family = "Helvetica", size = 14)

        self.install_config = install_config

        topFrame = Frame(self.master, relief=GROOVE, width = 50, height = 100)
        topFrame.place(x=10, y= 10)

        self.canvas = Canvas(topFrame)

        self.viewFrame = Frame(self.canvas, relief=GROOVE)
        scrollbar = Scrollbar(topFrame, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side='right', fill='y')
        self.canvas.pack(side='left');
        self.canvas.create_window((0,0), window=self.viewFrame, anchor='nw')
        self.viewFrame.bind('<Configure>', self.scrollFunction)
        Label(self.viewFrame, text='    Edit Loaded Install Configuration', anchor=W, justify=LEFT).grid(row = 0, column = 0, columnspan = 1, pady = 5)
        self.applyButton = Button(self.viewFrame, text = 'Apply', justify = LEFT, command=self.applyChanges).grid(row = 0, column = 5)
        self.splitter = Label(self.viewFrame, text='--------------------------------------------------------------------------------------------------------------------------------------')
        self.splitter.grid(row = 1, column = 0, columnspan = 6)

        Label(self.viewFrame, text='Install Location: ').grid(row=2, column = 0)
        self.installTextBox = Text(self.viewFrame, height = 1, width = 32, padx = 3, pady = 3)
        self.installTextBox.grid(row=2, column = 1, columnspan = 2)
        self.installTextBox.insert(INSERT, self.install_config.install_location)
        self.readInstallModules()

        self.master.mainloop()


    def readInstallModules(self):
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

            counter = counter + 1


    def scrollFunction(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"),width=700,height=575)


    def applyChanges(self):
        new_install_loc = self.installTextBox.get('1.0', END)
        new_install_loc = new_install_loc.strip()
        if len(new_install_loc) > 0:
            if os.path.exists(new_install_loc):
                self.install_config.install_location = new_install_loc

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
                module.version = self.installModuleLines[module.name]['versionTextBox'].get('1.0', END).strip()

        self.root.updateConfigPanel()

def runTest():
    parser = Parser.ConfigParser('configure')
    install_config = parser.parse_install_config()
    window = EditConfigGUI(None, install_config)