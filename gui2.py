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
        # Input/Output

        # Create main window
        self.canvas = tk.Frame(parent)
        self.canvas.pack(expand=True, fill='both')

        # create another frame
        self.ui_input_frame = tk.LabelFrame(self.canvas, text='Input/Output')
        self.ui_input_frame.grid(column=1, row=1)

        # insert Input
        self.input_entry = tk.Entry(
            self.canvas, width=15, textvariable=self.input)
        self.input_browse = tk.Button(
            self.canvas, text="Browse", command=lambda: self._browse_file(self.input, self.top))

        # insert Top
        self.top_entry = tk.Entry(self.canvas, width=15, textvariable=self.top)

        # restart file
        self.restart_entry = tk.Entry(
            self.canvas, width=15, textvariable=self.restart)
        self.restart_browse = tk.Button(
            self.canvas, text="Browse", command=lambda: self._browse_file(self.restart, None))

        # Output file
        self.output_entry = tk.Entry(
            self.canvas, width=15, textvariable=self.output)

        self.output_browse = tk.Button(
            self.canvas, text="Browse", command=lambda: self._browse_directory(self.output))

        self.model_grid = [['Input File', self.input_entry, self.input_browse],
                           ['Restart File', self.restart_entry,
                               self.restart_browse],
                           ['Save at', self.output_entry, self.output_browse]]

        self.auto_grid(self.ui_input_frame, self.model_grid)

        # System Basics

        # System paramaters frame
        self.ui_parameters_frame = tk.LabelFrame(
            self.canvas, text='System Parameters')
        self.ui_parameters_frame.grid(column=1, row=2)

        # Molecule colision rate
        self.colrate_entry = tk.Entry(
            self.canvas, textvariable=self.colrate)

        # Time per step
        self.timestep_entry = tk.Entry(
            self.canvas, textvariable=self.tstep)


        # MD temeperature
        self.temperature_entry = tk.Entry(
            self.canvas, textvariable=self.temp)


        # Barostat
        self.barostat_check = ttk.Checkbutton(
            self.canvas, text="", variable=self.barostat, command=self._barostat_show)

        # Apply grid
        self.model_grid = [['Colision Rate', self.colrate_entry, '', 'Time Step', self.timestep_entry],
                           ['Temperature', self.temperature_entry, '', 'Barostat', self.barostat_check]]

        self.auto_grid(self.ui_parameters_frame, self.model_grid)

        # SystemBasics
        self.ui_system_frame = tk.LabelFrame(self.canvas, text='System Basics')
        self.ui_system_frame.grid(column=2, row=2)

        # System Study
        self.cutoff_combo = ttk.Combobox(
            self.canvas, textvariable=self.cuttoff)
        self.cutoff_combo.config(
            values=('NoCutoff', 'CutoffNonPeriodic', 'CutoffPeriodic', 'Ewald', 'PME'))


        # Constraints
        self.constr_combo = ttk.Combobox(
            self.canvas, textvariable=self.constr)
        self.constr_combo.config(
            values=('None', 'HBonds', 'HAngles', 'AllBonds'))


        # Rigid watter
        self.water_combo = ttk.Combobox(
            self.canvas, textvariable=self.water)
        self.water_combo.config(values=('True', 'False'))


        # Non bonded methods
        self.nbm_entry = tk.Entry(
            self.canvas, textvariable=self.nbm)


        # Apply grid
        self.model_grid = [['System', self.cutoff_combo, '', 'Non Bonded CuttOff', self.nbm_entry],
                           ['Constraints', self.constr_combo, '', 'Rigid Water', self.water_combo]]

        self.auto_grid(self.ui_system_frame, self.model_grid)

        # simulation parameters

        # Forcefield
        self.ui_forcefield_frame = tk.LabelFrame(
            self.canvas, text='Forcefield Parameters')
        self.ui_forcefield_frame.grid(column=2, row=1)

        # Forcefield
        self.force_combo = ttk.Combobox(
            self.canvas, textvariable=self.forcefield)
        self.force_combo.config(values=(
            'amber96', 'amber99sb', 'amber99sbildn', 'amber99sbnmr', 'amber03', 'amber10'))


        # Water Model
        self.wat_mod_combo = ttk.Combobox(
            self.canvas, textvariable=self.solvent)
        self.wat_mod_combo.config(
            values=('spce', 'tip3p', 'tip4pew', 'tip5p', 'amber10_obc'))


        # Integrator
        self.int_combo = ttk.Combobox(
            self.canvas, textvariable=self.integrator)
        self.int_combo.config(
            values=('Langevin', 'Brownian', 'Verlet', 'VariableVerlet', 'VariableLangevin'))


        # Platform
        self.platform_entry = ttk.Combobox(
            self.canvas, textvariable=self.platform)
        self.platform_entry.config(
            values=('Reference', 'CPU', 'OpenCL', 'CUDA'))


        # Precision
        self.precision_entry = ttk.Combobox(
            self.canvas, textvariable=self.precision)
        self.precision_entry.config(
            values=('single', 'mixed', 'double'))


        # Error Tolerance
        self.tolerance_entry = ttk.Entry(
            self.canvas, textvariable=self.tolerance)

        # Apply grid
        self.model_grid = [['Forcefield', self.force_combo, 'Integrator', self.int_combo],
                           ['', '', '', ''],
                           ['Water Model', self.wat_mod_combo,
                               'Platform', self.platform_entry],
                           ['', '', '', ''],
                           ['Error Tolerance', self.tolerance_entry, 'Precision', self.precision_entry]]

        self.auto_grid(self.ui_forcefield_frame, self.model_grid)

        self.ui_labels['Precision'].grid_remove()
        self.precision_entry.grid_remove()
        
        self.platform_entry.bind("<<ComboboxSelected>>", self._precision_show)

        self.int_combo.bind("<<ComboboxSelected>>", self._set_parameters)

        # Minimiz
        self.ui_minimiz_frame = tk.LabelFrame(
            self.canvas, text='Minimization Parameters')
        self.ui_minimiz_frame.grid(column=1, row=3)

        # Checkbutton Minimization
        self.minimiz_check = ttk.Checkbutton(
            self.canvas, text='yes/no', variable=self.minimiz, command=self._enable_maxsteps)

        # Max minimization Steps
        self.max_steps_entry = ttk.Entry(
            self.canvas, textvariable=self.max_steps, state="disabled")


        # Setvelocities
        self.temp_eq_entry = ttk.Entry(
            self.canvas, textvariable=self.temp_eq)

        # Set temp equilibrium
        self.eqsteps_entry = ttk.Entry(
            self.canvas, textvariable=self.simstep)

        # Apply grid
        self.model_grid = [['Minimization', self.minimiz_check,  'Maximum Steps', self.max_steps_entry],
                           ['Set Velocities\nto Temperature', self.temp_eq_entry, 'Equilibration Steps', self.eqsteps_entry]]
        self.auto_grid(self.ui_minimiz_frame, self.model_grid)

        # Reporters

        self.ui_reporters_frame = tk.LabelFrame(self.canvas, text='Reporters')
        self.ui_reporters_frame.grid(column=2, row=3)

        # Creating Checkbuttons reporters
        reporters = ['dcd', 'pdb', 'time', 'steps', 'speed', 'progress',
                     'potencial_energy', 'kinetic_energy', 'total_energy', 'temperature',
                     'volume', 'density']
        for r in reporters:
            setattr(self, r, tk.StringVar())
            setattr(self, r+"_check", ttk.Checkbutton(self.canvas, text=r))

        # Apply grid
        self.model_grid = [[self.dcd_check, self.pdb_check, self.time_check, self.temperature_check],
                           [self.steps_check, self.speed_check,
                               self.progress_check, self.volume_check],
                           [self.potencial_energy_check, self.kinetic_energy_check, self.total_energy_check, self.density_check]]
        self.auto_grid(self.ui_reporters_frame, self.model_grid)

        # Barostat Settings

        # Barostat frame
        self.ui_barostat_frame = tk.LabelFrame(
            self.canvas, text='Barostat Settings')

        # Pressure
        self.pressure_entry = ttk.Entry(
            self.canvas, textvariable=self.pressure)


        # MD steps
        self.barostat_interval_entry = ttk.Entry(
            self.canvas, textvariable=self.bar_interval)


        # Apply grid
        self.model_grid = [
            ['Pressure (atm)', self.pressure_entry,  'Barostat interval', self.barostat_interval_entry]]
        self.auto_grid(self.ui_barostat_frame, self.model_grid)

        # MD settings

        # MD Frame
        self.ui_md_frame = tk.LabelFrame(self.canvas, text='MD Final Settings')

        # MD interval reporting
        self.interval_entry = ttk.Entry(
            self.canvas, textvariable=self.inter)


        # MD steps
        self.mdsteps_entry = ttk.Entry(
            self.canvas, textvariable=self.simulstep)


        # Apply grid
        self.model_grid = [['MD steps', self.mdsteps_entry, '',
                            '',  'Interval steps to report', self.interval_entry]]
        self.auto_grid(self.ui_md_frame, self.model_grid)

        # Apply grid to frames

        frames = [[self.ui_input_frame, self.ui_forcefield_frame],
                  [self.ui_system_frame, self.ui_parameters_frame],
                  [self.ui_minimiz_frame, self.ui_reporters_frame],
                  [self.ui_barostat_frame, self.ui_md_frame]]
        self.auto_grid(
            self.canvas, frames, resize_columns=(0, 1), sticky='news')

        self.ui_barostat_frame.grid_remove()

        #Setting Default Variables
        self.output.set("~/")
        self.colrate.set(0.002)
        self.tstep.set(1)
        self.temp.set(300)
        self.cutoff_combo.current(0)
        self.constr_combo.current(0)
        self.water_combo.current(1)
        self.nbm.set(1)
        self.force_combo.current(0)
        self.wat_mod_combo.current(1)
        self.int_combo.current(0)
        self.platform_entry.current(0)
        self.precision_entry.current(0)
        self.max_steps.set(1000)
        self.pressure.set(1)
        self.bar_interval.set(30)
        self.inter.set(100)
        self.simulstep.set(1000)




    #Callbacks
    def _set_parameters(self,event):
    
        """Enable or Disable different settings depending on the integrator user choice"""   


        #Enabling all variables 
        self.tolerance_entry.configure(state='normal')
        self.colrate_entry.configure(state='normal')
        self.temperature_entry.configure(state='normal')
        self.barostat_check.configure(state='normal')
        self.timestep_entry.configure(state='normal')
        

        #Disabled parameters dependin on the users integrator choice
        if self.int_combo.get() == 'Langevin':
            self.tolerance_entry.configure(state='disabled')
        if self.int_combo.get() == 'Brownian':
            self.tolerance_entry.configure(state='disabled')
        elif self.int_combo.get() == 'Verlet':
            self.tolerance_entry.configure(state='disabled')
            self.colrate_entry.configure(state='disabled')
            self.temperature_entry.configure(state='disabled')
            self.barostat_check.configure(state='disabled')
        elif self.int_combo.get() == 'VariableLangevin':
            self.timestep_entry.configure(state='disabled')
        elif self.int_combo.get() == 'VariableVerlet':
            self.colrate_entry.configure(state='disabled')
            self.temperature_entry.configure(state='disabled')
            

    def _enable_maxsteps(self):
        """Enable and Disable minimization settings"""
        if self.minimiz.get() is 1:
            self.max_steps_entry.configure(state='normal')
        else:
            self.max_steps_entry.configure(state='disabled')

    def _barostat_show(self):
        """Show or Hide the barostat interface depending whether or not the barostat Checkbutton is pressed"""
        if self.barostat.get() is 1:
            self.ui_barostat_frame.grid()
        else:
            self.ui_barostat_frame.grid_remove()



    def _browse_file(self, var_1, var_2):
        """Browse file and reset frame if an Amber input is found"""

        path = filedialog.askopenfilename(initialdir='~/', filetypes=(
            ('PDB Files', '.pdb'), ('AMBER Files', '.inpcrd'), ('All', '*')))
        var_1.set(path)
        file_path, file_extension = os.path.splitext(path)
        if file_extension == ".inpcrd":
            top_entry = tk.Entry(self.canvas, textvariable=var_2)

            self.model_grid = [['Input File', self.input_entry, self.input_browse],
                               ['Amber Top File', self.top_entry, ''],
                               ['Restart File', self.restart_entry,
                                   self.restart_browse],
                               ['Save at', self.output_entry, self.output_browse]]
            self.auto_grid(self.ui_input_frame, self.model_grid)
            var_2.set(file_path + ".prmtop")

    def _browse_directory(self, var):
        """Search for the path to save the output"""

        path = filedialog.askdirectory(
            initialdir='~/')
        var.set(path)

    def _precision_show(self, event):
        """Showe or Hide precision button depending on the platform user choice"""

        if self.platform_entry.get() == 'CUDA':

            self.ui_labels['Precision'].grid()
            self.precision_entry.grid()

        elif self.platform_entry.get() == 'OpenCL':
            self.ui_labels['Precision'].grid()
            self.precision_entry.grid()

        else:
            self.ui_labels['Precision'].grid_remove()
            self.precision_entry.grid_remove()




    #Script Functions
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
