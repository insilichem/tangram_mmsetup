#!/usr/bin/env python
# encoding: utf-8

# Get used to importing this in your Py27 projects!
from __future__ import print_function, division
# Python stdlib
import os.path
import Tkinter as tk
import tkFileDialog as filedialog
import ttk
# Chimera stuff
import chimera
from chimera import UserError
import chimera.tkgui
from chimera.widgets import MoleculeScrolledListBox
from chimera.baseDialog import ModelessDialog
from chimera import runCommand as rc
# OpenMM package
import simtk.openmm.app as app
# Pdbfixer
from pdbfixer import pdbfixer
# Own
from libplume.ui import PlumeBaseDialog
from core import Controller, Model


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
    model = Model(gui=ui)
    controller = Controller(gui=ui, model=model)
    ui.enter()
    if callback:
        ui.addCallback(callback)


class OpenMM(PlumeBaseDialog):

    """
    To display a new dialog on the interface, you will normally inherit from
    ModelessDialog class of chimera.baseDialog module. Being modeless means
    you can have this dialog open while using other parts of the interface.
    If you don't want this behaviour and instead you want your extension to
    claim exclusive usage, use ModalDialog.
    """

    buttons = ('Save Input', 'Run', 'Close')
    default = None
    help = "https://github.com/insilichem/plume_openmmgui"
    VERSION = '0.0.1'
    VERSION_URL = "https://api.github.com/repos/insilichem/plume_openmmgui/releases/latest"

    def __init__(self, *args, **kwargs):

        # GUI init
        self.title = 'Plume OpenMM GUI'

        # OpenMM variables
        self.entries = ('output', 'forcefield', 'integrator',
                        'parametrize_forc', 'md_reporters', 'stage_constrprot',
                        'stage_constrback', 'advopt_nbm', 'advopt_constr',
                        'stage_reporters', 'advopt_hardware', 'advopt_rigwat',
                        'advopt_precision', 'input_coords', 'input_vel', 'input_box',
                        'checkpoint', 'output_restart', 'positions', 'traj_atoms',
                        'barostat', 'stage_name', 'stage_constrother',
                        'path', 'path_crd', 'path_extinput_top',
                        'path_extinput_crd', 'verbose',
                        'forcefield_external', 'output_projectname')

        self.boolean = ('stage_barostat', 'advopt_barostat', 'stage_minimiz')

        self.reporters = ('Time', 'Steps', 'Speed', 'Progress',
                          'Potencial Energy', 'Kinetic Energy',
                          'Total Energy', 'Temperature', 'Volume', 'Density')

        self.floats = ('tstep', 'stage_pressure',
                       'stage_temp', 'stage_minimiz_tolerance',
                       'advopt_temp', 'advopt_pressure',
                       'advopt_friction', 'advopt_edwalderr', 'advopt_cutoff')

        self.integer = ('output_traj_interval', 'output_stdout_interval',
                        'traj_new_every', 'restart_every',
                        'stage_steps', 'stage_reportevery',
                        'stage_pressure_steps', 'stage_minimiz_maxsteps',
                        'advopt_pressure_steps')

        for e in self.entries:
            setattr(self, 'var_' + e, tk.StringVar())
        for r in self.reporters:
            setattr(self, 'var_' + r, tk.StringVar())
        for f in self.floats:
            setattr(self, 'var_' + f, tk.DoubleVar())
        for i in self.integer:
            setattr(self, 'var_' + i, tk.IntVar())
        for boolean in self.boolean:
            setattr(self, 'var_' + boolean, tk.BooleanVar())

        # Initialise Variables
        self.var_forcefield.set('amber96')
        self.var_integrator.set('LangevinIntegrator')
        self.var_tstep.set(1)
        self.var_output_projectname.set('sys')
        self.var_output_traj_interval.set(1000)
        self.var_output_stdout_interval.set(1000)
        self.var_md_reporters.set('DCD')
        self.var_advopt_friction.set(0.01)
        self.var_advopt_temp.set(300)
        self.var_advopt_barostat.set(False)
        self.var_advopt_pressure.set(1)
        self.var_advopt_edwalderr.set(0.001)
        self.var_advopt_pressure_steps.set(25)
        self.var_advopt_cutoff.set(1)
        self.var_advopt_nbm.set('NoCutoff')
        self.var_advopt_constr.set(None)
        self.var_advopt_hardware.set('Auto')
        self.var_advopt_precision.set('mixed')
        self.var_advopt_rigwat.set('True')
        self.var_verbose.set('True')
        self.set_stage_variables()

        # Misc
        self._basis_set_dialog = None
        self.ui_labels = {}
        self.dict_stage = {}
        self.names = []
        self.stages = []
        self.sanitize = []
        self.additional_force = []
        self.stages_strings = (
            'ui_stage_barostat_steps', 'ui_stage_pressure',
            'ui_stage_temp', 'ui_stage_minimiz_maxsteps',
            'ui_stage_minimiz_tolerance',
            'ui_stage_reportevery', 'ui_stage_steps',
            'ui_stage_name', 'ui_stage_constrother')
        self.check_variables = ['var_stage_minimiz', 'var_stage_barostat',
                                'var_stage_constrprot', 'var_stage_constrback']
        self.style_option = {'padx': 10, 'pady': 10}

        # Fire up
        super(OpenMM, self).__init__(*args, **kwargs)

    def fill_in_ui(self, parent):
        """
        This is the main part of the interface. With this method you code
        the whole dialog, buttons, textareas and everything.
        """

        # Create all frames
        frames = [('ui_input_frame', 'Model Topology'),
                  ('ui_output_frame', 'Output'),
                  ('ui_settings_frame', 'System & Simulation Settings'),
                  ('ui_stage_frame', 'Stages')]
        for attr, text in frames:
            setattr(self, attr, tk.LabelFrame(self.canvas, text=text))

        # Fill frames
        # Fill Input frame
        # Creating tabs
        self.ui_input_note = ttk.Notebook(self.ui_input_frame, padding=5)
        self.ui_tab_1 = tk.Frame(self.ui_input_note)
        self.ui_tab_1.rowconfigure(0, weight=1)
        self.ui_tab_1.columnconfigure(0, weight=1)
        self.ui_tab_2 = tk.Frame(self.ui_input_note)
        self.ui_tab_2.rowconfigure(0, weight=1)
        self.ui_input_note.add(self.ui_tab_1, text="Chimera", state="normal", sticky='news')
        self.ui_input_note.add(self.ui_tab_2, text="External Input", state="normal", sticky='news')
        self.ui_input_note.pack(expand=True, fill='both')

        # Input Frame
        # Tab1
        self.ui_chimera_models = MoleculeScrolledListBox(self.ui_input_frame,
            listbox_selectmode='single', autoselect='single')
        self.ui_chimera_models_options = tk.Button(
            self.ui_input_frame, text="Advanced\nOptions",
            command=lambda: self.Open_window(
                'ui_input_opt_window', self._fill_ui_input_opt_window))
        self.ui_sanitize_chimera_model = tk.Button(
            self.ui_input_frame, text="Sanitize\nModel", command=self.sanitize_model)
        chimera_input_grid = [[self.ui_chimera_models],
                              [(self.ui_chimera_models_options, self.ui_sanitize_chimera_model)]]
        self.auto_grid(self.ui_tab_1, chimera_input_grid, sticky='news', padx=5, pady=5)
        # Tab 2
        self.ui_model_extinput_add = tk.Button(self.ui_input_frame, text='Add\nModel',
            command=self._set_model)
        self.ui_amber_model = tk.Listbox(self.ui_input_frame, height=5,
            listvariable=self.var_path_extinput_top)
        ui_amber_model_options = tk.Button(self.ui_input_frame, text="Advanced\nOptions",
            command=lambda: self.Open_window('ui_input_opt_window', self._fill_ui_input_opt_window))
        extinput_grid = [[self.ui_amber_model],
                         [(ui_amber_model_options, self.ui_model_extinput_add)]]
        self.auto_grid(self.ui_tab_2, extinput_grid, sticky='news', padx=5, pady=5)

        # Output frame
        self.ui_output_projectname_Entry = self.ui_output_entry = tk.Entry(
            self.canvas, textvariable=self.var_output_projectname)
        self.ui_output_reporters_md = ttk.Combobox(
            self.canvas, textvariable=self.var_md_reporters, width=20)
        self.ui_output_reporters_md.config(values=('PDB', 'DCD', 'None'))
        self.ui_output_reporters_realtime = ttk.Combobox(
            self.canvas, textvariable=self.var_verbose, width=20)
        self.ui_output_reporters_realtime.config(values=('True', 'False'))
        self.ui_output_trjinterval_Entry = tk.Entry(
            self.canvas, textvariable=self.var_output_traj_interval, width=8)
        self.ui_output_stdout_interval_Entry = tk.Entry(
            self.canvas, textvariable=self.var_output_stdout_interval, width=8)
        self.ui_output_options = tk.Button(self.canvas, text='Advanced options',
            command=lambda: self.Open_window('ui_output_opt', self._fill_ui_output_opt_window))
        self.ui_output_restart_Entry = tk.Entry(
            self.canvas, textvariable=self.var_output_restart)
        self.ui_output_restart_browse = tk.Button(self.canvas, text='...',
            command=lambda: self._browse_file(self.var_output_restart, 'rst', 'xml'))

        output_grid = [['Project name:', self.ui_output_projectname_Entry],
                       ['Restart file:', self.ui_output_restart_Entry,
                       self.ui_output_restart_browse],
                       ['REPORTERS'],
                       ['Trajectory:', (self.ui_output_reporters_md, 'every',
                        self.ui_output_trjinterval_Entry, 'frames')],
                       ['Progress:', (self.ui_output_reporters_realtime, 'every',
                        self.ui_output_stdout_interval_Entry, 'frames')],
                       ['', self.ui_output_options]]

        self.auto_grid(self.ui_output_frame, output_grid, label_sep='')

        # Settings frame
        self.ui_forcefield_combo = ttk.Combobox(self.canvas, textvariable=self.var_forcefield)
        self.ui_forcefield_combo.config(values=('amber96', 'amber99sb', 'amber99sbildn',
                                                'amber99sbnmr', 'amber03', 'amber10'))
        self.ui_forcefield_add = tk.Button(self.canvas, text='+',
            command=lambda: self.Open_window('ui_add_forcefields', self._fill_ui_add_forcefields))
        self.ui_forcefield_charmmpar = tk.Button(self.canvas, text='...', state='disabled',
            command=lambda: self._browse_file(self.var_parametrize_forc, 'par', ''))
        self.ui_forcefield_charmmpar_entry = tk.Entry(self.canvas,
            textvariable=self.var_parametrize_forc, state='disabled')
        self.ui_integrator = ttk.Combobox(self.canvas, textvariable=self.var_integrator,
            values=('LangevinIntegrator', 'BrownianIntegrator', 'VerletIntegrator',
                    'VariableVerletIntegrator', 'VariableLangevinIntegrator'))
        self.ui_timestep_entry = tk.Entry(self.canvas, textvariable=self.var_tstep)
        self.ui_advanced_options = tk.Button(self.canvas, text='More options',
            command=lambda: self.Open_window('ui_advopt_window', self._fill_ui_advopt_window))

        settings_grid = [['Forcefield', self.ui_forcefield_combo, self.ui_forcefield_add,
                          'Charmm Parameters', (self.ui_forcefield_charmmpar_entry, self.ui_forcefield_charmmpar)],
                         ['Integrator', self.ui_integrator, 'Time Step (fs)', self.ui_timestep_entry, self.ui_advanced_options]]
        self.auto_grid(self.ui_settings_frame, settings_grid)

        # Stages Frame
        self.ui_stages_up = tk.Button(self.canvas, text='^', command=self._move_stage_up)
        self.ui_stages_down = tk.Button(self.canvas, text='v', command=self._move_stage_down)
        self.ui_stages_add = tk.Button(self.canvas, text='+',
            command=lambda: self.Open_window(
                'ui_stages_window', self._fill_ui_stages_window))
        self.ui_stages_listbox = tk.Listbox(self.ui_stage_frame, height=18, background='white')
        self.ui_stages_remove = tk.Button(self.canvas, text='-',
            command=lambda: self._remove_stage('ui_stages_listbox', self.stages))

        stage_frame_widgets = [self.ui_stages_add, self.ui_stages_remove,
                               self.ui_stages_up, self.ui_stages_down]
        for row, item in enumerate(stage_frame_widgets):
            item.grid(in_=self.ui_stage_frame, row=row, column=2,
                      sticky='news', **self.style_option)

        self.ui_stages_listbox.grid(
            in_=self.ui_stage_frame, row=0, column=0, rowspan=4,
            sticky='news', **self.style_option)

        # Grid Frames
        self.ui_input_frame.grid(row=0, column=0, sticky='news', padx=5, pady=5)
        self.ui_output_frame.grid(row=0, column=1, sticky='news', padx=5, pady=5)
        self.ui_stage_frame.grid(row=0, column=3, rowspan=2, sticky='news', padx=5, pady=5)
        self.ui_settings_frame.grid(row=1, columnspan=2, sticky='ew', padx=5, pady=5)

        # Events
        self.ui_input_note.bind("<ButtonRelease-1>", self._forc_param)
        sys = chimera.openModels.addAddHandler(self._chimera_model_handler, None)

    def _chimera_model_handler(self, trigger,arg,new_model):
        for model in chimera.openModels.list():
            if model.id != new_model[0].id:
                chimera.openModels.remove(model)

    def _forc_param(self, event):
        """
        Enable or Disable forcefield option
        depending on user input choice
        """
        if self.ui_input_note.index(self.ui_input_note.select()) == 0:
            self.ui_forcefield_combo.configure(state='normal')
            self.ui_forcefield_charmmpar_entry.configure(state='disabled')
            self.ui_forcefield_charmmpar.configure(state='disabled')
            self.ui_forcefield_add.configure(state='normal')
        elif self.ui_input_note.index(self.ui_input_note.select()) == 1:
            self.ui_forcefield_combo.configure(state='disabled')
            self.ui_forcefield_charmmpar_entry.configure(state='normal')
            self.ui_forcefield_charmmpar.configure(state='normal')
            self.ui_forcefield_add.configure(state='disabled')

    # Main Window Callbacks

    def _set_model(self):
        """
        Open and include PSF file or Prmtop.
        In last case, add the adjacent inpcrd file.
        """

        topology_path = filedialog.askopenfilename(initialdir='~/', filetypes=(
            ('Amber Top', '*.prmtop'), ('PSF File', '*.psf')))
        if topology_path:
            path_name, extension = os.path.splitext(topology_path)
            file_name = os.path.basename(path_name).rstrip('/')
            self.ui_amber_model.delete(0, 'end')
            self.var_path_extinput_top.set(topology_path)
            self.ui_amber_model.select_set(0)
            self.var_path.set(self.ui_amber_model.get(0))
            if extension == '.prmtop':
                crd_name = file_name + '.inpcrd'
                crd_path = os.path.join(os.path.dirname(topology_path), crd_name)
                if os.path.isfile(crd_path):
                    self.ui_amber_model.insert(
                        'end', crd_path)
                    self.var_positions.set(self.ui_amber_model.get(1))
                else:
                    positions_path = filedialog.askopenfilename(initialdir='~/', filetypes=(
                    ('AMBER positions', '*.inpcrd'), ('Position File', '*.coor')))
                    if os.path.isfile(positions_path):
                        self.ui_amber_model.insert(
                        'end', positions_path)
                        self.var_positions.set(self.ui_amber_model.get(1))


    def _remove_stage(self, listbox, List):
        """
        Remove the selected stage from the stage listbox
        """
        widget = getattr(self, listbox)
        selection = widget.curselection()
        if selection:
            selection_index = selection[0]
            widget.delete(selection)
            del List[selection_index]


    def _move_stage_up(self):
        """
        Move one position upwards the selected stage
        """

        if self.ui_stages_listbox.curselection():
            i = int(self.ui_stages_listbox.curselection()[0])
            if i != 0:
                move_item = self.ui_stages_listbox.get(i-1)
                self.ui_stages_listbox.delete(i-1)
                self.ui_stages_listbox.insert(i, move_item)
                move_item = self.stages[i-1]
                del self.stages[i-1]
                self.stages.insert(i, move_item)

    def _move_stage_down(self):
        """
        Move one position downwards the selected stage
        """

        if self.ui_stages_listbox.curselection():
            i = (self.ui_stages_listbox.curselection()[0])
            if i != len(self.ui_stages_listbox.get(0, 'end')) - 1:
                move_item = self.ui_stages_listbox.get(i+1)
                self.ui_stages_listbox.delete(i+1)
                self.ui_stages_listbox.insert(i, move_item)
                move_item = self.stages[i+1]
                del self.stages[i+1]
                self.stages.insert(i, move_item)


    def _fill_ui_output_opt_window(self):
        """
        Opening  report options
        """
        # Create window
        self.ui_output_opt = tk.Toplevel()
        self.Center(self.ui_output_opt)
        self.ui_output_opt.title("Output Options")

        # Create frame and lframe
        self.ui_output_opt_frame = tk.Frame(self.ui_output_opt)
        self.ui_output_opt_frame.pack()
        self.ui_output_opt_frame_label = tk.LabelFrame(
            self.ui_output_opt_frame, text='Advanced Output Options')
        self.ui_output_opt_frame_label.grid(
            row=0, column=0, **self.style_option)

        # Create Widgets
        self.ui_output_opt_traj_new_every_Entry = tk.Entry(
            self.ui_output_opt_frame, textvariable=self.var_traj_new_every)
        self.ui_output_opt_traj_atom_subset_Entry = tk.Entry(
            self.ui_output_opt_frame, textvariable=self.var_traj_atoms)
        self.ui_output_opt_restart_every_Entry = tk.Entry(
            self.ui_output_opt_frame, textvariable=self.var_restart_every)



        # Grid them
        output_opt_grid = [['Trajectory\nNew Every', self.ui_output_opt_traj_new_every_Entry],
                           ['Trajectory\nAtom Subset', self.ui_output_opt_traj_atom_subset_Entry],
                           ['Restart Every', self.ui_output_opt_restart_every_Entry]]
        self.auto_grid(self.ui_output_opt_frame_label, output_opt_grid)

    def _fill_ui_stages_window(self):
        """
        Create widgets on TopLevel Window to set different
        stages inside our Molecular Dinamic Simulation
        """

        # creating window
        self.ui_stages_window = tk.Toplevel()
        self.Center(self.ui_stages_window)
        self.ui_stages_window.title("MD Stages")

        # Creating tabs---> How to fix (tried to do it with list not working)
        ui_note = ttk.Notebook(self.ui_stages_window)
        titles = ["Stage", "Temperature & Pressure",
                  "Constrains & Minimization", "MD Settings"]
        for i, title in enumerate(titles, 1):
            setattr(self, 'ui_tab_' + str(i), tk.Frame(ui_note))
            ui_note.add(
                getattr(self, 'ui_tab_' + str(i)), text=title, state="normal")
        ui_note.pack()

        # tab_1
        self.ui_stage_name_lframe = tk.LabelFrame(
            self.ui_tab_1, text='Stage Main Settings')
        self.ui_stage_name_lframe.pack(expand=True, fill='both')

        self.ui_stage_name_Entry = tk.Entry(
            self.ui_tab_1, textvariable=self.var_stage_name)
        self.ui_stage_close = tk.Button(
            self.ui_tab_1, text='Close', command=self._close_ui_stages_window)
        self.ui_stage_save_Button = tk.Button(
            self.ui_tab_1, text='Save and Close',
            command=self._save_ui_stages_window)

        stage_grid = [['Stage Name', self.ui_stage_name_Entry],
                      ['', self.ui_stage_close, self.ui_stage_save_Button]]
        self.auto_grid(self.ui_stage_name_lframe, stage_grid)

        # tab_2
        self.ui_stage_temp_lframe = tk.LabelFrame(
            self.ui_tab_2, text='Temperature')
        self.ui_stage_pressure_lframe = tk.LabelFrame(
            self.ui_tab_2, text='Pressure')
        frames = [[self.ui_stage_temp_lframe, self.ui_stage_pressure_lframe]]
        self.auto_grid(self.ui_tab_2, frames)

        self.ui_stage_temp_Entry = tk.Entry(
            self.ui_tab_2, textvariable=self.var_stage_temp)
        self.temp_grid = [['Stage Temperature (K)', self.ui_stage_temp_Entry]]
        self.auto_grid(self.ui_stage_temp_lframe, self.temp_grid)

        self.ui_stage_pressure_Entry = tk.Entry(
            self.ui_tab_2, state='disabled', textvariable=self.var_stage_pressure)
        self.ui_stage_barostat_steps_Entry = tk.Entry(
            self.ui_tab_2, state='disabled', textvariable=self.var_stage_pressure_steps)
        self.ui_stage_barostat_check = ttk.Checkbutton(
            self.ui_tab_2, text="Barostat", variable=self.var_stage_barostat,
            onvalue=True, offvalue=False,
            command=lambda: self._check_settings(
                self.var_stage_barostat, True, self.ui_stage_pressure_Entry,
                self.ui_stage_barostat_steps_Entry))
        self.pres_grid = [[self.ui_stage_barostat_check, ''],
                          ['Pressure (bar)', self.ui_stage_pressure_Entry],
                          ['Barostat Every (frames)', self.ui_stage_barostat_steps_Entry]]
        self.auto_grid(self.ui_stage_pressure_lframe, self.pres_grid)

        # Tab3
        self.ui_stage_constr_lframe = tk.LabelFrame(
            self.ui_tab_3, text='Constrained Atoms')
        self.ui_stage_minim_lframe = tk.LabelFrame(
            self.ui_tab_3, text='Minimize:')
        frames = [[self.ui_stage_constr_lframe, self.ui_stage_minim_lframe]]
        self.auto_grid(self.ui_tab_3, frames)

        self.ui_stage_constrprot_check = ttk.Checkbutton(
            self.ui_tab_3, text='Protein', variable=self.var_stage_constrprot,
            onvalue='Protein', offvalue='')
        self.ui_stage_constrback_check = ttk.Checkbutton(
            self.ui_tab_3, text='Backbone', variable=self.var_stage_constrback,
            onvalue='Backbone', offvalue='')
        self.ui_stage_constrother_Entry = tk.Entry(
            self.ui_tab_3, width=20, textvariable=self.var_stage_constrother)
        constraints_grid = [[self.ui_stage_constrprot_check],
                            [self.ui_stage_constrback_check],
                            ['Other', self.ui_stage_constrother_Entry]]
        self.auto_grid(self.ui_stage_constr_lframe, constraints_grid)

        self.ui_stage_minimiz_check = ttk.Checkbutton(
            self.ui_tab_3, text="Minimization",
            variable=self.var_stage_minimiz, offvalue=False,
            onvalue=True, command=lambda: self._check_settings(
                self.var_stage_minimiz, True,
                self.ui_stage_minimiz_maxsteps_Entry,
                self.ui_stage_minimiz_tolerance_Entry))
        self.ui_stage_minimiz_maxsteps_Entry = tk.Entry(
            self.ui_tab_3, state='disabled',
            textvariable=self.var_stage_minimiz_maxsteps)
        self.ui_stage_minimiz_tolerance_Entry = tk.Entry(
            self.ui_tab_3, state='disabled',
            textvariable=self.var_stage_minimiz_tolerance)

        minimiz_grid = [[self.ui_stage_minimiz_check, ''],
                        ['Max Steps',
                         self.ui_stage_minimiz_maxsteps_Entry],
                        ['Tolerance', self.ui_stage_minimiz_tolerance_Entry]]
        self.auto_grid(self.ui_stage_minim_lframe, minimiz_grid)

        # Tab 4
        self.ui_stage_mdset_lframe = tk.LabelFrame(self.ui_tab_4)
        self.ui_stage_mdset_lframe.pack(expand=True, fill='both')

        self.ui_stage_steps_Entry = tk.Entry(
            self.ui_tab_4, textvariable=self.var_stage_steps)
        self.ui_stage_reporters_combo = ttk.Combobox(
            self.ui_tab_4, textvariable=self.var_stage_reporters)
        self.ui_stage_reporters_combo.config(values=('PDB', 'DCD', 'None'))
        self.ui_stage_reportevery_Entry = tk.Entry(
            self.ui_tab_4, textvariable=self.var_stage_reportevery)

        self.stage_md = [['MD Steps', self.ui_stage_steps_Entry],
                         ['Trajectory Reporters', self.ui_stage_reporters_combo],
                         ['Every (frames)', self.ui_stage_reportevery_Entry]]
        self.auto_grid(self.ui_stage_mdset_lframe, self.stage_md)
        self.ui_stages_window.mainloop()

    def _save_ui_stages_window(self):
        """
        Save stage on the main listbox while closing the window
        reset all variables and create a dict with all stages
        """
        if not self.var_stage_name.get():
            self.ui_stage_name_Entry.configure(background='red')
        else:
            self.ui_stage_name_Entry.configure(background='white')
            self.ui_stages_listbox.insert('end', self.var_stage_name.get())
            self.ui_stages_window.withdraw()

            self.create_stage_dict()

            # Reset Variables
            for item in self.stages_strings:
                getattr(self, item + '_Entry').delete(0, 'end')
            for item in self.check_variables:
                getattr(self, item).set(False)
            self.set_stage_variables()

    def create_stage_dict(self):

            # Create Stage Dictionary for output
            stage_dict = setattr(self, self.var_stage_name.get(), {})
            # Save constraints as a list
            constraint_variables = (self.var_stage_constrback.get(),
                                    self.var_stage_constrprot.get(),
                                    self.var_stage_constrother.get())
            constraints= []
            for item in constraint_variables:
                if item:
                    constraints.append(item)
            if not constraints:
                constraints = None

            stage_dict = {
                'name': self.var_stage_name.get(),
                'temperature': self.var_stage_temp.get(),
                'pressure': self.var_stage_pressure.get(),
                'barostat_interval': self.var_stage_pressure_steps.get(),
                'barostat': self.var_stage_barostat.get(),
                'constrained_atoms': constraints,
                'minimization': self.var_stage_minimiz.get(),
                'minimization_max_iterations': self.var_stage_minimiz_maxsteps.get(),
                'minimization_tolerance': self.var_stage_minimiz_tolerance.get(),
                'trajectory': self.var_stage_reporters.get(),
                'steps': self.var_stage_steps.get(),
                'trajectory_every': None if self.var_stage_reporters.get() == 'None' else self.var_stage_reportevery.get() }
            self.stages.append(stage_dict)


    def _close_ui_stages_window(self):
        """
        Close window ui_stages_window and reset all variables
        """
        self.ui_stages_window.withdraw()
        for item in self.stages_strings:
            getattr(self, item + '_Entry').delete(0, 'end')
        for item in self.check_variables:
            getattr(self, item).set(False)
        self.set_stage_variables()

    def _fill_ui_advopt_window(self):
        """
        Create widgets on TopLevel Window to set different general
        advanced optinons inside our Molecular Dinamic Simulation
        """

        # Create TopLevel window
        self.ui_advopt_window = tk.Toplevel()
        self.Center(self.ui_advopt_window)
        self.ui_advopt_window.title("Advanced Options")

        # Create Tabs
        ui_note = ttk.Notebook(self.ui_advopt_window)
        titles = ["Conditions", "OpenMM System Options", "Hardware"]
        for i, title in enumerate(titles, 1):
            setattr(self, 'ui_tab_' + str(i), tk.Frame(ui_note))
            ui_note.add(
                getattr(self, 'ui_tab_' + str(i)), text=title, state="normal")
        ui_note.pack()

        # tab_1
        self.ui_advopt_conditions_lframe = tk.LabelFrame(
            self.ui_tab_1, text='Set Conditions')
        self.ui_advopt_conditions_lframe.pack(expand=True, fill='both')
        self.ui_advopt_friction_Entry = tk.Entry(
            self.ui_tab_1, textvariable=self.var_advopt_friction)
        self.ui_advopt_temp_Entry = tk.Entry(
            self.ui_tab_1, textvariable=self.var_advopt_temp)
        self.ui_advopt_barostat_check = ttk.Checkbutton(
            self.ui_tab_1, text="Barostat", variable=self.var_advopt_barostat,
            onvalue=True, offvalue=False,
            command=lambda: self._check_settings(
                self.var_advopt_barostat, True,
                self.ui_advopt_pressure_Entry,
                self.ui_advopt_barostat_steps_Entry))
        self.ui_advopt_pressure_Entry = tk.Entry(
            self.ui_tab_1, state='disabled',
            textvariable=self.var_advopt_pressure)
        self.ui_advopt_barostat_steps_Entry = tk.Entry(
            self.ui_tab_1, state='disabled',
            textvariable=self.var_advopt_pressure_steps)

        advopt_grid = [['Friction (1/ps)', self.ui_advopt_friction_Entry],
                       ['Temperature (K)', self.ui_advopt_temp_Entry],
                       [self.ui_advopt_barostat_check, ''],
                       ['Pressure (bar)', self.ui_advopt_pressure_Entry],
                       ['Maximum Steps', self.ui_advopt_barostat_steps_Entry]]
        self.auto_grid(self.ui_advopt_conditions_lframe, advopt_grid)

        # tab_2
        self.ui_advopt_system_lframe = tk.LabelFrame(
            self.ui_tab_2, text='Set System Options')
        self.ui_advopt_system_lframe.pack(expand=True, fill='both')

        self.ui_advopt_nbm_combo = ttk.Combobox(
            self.ui_tab_2, textvariable=self.var_advopt_nbm)
        self.ui_advopt_nbm_combo.config(
            values=('NoCutoff', 'CutoffNonPeriodic', 'CutoffPeriodic', 'Ewald', 'PME'))
        self.ui_advopt_cutoff_Entry = tk.Entry(
            self.ui_tab_2, textvariable=self.var_advopt_cutoff)
        self.ui_advopt_ewalderr_Entry = tk.Entry(
            self.ui_tab_2, textvariable=self.var_advopt_edwalderr, state='disabled')
        self.ui_advopt_constr_combo = ttk.Combobox(
            self.ui_tab_2, textvariable=self.var_advopt_constr)
        self.ui_advopt_constr_combo.config(
            values=('None', 'HBonds', 'HAngles', 'AllBonds'))
        self.ui_advopt_rigwat_combo = ttk.Combobox(
            self.ui_tab_2, textvariable=self.var_advopt_rigwat)
        self.ui_advopt_rigwat_combo.config(
            values=('True', 'False'))

        advopt_grid = [['Non Bonded Method', self.ui_advopt_nbm_combo],
                       ['Ewald Tolerance',
                        self.ui_advopt_ewalderr_Entry],
                       ['Non Bonded Cutoff (nm)', self.ui_advopt_cutoff_Entry],
                       ['Constraints', self.ui_advopt_constr_combo],
                       ['Rigid Water', self.ui_advopt_rigwat_combo]]
        self.auto_grid(self.ui_advopt_system_lframe, advopt_grid)
        # Events
        self.ui_advopt_nbm_combo.bind(
            "<<ComboboxSelected>>", self._PME_settings)

        # Tab3

        self.ui_advopt_hardware_lframe = tk.LabelFrame(
            self.ui_tab_3, text='Platform')
        self.ui_advopt_hardware_lframe.pack(expand=True, fill='both')

        self.ui_advopt_platform_combo = ttk.Combobox(
            self.ui_tab_3, textvariable=self.var_advopt_hardware)
        self.ui_advopt_platform_combo.config(values=('Auto', 'CPU', 'OpenCL', 'CUDA'))
        self.ui_advopt_precision_combo = ttk.Combobox(
            self.ui_tab_3, textvariable=self.var_advopt_precision)
        self.ui_advopt_precision_combo.config(
            values=('single', 'mixed', 'double'))

        advopt_grid_hardware = [['', ''],
                                ['Platform',
                                 self.ui_advopt_platform_combo],
                                ['Precision', self.ui_advopt_precision_combo]]
        self.auto_grid(
            self.ui_advopt_hardware_lframe, advopt_grid_hardware)

    def _PME_settings(self, event):
        """
        Enable or Disable Edwald Error Entry when
        CutoffNonPeriodic Combobox is selected
        """
        if self.var_advopt_nbm.get() == 'PME':
            self.ui_advopt_edwalderr_Entry.configure(state='normal')
            self.var_advopt_edwalderr.set(0.001)
        else:
            self.ui_advopt_edwalderr_Entry.configure(state='disabled')
            self.var_advopt_edwalderr.set(0.001)

    def _fill_ui_input_opt_window(self):

        # Create TopLevel window
        self.ui_input_opt_window = tk.Toplevel()
        self.Center(self.ui_input_opt_window)
        self.ui_input_opt_window.title("Advanced Options")
        # Create lframe
        self.ui_advopt_input_opt_lframe = tk.LabelFrame(
            self.ui_input_opt_window, text='Initial Files')
        self.ui_advopt_input_opt_lframe.pack(expand=True, fill='both')
        # Fill lframe
        self.ui_input_coords_Entry = tk.Entry(
            self.ui_input_opt_window, textvariable=self.var_input_coords)
        self.ui_input_coords_browse = tk.Button(
            self.ui_input_opt_window, text='...',
            command=lambda: self._browse_file(self.var_input_coords, 'inpcrd', 'crd'))
        self.ui_input_vel_Entry = tk.Entry(
            self.ui_input_opt_window, textvariable=self.var_input_vel)
        self.ui_input_vel_browse = tk.Button(
            self.ui_input_opt_window, text='...',
            command=lambda: self._browse_file(self.var_input_vel, 'vel'))
        self.ui_input_box_Entry = tk.Entry(
            self.ui_input_opt_window, textvariable=self.var_input_box)
        self.ui_input_box_browse = tk.Button(
            self.ui_input_opt_window, text='...',
            command=lambda: self._browse_file(self.var_input_box, 'xsc', 'csv'))
        self.ui_input_checkpoint_Entry = tk.Entry(
            self.ui_input_opt_window, textvariable=self.var_input_restart)
        self.ui_input_checkpoint_browse = tk.Button(
            self.ui_input_opt_window, text='...',
            command=lambda: self._browse_file(self.var_checkpoint, 'rst', 'xml', '*'))
        input_grid = [['Coordinates', self.ui_input_coords_Entry, self.ui_input_coords_browse],
                      ['Velocities', self.ui_input_vel_Entry, self.ui_input_vel_browse],
                      ['Box vectors', self.ui_input_box_Entry, self.ui_input_box_browse],
                      ['From checkpoint', self.ui_input_checkpoint_Entry, self.ui_input_checkpoint_browse]]

        self.auto_grid(self.ui_advopt_input_opt_lframe, input_grid)

    def _fill_ui_add_forcefields(self):
        # Create TopLevel window
        self.ui_add_forcefields = tk.Toplevel()
        self.Center(self.ui_add_forcefields)
        self.ui_add_forcefields.title("External Forcefield")
        # Create lframe
        self.ui_add_forcefields_lframe = tk.LabelFrame(
            self.ui_add_forcefields, text='Add your Own Forcefield')
        self.ui_add_forcefields_lframe.pack(expand=True, fill='both')
        # Fill lframe
        self.ui_add_forcefields_List = tk.Listbox(
            self.ui_add_forcefields, listvariable=self.var_forcefield_external)
        self.ui_add_forcefields_include = tk.Button(
            self.ui_add_forcefields, text='+',
            command=self.create_extforcefield_add)
        self.ui_add_forcefields_remove = tk.Button(
            self.ui_add_forcefields, text='-',
            command=lambda: self._remove_stage('ui_add_forcefields_List', self.additional_force))
        add_forcefields_grid = [[
            'Xml:\nFrcmod', self.ui_add_forcefields_List,
            (self.ui_add_forcefields_include, self.ui_add_forcefields_remove)]]
        self.auto_grid(
            self.ui_add_forcefields_lframe, add_forcefields_grid)
        self.ui_add_forcefields_List.configure(width=20)

    def create_extforcefield_add(self):
        path = filedialog.askopenfilename(initialdir='~/', filetypes=(
            ('Xml File', '*.xml'), ('Frcmod File', '*.frcmod'),('gaff.mol2 File', '*.gaff.mol2')))
        if path:
            self.ui_add_forcefields_List.insert('end', path)
            self.additional_force.append(path)


    def _check_settings(self, var, onvalue, *args):
        """
        Enable or Disable several settings
        depending on other Checkbutton value

        Parameters
        ----------
        var: tk widget Checkbutton where we set an options
        onvalue: onvalue Checkbutton normally set as 1
        args...: tk widgets to enable or disabled

        """
        if var.get() == onvalue:
            for entry in args:
                entry.configure(state='normal')
        else:
            for entry in args:
                entry.configure(state='disabled')

    # Sanitize functions

    def sanitize_model(self):
        # Each model in a single model
        #Getting molecule attributes
        model = self.ui_chimera_models.getvalue()
        modelfile_path = getattr(model, 'openedAs', (model.name,))[0]
        output_file = '{0[0]}{1}{0[1]}'.format(os.path.splitext(modelfile_path), '_fixed')
        chimera.pdbWrite([model], chimera.Xform(), output_file)
        self.fix_pdb(output_file, out=output_file)
        m = chimera.openModels.open(output_file, sameAs=model, temporary=True)[0]
        m.name = model.name + ' - Fixed'
        self.ui_chimera_models.selection_clear()
        self.ui_chimera_models.selection_set(chimera.openModels.list().index(m))
        model.display = False

    def fix_pdb(self, infile, out=None, pH=7):
        with open(infile, 'r') as f:
            fixer = pdbfixer.PDBFixer(pdbfile=f)
        fixer.findMissingResidues()
        fixer.findMissingAtoms()
        fixer.addMissingAtoms()
        fixer.addMissingHydrogens(pH=pH)
        if out is None:
            out = '{0[0]}{1}{0[1]}'.format(os.path.splitext(infile), '_fixed')
        with open(out, 'w') as f:
            app.PDBFile.writeFile(fixer.topology, fixer.positions, f)

    # Callbacks

    def _browse_file(self, var, *filetypes):
        """
        Browse file path

        Parameters
        ----------
        var= Interface entry widget where we wish insert the browse file.
        file_type1 = 1st type of file to open
        file_type2 = 2nd  type of file to open
        """
        path = filedialog.askopenfilename(initialdir='~/',
            filetypes=[(ft, '*.' + ft) for ft in filetypes])
        if path:
            var.set(path)

    def _browse_directory(self, var):
        """
        Search for the path to save the output

        Parameters
        ----------
        var= Interface entry widget where we wish insert the path file.

        """

        path_dir = filedialog.askdirectory(initialdir='~/')
        if path_dir:
            var.set(path_dir)

    # Script Functions
    def Open_window(self, window, fill_function):
        """
        Get sure the window is not opened
        a second time

        Parameters:
        window: window to open
        fill_function: fillin function for window
        """
        try:
            var_window = window
            var_window.state()
            if window == self.ui_stages_window:
                self.set_stage_variables()
                self.ui_stage_minimiz_tolerance_Entry.configure(state='disabled')
                self.ui_stage_minimiz_maxsteps_Entry.configure(state = 'disabled')
                self.ui_stage_barostat_steps_Entry.configure(state='disabled')
                self.ui_stage_pressure_Entry.configure(state='disabled')
            var_window.deiconify()
        except (AttributeError, tk.TclError):
            return fill_function()

    def Center(self, window):
        """
        Update "requested size" from geometry manager
        """
        window.update_idletasks()
        x = (window.winfo_screenwidth() -
             window.winfo_reqwidth()) / 2
        y = (window.winfo_screenheight() -
             window.winfo_reqheight()) / 2
        window.geometry("+%d+%d" % (x, y))
        window.deiconify()

    def Close(self):
        """
        Default! Triggered action if you click on the Close button
        """
        global ui
        ui = None
        ModelessDialog.Close(self)
        self.destroy()

    def set_stage_variables(self):
        self.var_stage_temp.set(300)
        self.var_stage_minimiz.set(False)
        self.var_stage_minimiz_maxsteps.set(10000)
        self.var_stage_minimiz_tolerance.set(0.0001)
        self.var_stage_constrprot.set('')
        self.var_stage_constrback.set('')
        self.var_stage_constrother.set('')
        self.var_stage_barostat.set(False)
        self.var_stage_pressure.set(self.var_advopt_pressure.get())
        self.var_stage_pressure_steps.set(self.var_advopt_pressure_steps.get())
        self.var_stage_reporters.set(self.var_md_reporters.get())
        self.var_stage_reportevery.set(1000)
        self.var_stage_steps.set(10000)

