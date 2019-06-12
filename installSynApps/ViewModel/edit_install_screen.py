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


# installSynApps module imports
import installSynApps.DataModel.install_config as Config


class EditConfigGUI:

    def __init__(self, root, install_config):

        self.root = root
        self.master=Tk()
        sizex = 800
        sizey = 600
        posx  = 100
        posy  = 100
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
        Label(self.viewFrame, text='Edit Loaded Install Configuration').grid(row = 0, column = 1, columnspan = 4, padx = 5, pady = 5)
        Label(self.viewFrame, text='---------------------------------------------------------------------------------').grid(row = 1, column = 1, columnspan = 4, padx = 5, )

        Label(self.viewFrame, text='Install Location: ').grid(row=2, column = 0)
        self.installTextBox = Text(self.viewFrame).grid(row=2, column = 1, columnspan = 2)
        #self.readInstallModules()
        self.test()

        self.master.mainloop()


    def test(self):
        for i in range(50):
            Label(self.viewFrame, text = i).grid(row=i+2, column = 1)
            Label(self.viewFrame,text="my text"+str(i)).grid(row=i+2,column=1)
            Label(self.viewFrame, text="..........").grid(row=i+2,column=2)

    def scrollFunction(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"),width=750,height=575)


