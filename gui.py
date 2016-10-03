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
        'height': '10',
        'width': '5',
        'background': 'white',

    },
    tk.Button: {
        'borderwidth': 1,
        'highlightthickness': 0,

    },
    tk.Checkbutton: {
        'highlightbackground': chimera.tkgui.app.cget('bg'),
        'activebackground': chimera.tkgui.app.cget('bg'),
    },
    MoleculeScrolledListBox: {
        'listbox_borderwidth': 1,
        'listbox_background': 'white',
        'listbox_highlightthickness': 0,
        'listbox_height': 10,
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
    model = Model(gui=ui)
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
        self.title = 'Plume OpenMM'

        # OpenMM variables
        self.entries = ('output', 'forcefield', 'integrator', 'external_forc', 'parametrize_forc',
                        'md_reporters', 'stage_constrprot', 'stage_constrback',
                        'advopt_nbm', 'advopt_constr', 'advopt_rigwat', 'stage_dcd',
                        'advopt_hardware', 'advopt_precision', 'input_vel', 'input_box',
                        'input_checkpoint', 'positions', 'traj_atoms', 'barostat',
                        'stage_name', 'stage_constrother', '_path', '_path_crd',
                        'path_extinput_top', 'path_extinput_crd', 'verbose',
                        'advopt_cutoff')
        self.boolean = ('stage_barostat', 'advopt_barostat', 'stage_minimiz')


        self.reporters = ('Time', 'Steps', 'Speed', 'Progress', 'Potencial Energy', 'Kinetic Energy',
                          'Total Energy', 'Temperature', 'Volume', 'Density')

        self.floats = ('tstep', 'stage_pressure', 'stage_temp','stage_minimiz_tolerance',
                       'advopt_temp', 'advopt_pressure', 'advopt_friction','advopt_edwalderr')

        self.integer = ('output_traj_interval', 'output_stdout_interval', 'traj_new_every', 'restart_every',
                         'stage_steps', 'stage_reportevery', 'stage_pressure_steps', 'stage_minimiz_maxsteps',
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

        # Misc
        self._basis_set_dialog = None
        self.ui_labels = {}
        self.input_option = {'padx': 10, 'pady': 10}
        self.names = []
        self.stage_variables = ('var_stage_barostat', 'var_stage_pressure_steps', 'var_stage_constrprot',
                                'var_stage_constrback', 'var_stage_constrother', 'var_stage_minimiz',
                                'var_stage_minimiz_maxsteps', 'var_stage_minimiz_tolerance', 
                                'var_stage_name', 'var_stage_pressure', 'var_stage_dcd', 
                                'var_stage_reportevery', 'var_stage_steps', 'var_stage_temp')
                                
                                
        self.stages_strings = (
                    'ui_stage_barostat_steps', 'ui_stage_pressure',
                    'ui_stage_temp', 'ui_stage_minimiz_maxsteps',
                    'ui_stage_minimiz_tolerance',
                    'ui_stage_reportevery', 'ui_stage_steps',
                    'ui_stage_name', 'ui_stage_constrother')
        self.check_variables = ['var_stage_minimiz', 'var_stage_dcd', 'var_stage_barostat',
                                'var_stage_constrprot', 'var_stage_constrback']

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
        frames = [('ui_input_frame', 'Model Topology'), ('ui_output_frame', 'Output'),
                  ('ui_settings_frame', 'Settings'), ('ui_stage_frame', 'Stages')]
        for frame in frames:
            for item in frames:
                setattr(
                    self, item[0], tk.LabelFrame(self.canvas, text=item[1]))

        # Fill frames
        # Fill Input frame
        # Creating tabs
        self.ui_note = ttk.Notebook(self.ui_input_frame)
        self.ui_tab_1 = tk.Frame(self.ui_note)
        self.ui_tab_2 = tk.Frame(self.ui_note)
        self.ui_note.add(self.ui_tab_1, text="Chimera", state="normal")
        self.ui_note.add(self.ui_tab_2, text="External Input", state="normal")
        self.ui_note.pack(expand=True, fill='both')

        # Fill input frame
        # Create and grid tab 1, 2 and 3

        # self.model_pdb_add = tk.Button(
        # self.ui_input_frame, text='Set Model',
        # command=self._include_pdb_model)
        self.ui_model_pdb_show = MoleculeScrolledListBox(self.ui_input_frame)

        self.ui_model_pdb_options = tk.Button(
            self.ui_input_frame, text="Advanced\nOptions", command=self._fill_ui_input_opt_window)
        self.ui_model_pdb_sanitize = tk.Button(
            self.ui_input_frame, text="Sanitize\nModel")
        self.pdb_grid = [[self.ui_model_pdb_show],
                         [(self.ui_model_pdb_options, self.ui_model_pdb_sanitize)]]
        #[self.model_pdb_add]]
        self.auto_grid(self.ui_tab_1, self.pdb_grid)

        self.ui_model_extinput_add = tk.Button(
            self.ui_input_frame, text='Set Model', command=self._include_amber_model)
        self.ui_model_extinput_show = tk.Listbox(
            self.ui_input_frame, listvariable=self.var_path_extinput_top)
        self.ui_model_extinput_options = tk.Button(
            self.ui_input_frame, text="Advanced\nOptions", command=self._fill_ui_input_opt_window)
        self.ui_model_extinput_sanitize = tk.Button(
            self.ui_input_frame, text="Sanitize\nModel")
        self.extinput_grid = [[self.ui_model_extinput_show],
                              [(self.ui_model_extinput_options,
                                self.ui_model_extinput_sanitize)],
                              [self.ui_model_extinput_add]]
        self.auto_grid(self.ui_tab_2, self.extinput_grid)

        # Fill Output frame
        self.ui_output_entry = tk.Entry(self.canvas, textvariable=self.var_output)
        self.ui_output_browse = tk.Button(
            self.canvas, text='...', command=lambda: self._browse_directory(self.var_output))
        self.ui_output_reporters_md = ttk.Combobox(
            self.canvas, textvariable=self.var_md_reporters)
        self.ui_output_reporters_md.config(values=('PDB', 'DCD', 'None'))
        self.ui_output_addreporters_realtime = tk.Button(
            self.canvas, text='+', command=self._fill_ui_stdout_window)
        self.ui_output_reporters_realtime = tk.Listbox(
            self.ui_output_frame)
        self.ui_output_trjinterval_Entry = tk.Entry(
            self.canvas, textvariable=self.var_output_traj_interval)
        self.ui_output_stdout_interval_Entry = tk.Entry(
            self.canvas, textvariable=self.var_output_stdout_interval)
        self.ui_output_options = tk.Button(
            self.canvas, text='Opt', command=self._fill_ui_output_opt_window)

        self.output_grid = [['Save at', self.ui_output_entry, self.ui_output_browse],
                            ['Trajectory\nReporters',  self.ui_output_reporters_md],
                            ['Real Time\nReporters', self.ui_output_reporters_realtime,
                                self.ui_output_addreporters_realtime],
                            ['Trajectory\nEvery',
                                self.ui_output_trjinterval_Entry],
                            ['Stdout \nEvery', self.ui_output_stdout_interval_Entry,
                             self.ui_output_options]]
        self.auto_grid(self.ui_output_frame, self.output_grid)

        # Fill Settings frame
        self.ui_forcefield_combo = ttk.Combobox(
            self.canvas, textvariable=self.var_forcefield)
        self.ui_forcefield_combo.config(values=(
            'amber96', 'amber99sb', 'amber99sbildn', 'amber99sbnmr', 'amber03', 'amber10'))
        self.ui_forcefield_add = tk.Button(
            self.canvas, text='+')
        self.ui_forcefield_frcmod = tk.Button(
            self.canvas, text='...', command=lambda: self._browse_file(self.var_external_forc, 'frcmod', ''))
        self.ui_forcefield_charmmpar = tk.Button(
            self.canvas, text='...', command=lambda: self._browse_file(self.var_parametrize_forc, 'par', ''))
        self.ui_forcefield_frcmod_entry = tk.Entry(
            self.canvas, textvariable=self.var_external_forc)
        self.ui_forcefield_charmmpar_entry = tk.Entry(
            self.canvas, textvariable=self.var_parametrize_forc, state='disabled')
        self.ui_integrator = ttk.Combobox(
            self.canvas, textvariable=self.var_integrator)
        self.ui_integrator.config(
            values=('Langevin', 'Brownian', 'Verlet', 'VariableVerlet', 'VariableLangevin'))
        self.ui_timestep_entry = tk.Entry(
            self.canvas, textvariable=self.var_tstep, )
        self.ui_advanced_options = tk.Button(
            self.canvas, text='Opt', command=self._fill_ui_advopt_window)

        self.settings_grid = [['Forcefield', self.ui_forcefield_combo, self.ui_forcefield_add],
                              ['External\nForcefield',  self.ui_forcefield_frcmod_entry,
                                  self.ui_forcefield_frcmod],
                              ['Charmm\nParamaters', self.ui_forcefield_charmmpar_entry,
                                  self.ui_forcefield_charmmpar],
                              ['Integrator', self.ui_integrator],
                              ['Time Step', self.ui_timestep_entry, self.ui_advanced_options]]
        self.auto_grid(self.ui_settings_frame, self.settings_grid)

        # Fill Steady frame

        try:
            self.photo_down = tk.PhotoImage(
                file=(os.path.join(os.path.dirname(__file__), 'arrow_down.png')))
            self.photo_up = tk.PhotoImage(
                file=(os.path.join(os.path.dirname(__file__), 'arrow_up.png')))
        except (tk.TclError):
            print(
                'No image inside directory. Up and down arrow PNGS should be inside the OpenMM package')
        self.ui_stages_up = tk.Button(
            self.canvas, image=self.photo_up, command=self._move_stage_up)
        self.ui_stages_down = tk.Button(
            self.canvas, image=self.photo_down, command=self._move_stage_down)
        self.ui_stages_add = tk.Button(
            self.canvas, text='+', command=self._fill_ui_stages_window)
        self.ui_stages_remove = tk.Button(
            self.canvas, text='-', command=self._remove_stage)
        self.ui_stages_listbox = tk.Listbox(self.ui_stage_frame, height=27)

        stage_frame_widgets = [['ui_stages_down', 8, 4], ['ui_stages_up', 6, 4],
                               ['ui_stages_add', 2, 4], ['ui_stages_remove', 4, 4]]
        for item in stage_frame_widgets:
            getattr(self, item[0]).grid(
                in_=self.ui_stage_frame, row=item[1], column=item[2],  sticky='news', **self.input_option)
        self.ui_stages_listbox.grid(
            in_=self.ui_stage_frame, row=0, column=0, rowspan=10, columnspan=3, sticky='news', **self.input_option)
        self.ui_stages_listbox.configure(background='white')

        # Grid Frames
        frames = [[self.ui_input_frame, self.ui_output_frame]]
        self.auto_grid(
            self.canvas, frames, resize_columns=(0, 1), sticky='news')
        self.ui_settings_frame.grid(
            row=len(frames), columnspan=2, sticky='ew', padx=5, pady=5)
        self.ui_stage_frame.grid(
            row=0, column=3, rowspan=2, sticky='new', padx=5, pady=5)

        # Events
        self.ui_note.bind("<ButtonRelease-1>", self._forc_param)
        self.ui_model_extinput_show.bind("<<ListboxSelect>>", self._get_path)
        self.ui_model_pdb_show.bind("<<ListboxSelect>>", self._get_path)

        # Initialize Variables
        self.ui_forcefield_combo.current(0)
        self.ui_integrator.current(0)
        self.var_tstep.set(1000)
        self.var_output.set(os.path.expanduser('~'))
        self.var_output_traj_interval.set(1000)
        self.var_output_stdout_interval.set(1000)

    # Callbacks
    def _get_path(self, event):
        """
        Save path and position variables
        every single time an input Listbox
        is selected.
        """

        widget = event.widget
        if self.var_path_extinput_top.get():
            if widget == self.ui_model_extinput_show:
                self.var__path.set(self.ui_model_extinput_show.get(0))
                self.var_positions = (self.ui_model_extinput_show.get(1))
        if self.ui_model_pdb_show.getvalue():
            if widget == self.ui_model_pdb_show:
                self.var__path.set('path_pdb')  # Pathname in Moleculescrollboxx???
                self.var_positions = None

    def _browse_file(self, var_1, file_type1, file_type2):
        """
        Browse file path
        """

        path = filedialog.askopenfilename(initialdir='~/', filetypes=(
            (file_type1, '*.' + file_type1), (file_type2, '*.' + file_type2)))
        if path:
            var_1.set(path)

    def _browse_directory(self, var):
        """
        Search for the path to save the output

        Parameters
        ----------
        var= Interface entry widget where we wish insert the path file.

        """

        path_dir = filedialog.askdirectory(
            initialdir='~/')
        if path_dir:
            var.set(path_dir)

    def _include_amber_model(self):
        """
        Open and include PSF file or Prmtop.
        In that last case also add a inpcrd dile
        inside the listbox selecting the last added
        item and Opening all possible conformations
        """

        path_file = filedialog.askopenfilename(initialdir='~/', filetypes=(
            ('Amber Top', '*.prmtop'), ('PSF File', '*.psf')))
        if path_file:
            path_name, ext = os.path.splitext(path_file)
            file_name = os.path.basename(path_name).rstrip('/')
            self.ui_model_extinput_show.delete(0, 'end')
            self.var_path_extinput_top.set(path_file)
            self.ui_model_extinput_show.select_set(0)
            self.var__path.set(self.ui_model_extinput_show.get(0))
            if ext == '.prmtop':
                crd_name = file_name + '.inpcrd'
                self.ui_model_extinput_show.insert(
                    'end', os.path.join(os.path.dirname(path_file), crd_name))
                self.var_positions = self.ui_model_extinput_show.get(1)

    def _forc_param(self, event):
        """
        Enable or Disable forcefield option
        depending on user input choice
        """

        if self.ui_note.index(self.ui_note.select()) == 0:
            self.ui_forcefield_frcmod_entry.configure(state='normal')
            self.ui_forcefield_combo.configure(state='normal')
            self.ui_forcefield_charmmpar_entry.configure(state='disabled')
        elif self.ui_note.index(self.ui_note.select()) == 1:
            self.ui_forcefield_frcmod_entry.configure(state='disabled')
            self.ui_forcefield_combo.configure(state='disabled')
            self.ui_forcefield_charmmpar_entry.configure(state='normal')

    def _remove_stage(self):
        """
        Remove the selected stage from the stage listbox
        """
        if self.ui_stages_listbox.get(0):
            self.ui_stages_listbox.delete(self.ui_stages_listbox.curselection())

    def _move_stage_up(self):
        """
        Move one position upwards the selected stage
        """

        if self.ui_stages_listbox.curselection():
            i = (self.ui_stages_listbox.curselection())
            j = int(i[0])
            if j is not 0:
                move_item = self.ui_stages_listbox.get(j-1)
                self.ui_stages_listbox.delete(j-1)
                self.ui_stages_listbox.insert(j, move_item)

    def _move_stage_down(self):
        """
        Move one position downwards the selected stage
        """

        if self.ui_stages_listbox.curselection():
            i = (self.ui_stages_listbox.curselection())
            j = int(i[0])
            if j is not ((len(self.ui_stages_listbox.get(0, 'end'))-1)):
                move_item = self.ui_stages_listbox.get(j+1)
                self.ui_stages_listbox.delete(j+1)
                self.ui_stages_listbox.insert(j, move_item)

    def _fill_ui_stdout_window(self):
        """
        Opening Other reports options as Time, Energy, Temperature...
        """

        # Create window
        self.ui_stdout_window = tk.Toplevel()
        self.Center('ui_stdout_window')
        self.ui_stdout_window.title("Stdout Reporters")

        # Create frame and lframe
        self.ui_stdout_frame = tk.Frame(self.ui_stdout_window)
        self.ui_stdout_frame.pack()
        self.ui_stdout_frame_label = tk.LabelFrame(self.ui_stdout_frame, text='Real Time  Reporters')
        self.ui_stdout_frame_label.grid(row=0, column=0, **self.input_option)

        # Create Checkbuttons reporters and place them
        for i, item in enumerate(self.reporters):
            check = self.ui_labels[item] = ttk.Checkbutton(
                self.ui_stdout_frame, text=item, variable=getattr(self, 'var_' + item),  onvalue=item, offvalue='')
            item = check
            if i < 5:
                item.grid(
                    in_=self.ui_stdout_frame_label, row=0, column=i, sticky='ew', **self.input_option)
            else:
                item.grid(
                    in_=self.ui_stdout_frame_label, row=1, column=i-5, sticky='ew', **self.input_option)

        self.ui_stdout_close = tk.Button(
            self.ui_stdout_frame, text='close', command=lambda: self._close_ui_stdout_window('ui_output_reporters_realtime'))
        self.ui_stdout_close.grid(
            in_=self.ui_stdout_frame_label, row=2, column=5, sticky='ew', **self.input_option)
        self._fix_styles(self.ui_stdout_close)

        self.ui_stdout_window.mainloop()

    def _close_ui_stdout_window(self, listbox):
        """
        Close window while pass reporters to the listbox
        """
        getattr(self, listbox).delete(0, 'end')
        for item in self.reporters:
            if getattr(self, 'var_' + item).get() == item:
                getattr(self, listbox).insert('end', getattr(self,'var_' + item).get())
        if getattr(self, listbox).get(0, 'end'):
            self.var_verbose = True
        else:
            self.var_verbose = False
        self.ui_stdout_window.withdraw()

    def _fill_ui_output_opt_window(self):
        """
        Opening  report options
        """

        # Create window
        self.ui_output_opt = tk.Toplevel()
        self.Center('ui_output_opt')
        self.ui_output_opt.title("Output Options")

        # Create frame and lframe
        self.ui_output_opt_frame = tk.Frame(self.ui_output_opt)
        self.ui_output_opt_frame.pack()
        self.ui_output_opt_frame_label = tk.LabelFrame(self.ui_output_opt_frame, text='Advanced Output Options')
        self.ui_output_opt_frame_label.grid(row=0, column=0, **self.input_option)

        # Create Widgets
        self.ui_output_opt_traj_new_every_Entry = tk.Entry(
            self.ui_output_opt_frame, textvariable=self.var_traj_new_every)
        self.ui_output_opt_traj_atom_subset_Entry = tk.Entry(
            self.ui_output_opt_frame, textvariable=self.var_traj_atoms)
        self.ui_output_opt_restart_every_Entry = tk.Entry(
            self.ui_output_opt_frame, textvariable=self.var_restart_every)

        # Grid them
        self.output_opt_grid = [['Trajectory\nNew Every', self.ui_output_opt_traj_new_every_Entry],
                               ['Trajectory\nAtom Subset',
                                self.ui_output_opt_traj_atom_subset_Entry],
                               ['Restart Every', self.ui_output_opt_restart_every_Entry]]
        self.auto_grid(self.ui_output_opt_frame_label, self.output_opt_grid)

    def _fill_ui_stages_window(self):
        """
        Create widgets on TopLevel Window to set different
        stages inside our Molecular Dinamic Simulation
        """

        # creating window
        self.ui_stages_window = tk.Toplevel()
        self.Center('ui_stages_window')
        self.ui_stages_window.title("MD Stages")

        # Creating tabs
        ui_note = ttk.Notebook(self.ui_stages_window)
        titles = ["Stage", "Temperature & Pressure",
                  "Constrains & Minimization", "MD Final Settings"]
        for i, title in enumerate(titles, 1):
            setattr(self, 'ui_tab_'+str(i), tk.Frame(ui_note))
            ui_note.add(getattr(self, 'ui_tab_'+str(i)), text=title, state="normal")
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
            self.ui_tab_1, text='Save and Close', command=self._save_ui_stages_window)

        self.stage_grid = [['Stage Name', self.ui_stage_name_Entry],
                           ['', self.ui_stage_close, self.ui_stage_save_Button]]
        self.auto_grid(self.ui_stage_name_lframe, self.stage_grid)

        # tab_2
        self.ui_stage_temp_lframe = tk.LabelFrame(self.ui_tab_2, text='Temperature')
        self.ui_stage_pressure_lframe = tk.LabelFrame(self.ui_tab_2, text='Pressure')
        frames = [[self.ui_stage_temp_lframe, self.ui_stage_pressure_lframe]]
        self.auto_grid(self.ui_tab_2, frames)

        self.ui_stage_temp_Entry = tk.Entry(
            self.ui_tab_2, textvariable=self.var_stage_temp)
        self.temp_grid = [['Stage Temperature', self.ui_stage_temp_Entry]]
        self.auto_grid(self.ui_stage_temp_lframe, self.temp_grid)

        self.ui_stage_pressure_Entry = tk.Entry(
            self.ui_tab_2, state='disabled', textvariable=self.var_stage_pressure)
        self.ui_stage_barostat_steps_Entry = tk.Entry(
            self.ui_tab_2, state='disabled', textvariable=self.var_stage_pressure_steps)
        self.ui_stage_barostat_check = ttk.Checkbutton(
            self.ui_tab_2, text="Barostat", variable=self.var_stage_barostat,
            onvalue=True, offvalue=False,
            command=lambda: self._check_settings('var_stage_barostat', 'ui_stage_pressure_Entry',
                                                 'ui_stage_barostat_steps_Entry', True))
        self.pres_grid = [[self.ui_stage_barostat_check, ''],
                          ['Pressure', self.ui_stage_pressure_Entry],
                          ['Barostat Every', self.ui_stage_barostat_steps_Entry]]
        self.auto_grid(self.ui_stage_pressure_lframe, self.pres_grid)

        # Tab3
        self.ui_stage_constr_lframe = tk.LabelFrame(
            self.ui_tab_3, text='Constrained Atoms')
        self.ui_stage_minim_lframe = tk.LabelFrame(self.ui_tab_3, text='Minimize:')
        frames = [[self.ui_stage_constr_lframe, self.ui_stage_minim_lframe]]
        self.auto_grid(self.ui_tab_3, frames)

        self.ui_stage_constrprot_check = ttk.Checkbutton(
            self.ui_tab_3, text='Protein', variable=self.var_stage_constrprot,
            onvalue='Protein', offvalue=None)
        self.ui_stage_constrback_check = ttk.Checkbutton(
            self.ui_tab_3, text='Bakcbone', variable=self.var_stage_constrback,
            onvalue='Backbone', offvalue=None)
        self.ui_stage_constrother_Entry = tk.Entry(
            self.ui_tab_3, width=20, textvariable=self.var_stage_constrother)
        self.constr_grid = [[self.ui_stage_constrprot_check],
                            [self.ui_stage_constrback_check],
                            ['Other', self.ui_stage_constrother_Entry]]
        self.auto_grid(self.ui_stage_constr_lframe, self.constr_grid)

        self.ui_stage_minimiz_check = ttk.Checkbutton(
            self.ui_tab_3, text="Minimization", variable=self.var_stage_minimiz, offvalue=False,
            onvalue=True, command=lambda: self._check_settings(
                'var_stage_minimiz', 'ui_stage_minimiz_maxsteps_Entry', 'ui_stage_minimiz_tolerance_Entry', True))
        self.ui_stage_minimiz_maxsteps_Entry = tk.Entry(
            self.ui_tab_3, state='disabled', textvariable=self.var_stage_minimiz_maxsteps)
        self.ui_stage_minimiz_tolerance_Entry = tk.Entry(
            self.ui_tab_3, state='disabled', textvariable=self.var_stage_minimiz_tolerance)

        self.minimiz_grid = [[self.ui_stage_minimiz_check, ''],
                             ['Max Steps', self.ui_stage_minimiz_maxsteps_Entry],
                             ['Tolerance', self.ui_stage_minimiz_tolerance_Entry]]
        self.auto_grid(self.ui_stage_minim_lframe, self.minimiz_grid)

        # Tab 4
        self.ui_stage_mdset_lframe = tk.LabelFrame(self.ui_tab_4)
        self.ui_stage_mdset_lframe.pack(expand=True, fill='both')

        self.ui_stage_steps_Entry = tk.Entry(
            self.ui_tab_4, textvariable=self.var_stage_steps)
        self.ui_stage_dcd_check = tk.Checkbutton(
            self.ui_tab_4, text='DCD trajectory reports', variable=self.var_stage_dcd,
            onvalue='DCD', offvalue=None,
            command=lambda: self._check_settings('var_stage_dcd', 'ui_stage_reportevery_Entry', 'DCD'))
        self.ui_stage_reportevery_Entry = tk.Entry(
            self.ui_tab_4, textvariable=self.var_stage_reportevery, state='disabled')

        self.stage_md = [['MD Steps', self.ui_stage_steps_Entry],
                         ['Report every', self.ui_stage_reportevery_Entry],
                         ['', self.ui_stage_dcd_check]]
        self.auto_grid(self.ui_stage_mdset_lframe, self.stage_md)

        # Set variables
        self.var_stage_temp.set(300)
        self.var_stage_minimiz_maxsteps.set(10000)
        self.var_stage_minimiz_tolerance.set(10)
        self.var_stage_steps.set(10000)
        self.var_advopt_pressure.set(1)
        self.var_advopt_pressure_steps.set(25)
        self.var_stage_pressure.set(self.var_advopt_pressure.get())
        self.var_stage_pressure_steps.set(self.var_advopt_pressure_steps.get())
        self.var_stage_dcd.set(None)

        self.ui_stages_window.mainloop()

    def _save_ui_stages_window(self):
        """
        Save stage on the main listbox while closing the window and reset all variables
        """
        

        if not self.var_stage_name.get():
            self.ui_stage_name_Entry.configure(background='red')
        else:
            self.ui_stages_listbox.insert('end', self.var_stage_name.get())
            self.ui_stages_window.withdraw()
            setattr(self, 'stage_' + self.var_stage_name.get(), [])
            for variable in self.stage_variables:
                setattr(self,  variable + '_' + self.var_stage_name.get(),
                        getattr(self,  variable).get())
                getattr(self, 'stage_' + self.var_stage_name.get()).append(
                    getattr(self, variable + '_' + self.var_stage_name.get()))
            #print(getattr(self, 'stage_' + self.var_stage_name.get()))
            self.names.append(self.var_stage_name.get())
            for item in self.stages_strings:
                getattr(self, item + '_Entry').delete(0, 'end')
            for item in self.check_variables:
                getattr(self, item).set(False)

    def _close_ui_stages_window(self):
        """
        Close window ui_stages_window and reset all variables
        """
        self.ui_stages_window.withdraw()

        for item in self.stages_strings:
            getattr(self, item + '_Entry').delete(0, 'end')
        check_variables = ['var_stage_minimiz', 'var_stage_dcd', 'var_stage_barostat']
        for item in self.check_variables:
            getattr(self, item).set(False)

    def _fill_ui_advopt_window(self):
        """
        Create widgets on TopLevel Window to set different general
        advanced optinons inside our Molecular Dinamic Simulation
        """

        # Create TopLevel window
        self.ui_advopt_window = tk.Toplevel()
        self.Center('ui_advopt_window')
        self.ui_advopt_window.title("Advanced Options")

        # Create Tabs
        ui_note = ttk.Notebook(self.ui_advopt_window)
        titles = ["Conditions", "OpenMM System Options", "Hardware"]
        for i, title in enumerate(titles, 1):
            setattr(self, 'ui_tab_'+str(i), tk.Frame(ui_note))
            ui_note.add(getattr(self, 'ui_tab_'+str(i)), text=title, state="normal")
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
                'var_advopt_barostat', 'ui_advopt_pressure_Entry',
                'ui_advopt_barostat_steps_Entry', True))
        self.ui_advopt_pressure_Entry = tk.Entry(
            self.ui_tab_1, state='disabled', textvariable=self.var_advopt_pressure)
        self.ui_advopt_barostat_steps_Entry = tk.Entry(
            self.ui_tab_1, state='disabled', textvariable=self.var_advopt_pressure_steps)

        self.advopt_grid = [['Friction', self.ui_advopt_friction_Entry],
                            ['Temperature', self.ui_advopt_temp_Entry],
                            [self.ui_advopt_barostat_check, ''],
                            ['Pressure', self.ui_advopt_pressure_Entry],
                            ['Maximum Steps', self.ui_advopt_barostat_steps_Entry]]
        self.auto_grid(self.ui_advopt_conditions_lframe, self.advopt_grid)

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
        self.ui_advopt_edwalderr_Entry = tk.Entry(
            self.ui_tab_2, textvariable=self.var_advopt_edwalderr, state='disabled')
        self.ui_advopt_constr_combo = ttk.Combobox(
            self.ui_tab_2, textvariable=self.var_advopt_constr)
        self.ui_advopt_constr_combo.config(
            values=('None', 'HBonds', 'HAngles', 'AllBonds'))
        self.ui_advopt_rigwat_combo = ttk.Combobox(
            self.ui_tab_2, textvariable=self.var_advopt_rigwat)
        self.ui_advopt_rigwat_combo.config(
            values=('True', 'False'))

        self.advopt_grid = [['Non Bonded Method', self.ui_advopt_nbm_combo],
                            ['Edwald Tolerance', self.ui_advopt_edwalderr_Entry],
                            ['Non Bonded Cutoff', self.ui_advopt_cutoff_Entry],
                            ['Constraints', self.ui_advopt_constr_combo],
                            ['Rigid Water', self.ui_advopt_rigwat_combo]]
        self.auto_grid(self.ui_advopt_system_lframe, self.advopt_grid)
        # Events
        self.ui_advopt_nbm_combo.bind("<<ComboboxSelected>>", self._PME_settings)

        # Tab3

        self.ui_advopt_hardware_lframe = tk.LabelFrame(
            self.ui_tab_3, text='Platform')
        self.ui_advopt_hardware_lframe.pack(expand=True, fill='both')

        self.ui_advopt_platform_combo = ttk.Combobox(
            self.ui_tab_3, textvariable=self.var_advopt_hardware)
        self.ui_advopt_platform_combo.config(values=('CPU', 'OpenCL', 'CUDA'))
        self.ui_advopt_precision_combo = ttk.Combobox(
            self.ui_tab_3, textvariable=self.var_advopt_precision)
        self.ui_advopt_precision_combo.config(
            values=('single', 'mixed', 'double'))

        self.advopt_platform_grid = [['', ''],
                                     ['Platform', self.ui_advopt_platform_combo],
                                     ['Precision', self.ui_advopt_precision_combo]]
        self.auto_grid(self.ui_advopt_hardware_lframe, self.advopt_platform_grid)

        # Initialize Variables
        self.var_advopt_friction.set(0.01)
        self.var_advopt_temp.set(300)
        self.var_advopt_barostat.set(0)
        self.var_advopt_pressure.set(1)
        self.var_advopt_pressure_steps.set(25)
        self.ui_advopt_nbm_combo.current(0)
        self.var_advopt_cutoff.set(1)
        self.ui_advopt_constr_combo.current(0)
        self.ui_advopt_rigwat_combo.current(0)
        self.ui_advopt_platform_combo.current(0)
        self.ui_advopt_precision_combo.current(0)

    def _PME_settings(self, event):
        """
        Enable or Disable Edwald Error Entry when
        CutoffNonPeriodic Combobox is selected
        """
        if self.var_advopt_nbm.get() == 'PME':
            self.ui_advopt_edwalderr_Entry.configure(state='normal')
        else:
            self.ui_advopt_edwalderr_Entry.configure(state='disabled')

    def _fill_ui_input_opt_window(self):

        # Create TopLevel window
        self.ui_input_opt_window = tk.Toplevel()
        self.Center('ui_input_opt_window')
        self.ui_input_opt_window.title("Advanced Options")
        # Create lframe
        self.ui_advopt_input_opt_lframe = tk.LabelFrame(
            self.ui_input_opt_window, text='Initial Files')
        self.ui_advopt_input_opt_lframe.pack(expand=True, fill='both')
        # Fill lframe
        self.ui_input_vel_Entry = tk.Entry(
            self.ui_input_opt_window, textvariable=self.var_input_vel)
        self.ui_input_vel_browse = tk.Button(
            self.ui_input_opt_window, text='...', command=lambda: self._browse_file(self.var_input_vel, 'vel', ''))
        self.ui_input_box_Entry = tk.Entry(
            self.ui_input_opt_window, textvariable=self.var_input_box)
        self.ui_input_box_browse = tk.Button(
            self.ui_input_opt_window, text='...', command=lambda: self._browse_file(self.var_input_box, 'xsc', 'csv'))
        self.ui_input_checkpoint_Entry = tk.Entry(
            self.ui_input_opt_window, textvariable=self.var_input_checkpoint)
        self.ui_input_checkpoint_browse = tk.Button(
            self.ui_input_opt_window, text='...', command=lambda: self._browse_file(self.var_input_checkpoint, 'xml', 'rst'))

        self.input_grid = [['Velocities', self.ui_input_vel_Entry, self.ui_input_vel_browse,
                            'Box', self.ui_input_box_Entry, self.ui_input_box_browse],
                           ['Restart File', self.ui_input_checkpoint_Entry, self.ui_input_checkpoint_browse]]
        self.auto_grid(self.ui_advopt_input_opt_lframe, self.input_grid)

    def _check_settings(self, *args):
        """
        Enable or Disable several settings
        depending on other Checkbutton value

        Parameters
        ----------
        args[0]: tk widget Checkbutton where we set an options
        args[-1]: onvalue Checkbutton normally set as 1
        args[1],args[2]...: tk widgets to enable or disabled

        """
        if getattr(self, args[0]).get() == args[-1]:
            for x in args:
                if x == args[-1] or x == args[0]:
                    pass
                else:
                    getattr(self, x).configure(state='normal')

        else:
            for x in args:
                if x == args[-1] or x == args[0]:
                    pass
                else:
                    getattr(self, x).configure(state='disabled')


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
                    self.auto_pack(frame, item, side='left', padx=2, pady=2, expand=True, fill='both',
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

    def auto_pack(self, parent, widgets, label_sep=':', **kwargs):
        for widget in widgets:
            options = kwargs.copy()
            if isinstance(widget, basestring):
                label = self.ui_labels[widget] = tk.Label(
                    parent, text=widget + label_sep if widget else '')
                widget = label
            if isinstance(widget, (tk.Button, tk.Label)):
                options['expand'] = False
            widget.pack(in_=parent, **options)
            self._fix_styles(widget)

    def Center(self, window):
        # Update "requested size" from geometry manager
        getattr(self, window).update_idletasks()
        x = (getattr(self, window).winfo_screenwidth() -
             getattr(self, window).winfo_reqwidth()) / 2
        y = (getattr(self, window).winfo_screenheight() -
             getattr(self, window).winfo_reqheight()) / 2
        getattr(self, window).geometry("+%d+%d" % (x, y))
        getattr(self, window).deiconify()

    def Close(self):
        """
        Default! Triggered action if you click on the Close button
        """
        global ui
        ui = None
        ModelessDialog.Close(self)
        self.destroy()
