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
from chimera.widgets import MoleculeScrolledListBox
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
        'width': 10,
    },
    tk.Listbox: {
        'height': '5',
        'width': '5',

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

    buttons = ('Save Input', 'Schedule', 'Run', 'Close')
    default = None
    help = 'https://www.insilichem.com'

    def __init__(self, *args, **kwarg):

        # GUI init

        self.title = "Plume OpenMM"
        self.entries = ("output", "input", "restart", "top",
                        "cuttoff", "constr", "water",  "forcefield",
                        "solvent", "integrator", "platform", "precision", "external_forc", "parametrize_forc",
                         "dcd", "pdbr","other_reporters","md_reporters", "stage","number_stage")
        self.reporters = ['Time', 'Steps', 'Speed', 'Progress',
                     'Potencial Energy', 'Kinetic Energy', 'Total Energy', 'Temperature',
                     'Volume', 'Density']
        self.integrers = ("barostat", "colrate", "tstep", "temp", "nbm", "temp_eq", "simstep",
                          "inter", "simulstep",  "tolerance",
                          "minimiz", "max_steps", "pressure", "bar_interval", "stage_pressure_steps",
                           "stage_pressure", "stage_barostat","stage_temp")


        # OpenMM variables
        for e in self.entries:
            setattr(self, e, tk.StringVar())
        for r in self.reporters:
            setattr(self, r, tk.StringVar())
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

        # Create all frames

        # Create input frame
        self.ui_input_frame = tk.LabelFrame(self.canvas, text='Model')
        # Create output frame
        self.ui_output_frame = tk.LabelFrame(self.canvas, text='Output')
        # Create Settings frame
        self.ui_settings_frame = tk.LabelFrame(self.canvas, text='Settings')
        # create Steady frame
        self.ui_steady_frame = tk.LabelFrame(self.canvas, text='Steady')

        # Fill frames

        # Fill Input frame
        self.show_models = MoleculeScrolledListBox(self.ui_input_frame)
        self.add_model = tk.Button(self.canvas, text='Set Model')
        self.sanitize_model = tk.Button(self.canvas, text='Sanitize')

        # Configure Input frame
        self.ui_input_frame.columnconfigure(0, weight=1)
        self.ui_input_frame.rowconfigure(0, weight=1)
        input_option = {'padx': 5, 'pady': 5}
        self.show_models.grid(in_=self.ui_input_frame, row=0, column=0,
                              rowspan=2, columnspan=2, sticky='news', **input_option)
        self.add_model.grid(
            in_=self.ui_input_frame, row=2, column=0, sticky='we')
        self.sanitize_model.grid(
            in_=self.ui_input_frame, row=2, column=1, sticky='we')
        self._fix_styles(self.show_models, self.add_model, self.sanitize_model)

        # Fill Output frame

        # Output file
        self.output_entry = tk.Entry(
            self.canvas, textvariable=self.output)
        # Browse button
        self.output_browse = tk.Button(
            self.canvas, text='...', command=lambda: self._browse_directory(self.output))
        # MD reporters button
        self.add_reporters_md = tk.Button(
            self.canvas, text='+', command= self._fill_w1)
        # Show all MD reporters selected
        self.show_reporters_md = tk.Listbox(
            self.ui_output_frame, listvariable= self.md_reporters)
        # Add Other reporters
        self.add_reporters_others = tk.Button(
            self.canvas, text='+', command= self._fill_w2)
        # Show other reporters Selected
        self.show_reporters_others = tk.Listbox(
            self.ui_output_frame, listvariable= self.other_reporters)

        # Apply grid to output frame
        self.output_grid = [['Save at', self.output_entry, self.output_browse],
                            ['Trajectory\nReporters',  self.show_reporters_md,
                                self.add_reporters_md],
                            ['MD\nReporters', self.show_reporters_others, self.add_reporters_others]]
        self.auto_grid(self.ui_output_frame, self.output_grid)

        # Fill Settings frame
        # Forcefield Combobox
        self.force_combo = ttk.Combobox(
            self.canvas, textvariable=self.forcefield)
        self.force_combo.config(values=(
            'amber96', 'amber99sb', 'amber99sbildn', 'amber99sbnmr', 'amber03', 'amber10'))
        # Forcefield Buttons to add another stablished forcefield, get an
        # external one or create your own.
        self.add_default_forcefield = tk.Button(
            self.canvas, text='+')
        self.add_external_forcefield = tk.Button(
            self.canvas, text='...', command=lambda: self._browse_file(self.external_forc))
        self.parametrize_your_forcefield = tk.Button(
            self.canvas, text='...',)
        # Forcefield entries
        self.external_forc_entry = tk.Entry(
            self.canvas, textvariable=self.external_forc)
        self.parametrize_forc_entry = tk.Entry(
            self.canvas, textvariable=self.parametrize_forc)
        # Create Integrator
        self.int_combo = ttk.Combobox(
            self.canvas, textvariable=self.integrator)
        self.int_combo.config(
            values=('Langevin', 'Brownian', 'Verlet', 'VariableVerlet', 'VariableLangevin'))
        # Create Time Step Entry
        self.timestep_entry = tk.Entry(
            self.canvas, textvariable=self.tstep, )
        # Advanced Options Buttons
        self.advanced_options = tk.Button(
            self.canvas, text='Opt')

        # Apply grid to settings frame
        self.settings_grid = [['Forcefield', self.force_combo, self.add_default_forcefield],
                              ['External\nForcefield',  self.external_forc_entry,
                                  self.add_external_forcefield],
                              ['Parametrized\nForcefield', self.parametrize_forc_entry,
                                  self.parametrize_your_forcefield],
                              ['Integrator', self.int_combo],
                              ['Time Step', self.timestep_entry, self.advanced_options]]
        self.auto_grid(self.ui_settings_frame, self.settings_grid)

        # Filling Steady frame
        # Up and Down arrow button
        self.photo_down = tk.PhotoImage(
            file="/home/daniel/openmmTK/OpenMM/arrow_down.png")
        self.photo_up = tk.PhotoImage(
            file="/home/daniel/openmmTK/OpenMM/arrow_up.png")
        self.movesteady_up = tk.Button(self.canvas, image=self.photo_up)
        self.movesteady_down = tk.Button(self.canvas, image=self.photo_down)
        #+ and - button
        self.add_to_steady = tk.Button(self.canvas, text='+', command= self._fill_w3)
        self.remove_to_steady = tk.Button(self.canvas, text='-')
        # Scrolled Box
        self.steady_scrolbox = tk.Listbox(self.ui_steady_frame, height=27)

        # Apply grid
        self.steady_scrolbox.grid(
            in_=self.ui_steady_frame, row=0, column=0, rowspan=10, columnspan=3, sticky='news', **input_option)
        self.movesteady_down.grid(
            in_=self.ui_steady_frame, row=8, column=4,  sticky='news', **input_option)
        self.movesteady_up.grid(
            in_=self.ui_steady_frame, row=6, column=4, sticky='news', **input_option)
        self.add_to_steady.grid(
            in_=self.ui_steady_frame, row=2, column=4, sticky='news', **input_option)
        self.remove_to_steady.grid(
            in_=self.ui_steady_frame, row=4, column=4, sticky='news', **input_option)

        # Ordering Frames
        frames = [[self.ui_input_frame, self.ui_output_frame]]
        self.auto_grid(
            self.canvas, frames, resize_columns=(0, 1), sticky='news')
        self.ui_settings_frame.grid(
            row=len(frames), columnspan=2, sticky='ew', padx=5, pady=5)
        self.ui_steady_frame.grid(
            row=0, column=3, rowspan=2, sticky='new', padx=5, pady=5)




        








    # Callbacks
    def _browse_file(self, var_1):
        """
        Browse file path
         """

        path = filedialog.askopenfilename(initialdir='~/', filetypes=(
            ('Frcmod', '.frmod'), ('All', '*')))
        var_1.set(path)
        file_path, file_extension = os.path.splitext(path)
        

    def _browse_directory(self, var):
        """
        Search for the path to save the output

        Parameters
        ----------
        var= Interface entry widget where we wish insert the path file.

        """

        path = filedialog.askdirectory(
            initialdir='~/')
        var.set(path)

    def _fill_w1(self):
        """
        Opening MD reports options
        """

        input_option = {'padx': 10, 'pady': 10}

        #creating window
        self.w1=tk.Toplevel()
        self.w1.title("MD reporters")
        #creating Frame
        self.f1=tk.Frame(self.w1)
        self.f1.pack()
        #LabelFrame
        self.f1_label=tk.LabelFrame(self.f1, text='MD Reporters')
        self.f1_label.grid(row=0, column=0, **input_option)
        #Creating Buttons
        self.dcd_check = ttk.Checkbutton(
            self.f1, text="DCD Reporter", variable=self.dcd, onvalue='dcd', offvalue='')
        self.pdb_check = ttk.Checkbutton(
            self.f1, text="PDB Reporter", variable=self.pdbr, onvalue='pdb', offvalue='')
        self.close_b1=tk.Button(self.f1, text='close', command= self._close_w1)

        #Configure window grid
        self.dcd_check.grid(in_=self.f1_label, row=0, column=0, sticky='ew', **input_option)
        self.pdb_check.grid(in_=self.f1_label, row=1, column=0, sticky='ew', **input_option)
        self.close_b1.grid(in_=self.f1_label, row=2, column=1, sticky='ew', **input_option)
        #Define Widget Style
        self._fix_styles(self.dcd_check, self.pdb_check, self.close_b1)
        #Holding window
        self.w1.mainloop()
    def _close_w1(self):
        self.md_reporters.set((self.dcd.get(), self.pdbr.get()))
        self.w1.withdraw()
        


    def _fill_w2(self):
        """
        Opening Other reports options as Time, Energy, Temperature...
        """

        input_option = {'padx': 10, 'pady': 10}

        #creating window
        self.w2=tk.Toplevel()
        self.w2.title("Other reporters")
        #creating Frame
        self.f2=tk.Frame(self.w2)
        self.f2.pack()
        #LabelFrame
        self.f2_label=tk.LabelFrame(self.f2, text='Other Reporters')
        self.f2_label.grid(row=0, column=0, **input_option)
        #Creating Buttons
        # Creating Checkbuttons reporters


        for i, item in enumerate(self.reporters):
            #Gride Check Buttons
            check = self.ui_labels[item] = ttk.Checkbutton(
                self.f2, text=item, variable= getattr(self, item),  onvalue=item, offvalue='')
            item=check
            if i<5:
                item.grid(
                    in_=self.f2_label, row=0, column=i, sticky='ew', **input_option)
            else:
                item.grid(
                    in_=self.f2_label, row=1, column=i-5, sticky='ew', **input_option)


        #creating close button
        self.close_b2=tk.Button(
            self.f2, text='close', command= self._close_w2)
        #Configure window grid
        self.close_b2.grid(in_=self.f2_label, row=2, column=5, sticky='ew', **input_option)
        #Define Widget Style
        self._fix_styles(self.close_b2)
        #Holding window
        self.w2.mainloop()
    def _close_w2(self):
    
        self.other_reporters.set((
            self.Time.get(), self.Steps.get(), self.Speed.get(), self.Progress.get(),
            self.__dict__['Potencial Energy'].get(), self.__dict__['Kinetic Energy'].get(), self.__dict__['Total Energy'].get(),
            self.Temperature.get(), self.Volume.get(),self.Density.get()))
        self.w2.withdraw()


    def _fill_w3(self):
        """
        Window where we create different phases of our MD
        """

        input_option = {'padx': 10, 'pady': 10}

        #creating window
        self.w3=tk.Toplevel()
        self.w3.title("Md steady create")

        #Creating tabs

        note = ttk.Notebook(self.w3)
        self.tab_1=tk.Frame(note)
        self.tab_2=tk.Frame(note)
        self.tab_2.pack()
        self.tab_3=tk.Frame(note)
        self.tab_4=tk.Frame(note)
        self.tab_5=tk.Frame(note)
        note.add(self.tab_1, text="Stage", state="normal")
        note.add(self.tab_2, text="Temperature & Pressure", state="normal")
        note.add(self.tab_3, text="Constrains", state="normal")
        note.add(self.tab_4, text="Minimization", state="normal")
        note.add(self.tab_5, text="MD Final Settings", state="normal")
        note.pack()

        #Tab1
        #Creating Buttons  
        stage_name_entry = tk.Entry(
            self.tab_1, width= 20, textvariable=self.stage)
        stage_number_entry = tk.Entry(
            self.tab_1, width=20, textvariable=self.number_stage)
        self.close_b3=tk.Button(
            self.tab_1, text='close', command= self._close_w3)
        #Apply grid
        self.stage_grid=[['Stage Number', stage_number_entry],
                        ['Stage Name', stage_name_entry],
                        ['',self.close_b3]]
        self.auto_grid(self.tab_1, self.stage_grid)

        #Tab2
        #Creating Buttons
        self.stage_temp_lframe = tk.LabelFrame(self.tab_2, text='Temperature')
        self.stage_pressure_lframe = tk.LabelFrame(self.tab_2, text='Pressure')
        frames=[[self.stage_temp_lframe, self.stage_pressure_lframe]]
        self.auto_grid(self.tab_2, frames)



        self.stage_temp_entry = tk.Entry(
            self.tab_2, textvariable=self.stage_temp)
        self.temp_grid = [['Stage Temperature', self.stage_temp_entry]]
        self.auto_grid(self.stage_temp_lframe, self.temp_grid)


        self.stage_barostat_check = ttk.Checkbutton(
            self.tab_2, text="Barostat", variable=self.stage_barostat,
            command=self._bar_settings)
        self.stage_pressure_Entry = tk.Entry(
            self.tab_2, state= 'disabled', textvariable=self.stage_pressure)
        self.stage_barostat_steps_Entry = tk.Entry(
            self.tab_2, state= 'disabled', textvariable=self.stage_pressure_steps)

        self.pres_grid = [[self.stage_barostat_check,''],
                         ['Pressure', self.stage_pressure_Entry],
                         ['Barostat Every', self.stage_barostat_steps_Entry]]
        self.auto_grid(self.stage_pressure_lframe, self.pres_grid)
        
        self.w3.mainloop()



    def _bar_settings(self):
        """
        enable/disable barostat settings
        """

        if self.stage_barostat.get() is 1:
            self.stage_pressure_Entry.configure(state='normal')
            self.stage_barostat_steps_Entry.configure(state='normal')
        else:
            self.stage_pressure_Entry.configure(state='disabled')
            self.stage_barostat_steps_Entry.configure(state='disabled')
    
    
    def _close_w3(self):
        """
        Close window w3
        """

        self.w3.withdraw()


# Script Functions

    def auto_grid(self, parent, grid, resize_columns=(1,), label_sep=':', **options):
        """
        Auto grid an ordered matrix of Tkinter widgets.

        Parameters
        ----------
        parent : tk.Widget
            The widget that will host the widgets on the grid
        grid : list of list of tk.Widget
            A row x columns matrix of widgets. It is built on lists.
            Each list in the toplevel list represents a row. Each row
            contains widgets, tuples or strings, in column order.  
            If it's a widget, it will be grid at the row i (index of first level
            list) and column j (index of second level list).
            If a tuple of widgets is found instead of a naked widget,
            they will be packed in a frame, and grid'ed as a single cell.
            If it's a string, a Label will be created with that text, and grid'ed. 

            For example:
            >>> grid = [['A custom label', widget_0_1, widget_0_2], # first row
            >>>         [widget_1_0, widget_1_1, widget_1_2],       # second row
            >>>         [widget_2_0, widget_2_1, (widgets @ 2_2)]]  # third row

        """
        for column in resize_columns:
            parent.columnconfigure(column, weight=int(100/len(resize_columns)))
        _kwargs = {'padx': 2, 'pady': 2, 'ipadx': 2, 'ipady': 2}
        _kwargs.update(options)
        for i, row in enumerate(grid):
            for j, item in enumerate(row):
                kwargs = _kwargs.copy()
                sticky = 'ew'
                if isinstance(item, tuple):
                    frame = tk.Frame(parent)
                    self.auto_pack(frame, item, side='left', padx=2, pady=2, expand=True, fill='x',
                                   label_sep=label_sep)
                    item = frame
                elif isinstance(item, basestring):
                    sticky = 'e'
                    label = self.ui_labels[item] = tk.Label(
                        parent, text=item + label_sep if item else '')
                    item = label
                elif isinstance(item, tk.Checkbutton):
                    sticky = 'w'
                if 'sticky' not in kwargs:
                    kwargs['sticky'] = sticky
                item.grid(in_=parent, row=i, column=j, **kwargs)
                self._fix_styles(item)

    def Close(self):
        """
        Default! Triggered action if you click on the Close button
        """
        global ui
        ui = None
        ModelessDialog.Close(self)
        self.destroy()
