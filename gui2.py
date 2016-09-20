#!/usr/bin/env python
# encoding: utf-8

# Get used to importing this in your Py27 projects!
from __future__ import print_function, division
# Python stdlib
import os.path
import Tkinter as tk
import tkFileDialog as filedialog
import Pmw
from multiprocessing import cpu_count
import ttk

# Chimera stuff
import chimera
import chimera.tkgui
from chimera.baseDialog import ModelessDialog
# Own
from core import Controller, Model

"""
The gui.py module contains the interface code, and only that. 
It should only 'draw' the window, and should NOT contain any
business logic like parsing files or applying modifications
to the opened molecules. That belongs to core.py.
"""

STYLES = {
    tk.Entry: {
        'background': 'white',
        'borderwidth': 1,
        'highlightthickness': 0,
        'insertwidth': 1,
    },
    tk.Button: {
        'borderwidth': 1,
        'highlightthickness': 0,
    },
    tk.Checkbutton: {
        'highlightbackground': chimera.tkgui.app.cget('bg'),
        'activebackground': chimera.tkgui.app.cget('bg'),
    },
    Pmw.OptionMenu: {
        'menubutton_borderwidth': 1,
        'menu_relief': 'flat',
        'menu_activeborderwidth': 0,
        'menu_activebackground': '#DDD',
        'menu_borderwidth': 1,
        'menu_background': 'white',
        'hull_borderwidth': 0,
    },
    Pmw.ComboBox: {
        'entry_borderwidth': 1,
        'entry_highlightthickness': 0,
        'entry_background': 'white',
        'arrowbutton_borderwidth': 1,
        'arrowbutton_relief': 'flat',
        'arrowbutton_highlightthickness': 0,
        'listbox_borderwidth': 1,
        'listbox_background': 'white',
        'listbox_relief': 'ridge',
        'listbox_highlightthickness': 0,
        'scrolledlist_hull_borderwidth': 0
    },
    Pmw.ScrolledListBox: {
        'listbox_borderwidth': 1,
        'listbox_background': 'white',
        'listbox_relief': 'ridge',
        'listbox_highlightthickness': 0,
        'listbox_selectbackground': '#DDD',
        'listbox_selectborderwidth': 0
    }
}

# This is a Chimera thing. Do it, and deal with it.
ui = None


def showUI(callback=None, *args, **kwargs):
    """
    Requested by Chimera way-of-doing-things
    """
    if chimera.nogui:
        tk.Tk().withdraw()
    global ui
    if not ui:  # Edit this to reflect the name of the class!
        ui = OpenMM(*args, **kwargs)
    model = Model()
    controller = Controller(gui=ui, model=model)
    ui.enter()
    if callback:
        ui.addCallback(callback)


class OpenMM(ModelessDialog):

    """
    To display a new dialog on the interface, you will normally inherit from
    ModelessDialog class of chimera.baseDialog module. Being modeless means
    you can have this dialog open while using other parts of the interface.
    If you don't want this behaviour and instead you want your extension to 
    claim exclusive usage, use ModalDialog.
    """

    buttons = ('Run', 'Close')
    default = None
    help = 'https://www.insilichem.com'

    def __init__(self, *args, **kwarg):

        # GUI init
        self.title = "Plume OpenMM"
        self.entries = ("output", "input", "restart", "top",
                        "cuttoff", "constr", "water",  "forcefield",
                        "solvent", "integrator", "platform", "precision")
        self.integrers = ("barostat", "colrate", "tstep", "temp", "nbm", "temp_eq", "simstep",
            "inter", "simulstep", "dcd", "pdbr",  "tolerance",
            "minimiz", "max_steps", "pressure", "bar_interval")

        # OpenMM variables
        for e in self.entries:
            setattr(self, e, tk.StringVar())
        for i in self.integrers:
            setattr(self, i, tk.IntVar())



        # Misc
        self._basis_set_dialog = None
        self.ui_labels = {}

        # Fire up
        ModelessDialog.__init__(self)
        if not chimera.nogui:  # avoid useless errors during development
            chimera.extension.manager.registerInstance(self)

        # Fix styles
        self._fix_styles(*self.buttonWidgets.values())

    def _basis_sets_custom_build(self, *args):
        basis = self.var_qm_basis.get()
        ext = self.var_qm_basis_ext.get()
        if basis:
            self.var_qm_basis_custom.set(
                '{}{}'.format(basis, ext if ext else ''))

    def _initialPositionCheck(self, *args):
        try:
            ModelessDialog._initialPositionCheck(self, *args)
        except Exception as e:
            if not chimera.nogui:  # avoid useless errors during development
                raise e

    def _fix_styles(self, *widgets):
        for widget in widgets:
            try:
                widget.configure(**STYLES[widget.__class__])
            except Exception as e:
                print('Error fixing styles:', type(e), str(e))

    def fillInUI(self, parent):
        """
        This is the main part of the interface. With this method you code
        the whole dialog, buttons, textareas and everything.
        """
        
       

        # Create main window
        self.canvas = tk.Frame(parent)
        self.canvas.pack(expand=True, fill='both')

        # create input frame
        self.ui_input_frame = tk.LabelFrame(self.canvas, text='Model')

        #create output frame
        self.ui_output_frame = tk.LabelFrame(self.canvas, text='Output')

        #create Settings frame
        self.ui_settings_frame = tk.LabelFrame(self.canvas, text='Settings')


        #create Steady frame
        self.ui_steady_frame = tk.LabelFrame(self.canvas, text='Steady')

        #Filling Input frame
        #caja
        self.add_model = tk.Button(self.canvas, text='...')
        self.sanitize_model = tk.Button(self.canvas, text='Sanitize')


        #Filling Output frame

        # Output file
        self.output_entry = tk.Entry(
            self.canvas, width=15, textvariable=self.output)

        self.output_browse = tk.Button(
            self.canvas, text='Browse', command=lambda: self._browse_directory(self.output))

        self.add_reporters = tk.Button(
            self.canvas, text='Add Reporters')

        #Filling Settings frame
        self.force_combo = ttk.Combobox(
            self.canvas, textvariable=self.forcefield)
        self.force_combo.config(values=(
            'amber96', 'amber99sb', 'amber99sbildn', 'amber99sbnmr', 'amber03', 'amber10'))

        # Integrator
        self.int_combo = ttk.Combobox(
            self.canvas, textvariable=self.integrator)
        self.int_combo.config(
            values=('Langevin', 'Brownian', 'Verlet', 'VariableVerlet', 'VariableLangevin'))

        #Filling Steady frame


