""" Class for a window that allows editing of a loaded injector files.
"""

# Tkinter imports
import tkinter as tk
from tkinter import Button, Label, Toplevel, Frame, BooleanVar, Checkbutton
from tkinter import GROOVE, Text, END, INSERT, StringVar, OptionMenu
from tkinter import messagebox
from tkinter import simpledialog
from tkinter import filedialog
from tkinter import font as tkFont
import tkinter.scrolledtext as ScrolledText


class EditInjectorGUI:
    """Class representing a window for editing a currently loaded install config in the GUI.

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
    """

    def __init__(self, root, install_config):
        """Initializer for the EditInjectorGUI class
        """

        self.root = root
        self.master = Toplevel()
        self.master.title('Edit Injector Files')
        self.master.resizable(False, False)

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

        self.dropdown = OptionMenu(self.viewFrame, self.currentEditVar, self.injectorList[0], *self.injectorList)
        self.dropdown.config(width=20)
        self.dropdown.grid(row = 0, column = 0, columnspan = 1, padx = 5, pady = 5)
        self.currentEditVar.trace('w', self.updateEditPanel)

        Button(self.viewFrame, text='New Injector', command = self.newInjector, width = 10).grid(row = 0, column = 1, columnspan = 1)
        Button(self.viewFrame, text='Apply Changes', command = self.applyChanges, width=10).grid(row = 0, column = 2, columnspan = 1)
        Button(self.viewFrame, text='Apply and Exit', command = self.applyExit, width=10).grid(row = 0, column = 3, columnspan = 1)
        Button(self.viewFrame, text='Reload', command = self.reloadPanel, width=10).grid(row = 0, column = 4, columnspan = 1)

        self.editPanel = ScrolledText.ScrolledText(self.viewFrame, height = 37, width = 100)
        self.editPanel.grid(row = 1, column = 0, columnspan = 5)

        self.updateEditPanel()

        self.master.mainloop()


    def newInjector(self):
        """Function for creating new injector files from within the GUI
        """

        new_name = simpledialog.askstring('New Injector', 'Please enter a new injector filename')
        if new_name is not None:
            new_target = simpledialog.askstring('New Target', 'Please enter an injector target relative path using $(INSTALL), $(SUPPORT), $(AREA_DETECTOR), or $(MOTOR)')
            if new_target is not None:
                if not new_target.startswith('$(INSTALL)') and not new_target.startswith('$(SUPPORT)') and not new_target.startswith('$(AREA_DETECTOR)') and not new_target.startswith('$(MOTOR)'):
                    messagebox.showerror('ERROR', 'Please enter a valid relative path.')
                    return
                self.install_config.add_injector_file(new_name, '', new_target)
                self.root.updateAllRefs(self.install_config)
                del self.injectorList[:]
                for file in self.install_config.injector_files:
                    self.injectorList.append(file.name)

                self.currentEditVar.set(self.injectorList[0])
                self.dropdown = OptionMenu(self.viewFrame, self.currentEditVar, self.injectorList[0], *self.injectorList)
                self.dropdown.config(width=20)
                self.dropdown.grid(row = 0, column = 0, columnspan = 1, padx = 5, pady = 5)
                self.reloadPanel()


    def updateEditPanel(self, *args):
        """Wrapper that reloads the panel based on selection
        """

        self.reloadPanel()


    def reloadPanel(self):
        """Reloads Panel based on selection
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
        """Method that reads the edit panel, and sets the injector contents to whatever the user wrote.
        
        Note that there are no checks to see if the injection will be valid.
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
        self.root.updateAllRefs(self.install_config)


    def applyExit(self):
        """Applies changes and exits window
        """

        self.applyChanges()
        self.master.destroy()

