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
        'height': '5',
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
        self.title = "Plume OpenMM"

        # OpenMM variables
        self.entries = ("output", "input", "restart", "top", "cuttoff", "constr", "water",  "forcefield",
                        "solvent", "integrator", "platform", "precision", "external_forc", "parametrize_forc",
                        "dcd", "pdbr", "other_reporters", "md_reporters", "stage_name", "stage_constrprot",
                        "stage_constrback", "stage_constrother", "advopt_nbm", "advopt_constr", "advopt_rigwat",
                        "advopt_hardware", "advopt_precision", "input_vel", "input_box", "input_charmm",
                        "input_checkpoint", "var_positions", "traj_atoms")

        self.stages_strings = ("stage_barostat_steps", "stage_pressure",
                               "stage_temp", "stage_minimiz_maxsteps", "ststagesage_minimiz_tolerance",
                               "stage_reportevery", "stage_steps",
                               "stage_name", "stage_constrother")

        self.reporters = ('Time', 'Steps', 'Speed', 'Progress', 'Potencial Energy', 'Kinetic Energy',
                          'Total Energy', 'Temperature', 'Volume', 'Density')
        self.integrers = ("barostat", "colrate", "tstep", "temp", "nbm", "temp_eq", "simstep",
                          "inter", "simulstep",  "tolerance",
                          "minimiz", "max_steps", "pressure", "bar_interval", "stage_pressure_steps",
                          "stage_pressure", "stage_barostat", "stage_temp", "stage_minimiz_maxsteps",
                          "stage_minimiz_tolerance", "stage_minimiz", "stage_dcd", "stage_reportevery",
                          "stage_steps", "advopt_temp", "advopt_pressure", "advopt_pressure_steps",
                          "advopt_friction", "advopt_barostat", "advopt_cutoff", "advopt_edwalderr",
                          "output_trajinterval", "output_stdoutinterval", "traj_new_every",
                          "restart_every")

        for e in self.entries:
            setattr(self, e, tk.StringVar())
        for s in self.stages_strings:
            setattr(self, s, tk.StringVar())
        for r in self.reporters:
            setattr(self, r, tk.StringVar())
        for i in self.integrers:
            setattr(self, i, tk.IntVar())

        self._path = tk.StringVar()
        self._path_crd = tk.StringVar()
        self.path_extinput_top = tk.StringVar()
        self.path_extinput_crd = tk.StringVar()
        self.path_pdb = tk.StringVar()
        self.verbose = True

        # Misc
        self._basis_set_dialog = None
        self.ui_labels = {}
        self.input_option = {'padx': 10, 'pady': 10}

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
                  ('ui_settings_frame', 'Settings'), ('ui_steady_frame', 'Stages')]
        for frame in frames:
            for item in frames:
                setattr(
                    self, item[0], tk.LabelFrame(self.canvas, text=item[1]))

        # Fill frames
        # Fill Input frame
        # Creating tabs
        self.note = ttk.Notebook(self.ui_input_frame)
        self.tab_1 = tk.Frame(self.note)
        self.tab_2 = tk.Frame(self.note)
        self.note.add(self.tab_1, text="Chimera", state="normal")
        self.note.add(self.tab_2, text="External Input", state="normal")
        self.note.pack(expand=True, fill='both')

        # Fill input frame
        # Create and grid tab 1, 2 and 3

        #self.model_pdb_add = tk.Button(
         #   self.ui_input_frame, text='Set Model', command=self._include_pdb_model)
        self.model_pdb_show = MoleculeScrolledListBox(self.ui_input_frame)

        self.model_pdb_options = tk.Button(
            self.ui_input_frame, text="Advanced\nOptions", command=self._fill_inputopt_window)
        self.model_pdb_sanitize = tk.Button(
            self.ui_input_frame, text="Sanitize\nModel")
        self.pdb_grid = [[self.model_pdb_show],
                         [(self.model_pdb_options, self.model_pdb_sanitize)]]
                         #[self.model_pdb_add]]
        self.auto_grid(self.tab_1, self.pdb_grid)

        self.model_extinput_add = tk.Button(
            self.ui_input_frame, text='Set Model', command=self._include_amber_model)
        self.model_extinput_show = tk.Listbox(
            self.ui_input_frame, listvariable=self.path_extinput_top)
        self.model_extinput_options = tk.Button(
            self.ui_input_frame, text="Advanced\nOptions", command=self._fill_inputopt_window)
        self.model_extinput_sanitize = tk.Button(
            self.ui_input_frame, text="Sanitize\nModel")
        self.extinput_grid = [[self.model_extinput_show],
                              [(self.model_extinput_options,
                                self.model_extinput_sanitize)],
                              [self.model_extinput_add]]
        self.auto_grid(self.tab_2, self.extinput_grid)

        # Fill Output frame
        self.output_entry = tk.Entry(self.canvas, textvariable=self.output)
        self.output_browse = tk.Button(
            self.canvas, text='...', command=lambda: self._browse_directory(self.output))
        self.show_reporters_md =  ttk.Combobox(self.canvas, textvariable=self.md_reporters)
        self.show_reporters_md.config(values=('PDB','DCD','None'))
        self.add_reporters_realtime = tk.Button(
            self.canvas, text='+', command=self._fill_timerep_window)
        self.show_reporters_realtime = tk.Listbox(
            self.ui_output_frame)
        self.output_trjinterval_Entry = tk.Entry(
            self.canvas, textvariable=self.output_trajinterval)
        self.output_stdoutinterval_Entry = tk.Entry(
            self.canvas, textvariable=self.output_stdoutinterval)
        self.output_options = tk.Button(self.canvas, text='Opt', command = self._fill_outputopt_window)

        self.output_grid = [['Save at', self.output_entry, self.output_browse],
                            ['Trajectory\nReporters',  self.show_reporters_md],
                            ['Real Time\nReporters', self.show_reporters_realtime,
                                self.add_reporters_realtime],
                            ['Trajectory\nEvery', self.output_trjinterval_Entry],
                            ['Stdout \nEvery', self.output_stdoutinterval_Entry,
                            self.output_options]]
        self.auto_grid(self.ui_output_frame, self.output_grid)

        # Fill Settings frame
        self.force_combo = ttk.Combobox(
            self.canvas, textvariable=self.forcefield)
        self.force_combo.config(values=(
            'amber96', 'amber99sb', 'amber99sbildn', 'amber99sbnmr', 'amber03', 'amber10'))
        self.add_default_forcefield = tk.Button(
            self.canvas, text='+')
        self.add_external_forcefield = tk.Button(
            self.canvas, text='...', command=lambda: self._browse_file(self.external_forc, 'frcmod', ''))
        self.parametrize_your_forcefield = tk.Button(
            self.canvas, text='...', command=lambda: self._browse_file(self.parametrize_forc, 'par', ''))
        self.external_forc_entry = tk.Entry(
            self.canvas, textvariable=self.external_forc)
        self.parametrize_forc_entry = tk.Entry(
            self.canvas, textvariable=self.parametrize_forc, state='disabled')
        self.int_combo = ttk.Combobox(
            self.canvas, textvariable=self.integrator)
        self.int_combo.config(
            values=('Langevin', 'Brownian', 'Verlet', 'VariableVerlet', 'VariableLangevin'))
        self.timestep_entry = tk.Entry(
            self.canvas, textvariable=self.tstep, )
        self.advanced_options = tk.Button(
            self.canvas, text='Opt', command=self._fill_advoptions_window)

        self.settings_grid = [['Forcefield', self.force_combo, self.add_default_forcefield],
                              ['External\nForcefield',  self.external_forc_entry, self.add_external_forcefield],
                              ['Charmm\nParamaters', self.parametrize_forc_entry, self.parametrize_your_forcefield],
                              ['Integrator', self.int_combo], 
                              ['Time Step', self.timestep_entry, self.advanced_options]]
        self.auto_grid(self.ui_settings_frame, self.settings_grid)

        # Fill Steady frame

        try:
            self.photo_down = tk.PhotoImage(
                file=(os.path.join(os.path.dirname(__file__),'arrow_down.png')))
            self.photo_up = tk.PhotoImage(
                file=(os.path.join(os.path.dirname(__file__),'arrow_up.png')))
        except (tk.TclError):
            print('No image inside directory. Up and down arrow PNGS should be inside the OpenMM package')
        self.movesteady_up = tk.Button(
            self.canvas, image=self.photo_up, command=self._move_stage_up)
        self.movesteady_down = tk.Button(
            self.canvas, image=self.photo_down, command=self._move_stage_down)
        self.add_to_steady = tk.Button(
            self.canvas, text='+', command=self._fill_stages_window)
        self.remove_from_steady = tk.Button(
            self.canvas, text='-', command=self._remove_stage)
        self.steady_scrolbox = tk.Listbox(self.ui_steady_frame, height=27)

        stage_frame_widgets = [['movesteady_down', 8, 4], ['movesteady_up', 6, 4],
                               ['add_to_steady', 2, 4], ['remove_from_steady', 4, 4]]
        for item in stage_frame_widgets:
            getattr(self, item[0]).grid(
                in_=self.ui_steady_frame, row=item[1], column=item[2],  sticky='news', **self.input_option)
        self.steady_scrolbox.grid(
            in_=self.ui_steady_frame, row=0, column=0, rowspan=10, columnspan=3, sticky='news', **self.input_option)
        self.steady_scrolbox.configure(background='white')

        # Grid Frames
        frames = [[self.ui_input_frame, self.ui_output_frame]]
        self.auto_grid(
            self.canvas, frames, resize_columns=(0, 1), sticky='news')
        self.ui_settings_frame.grid(
            row=len(frames), columnspan=2, sticky='ew', padx=5, pady=5)
        self.ui_steady_frame.grid(
            row=0, column=3, rowspan=2, sticky='new', padx=5, pady=5)

        # Events
        self.note.bind("<ButtonRelease-1>", self._forc_param)
        self.model_extinput_show.bind("<<ListboxSelect>>", self._get_path)
        self.model_pdb_show.bind("<<ListboxSelect>>", self._get_path)

        # Initialize Variables
        self.force_combo.current(0)
        self.int_combo.current(0)
        self.tstep.set(1000)
        self.output.set(os.path.expanduser('~'))
        self.output_trajinterval.set(1000)
        self.output_stdoutinterval.set(1000)

    # Callbacks
    def _get_path(self, event):
        """
        Save path and position variables
        every single time an input Listbox
        is selected.
        """

        widget = event.widget
        if self.path_extinput_top.get():
            if widget == self.model_extinput_show:
                self._path.set(self.model_extinput_show.get(0))
                self.var_positions=(self.model_extinput_show.get(1))
        if self.model_pdb_show.getvalue():
            if widget == self.model_pdb_show:
                self._path.set('path_pdb') #Pathname in Moleculescrollboxx???
                self.var_positions=None

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
            self.model_extinput_show.delete(0, 'end')
            self.path_extinput_top.set(path_file)
            self.model_extinput_show.select_set(0)
            self._path.set(self.model_extinput_show.get(0))
            if ext == '.prmtop':
                crd_name = file_name + '.inpcrd'
                self.model_extinput_show.insert(
                    'end', os.path.join(os.path.dirname(path_file), crd_name))
                self.var_positions = self.model_extinput_show.get(1)

    def _forc_param(self, event):
        """
        Enable or Disable forcefield option
        depending on user input choice
        """

        if self.note.index(self.note.select()) == 0:
            self.external_forc_entry.configure(state='normal')
            self.force_combo.configure(state='normal')
            self.parametrize_forc_entry.configure(state='disabled')
        elif self.note.index(self.note.select()) == 1:
            self.external_forc_entry.configure(state='disabled')
            self.force_combo.configure(state='disabled')
            self.parametrize_forc_entry.configure(state='normal')

    def _remove_stage(self):
        """
        Remove the selected stage from the stage listbox
        """
        if self.steady_scrolbox.get(0):
            self.steady_scrolbox.delete(self.steady_scrolbox.curselection())

    def _move_stage_up(self):
        """
        Move one position upwards the selected stage
        """

        if self.steady_scrolbox.curselection():
            i = (self.steady_scrolbox.curselection())
            j = int(i[0])
            if j is not 0:
                move_item = self.steady_scrolbox.get(j-1)
                self.steady_scrolbox.delete(j-1)
                self.steady_scrolbox.insert(j, move_item)

    def _move_stage_down(self):
        """
        Move one position downwards the selected stage
        """

        if self.steady_scrolbox.curselection():
            i = (self.steady_scrolbox.curselection())
            j = int(i[0])
            if j is not ((len(self.steady_scrolbox.get(0, 'end'))-1)):
                move_item = self.steady_scrolbox.get(j+1)
                self.steady_scrolbox.delete(j+1)
                self.steady_scrolbox.insert(j, move_item)



    def _fill_timerep_window(self):
        """
        Opening Other reports options as Time, Energy, Temperature...
        """

        # Create window
        self.timerep_window = tk.Toplevel()
        self.Center('timerep_window')
        self.timerep_window.title("Real Time Reporters")

        # Create frame and lframe
        self.f2 = tk.Frame(self.timerep_window)
        self.f2.pack()
        self.f2_label = tk.LabelFrame(self.f2, text='Real Time  Reporters')
        self.f2_label.grid(row=0, column=0, **self.input_option)

        # Create Checkbuttons reporters and place them
        for i, item in enumerate(self.reporters):
            check = self.ui_labels[item] = ttk.Checkbutton(
                self.f2, text=item, variable=getattr(self, item),  onvalue=item, offvalue='')
            item = check
            if i < 5:
                item.grid(
                    in_=self.f2_label, row=0, column=i, sticky='ew', **self.input_option)
            else:
                item.grid(
                    in_=self.f2_label, row=1, column=i-5, sticky='ew', **self.input_option)

        self.close_b2 = tk.Button(
            self.f2, text='close', command=lambda: self._close_timerep_window('show_reporters_realtime'))
        self.close_b2.grid(
            in_=self.f2_label, row=2, column=5, sticky='ew', **self.input_option)
        self._fix_styles(self.close_b2)

        self.timerep_window.mainloop()

    def _close_timerep_window(self, listbox):
        """
        Close window while pass reporters to the listbox
        """
        getattr(self, listbox).delete(0, 'end')
        for item in self.reporters:
            if getattr(self, item).get() == item:
                getattr(self, listbox).insert('end', getattr(self, item).get())
        if  getattr(self, listbox).get(0,'end'):
            self.verbose = True
        else:
            self.verbose = False
        self.timerep_window.withdraw()

    def _fill_outputopt_window(self):
        """
        Opening  report options
        """

        # Create window
        self.outputopt = tk.Toplevel()
        self.Center('outputopt')
        self.outputopt.title("Output Options")

        # Create frame and lframe
        self.f1 = tk.Frame(self.outputopt)
        self.f1.pack()
        self.f1_label = tk.LabelFrame(self.f1, text='Advanced Output Options')
        self.f1_label.grid(row=0, column=0, **self.input_option)

        #Create Widgets
        self.outputopt_traj_new_every_Entry = tk.Entry(self.f1, textvariable=self.traj_new_every)
        self.outputopt_traj_atom_subset_Entry = tk.Entry(self.f1, textvariable=self.traj_atoms)
        self.outputopt_restart_every_Entry = tk.Entry(self.f1, textvariable=self.restart_every)

        #Grid them
        self.outputopt_grid=[['Trajectory\nNew Every', self.outputopt_traj_new_every_Entry],
                             ['Trajectory\nAtom Subset', self.outputopt_traj_atom_subset_Entry],
                             ['Restart Every', self.outputopt_restart_every_Entry]]
        self.auto_grid(self.f1_label, self.outputopt_grid)


    def _fill_stages_window(self):
        """
        Create widgets on TopLevel Window to set different
        stages inside our Molecular Dinamic Simulation
        """

        # creating window
        self.stages_window = tk.Toplevel()
        self.Center('stages_window')
        self.stages_window.title("MD Stages")

        # Creating tabs
        note = ttk.Notebook(self.stages_window)
        titles = ["Stage", "Temperature & Pressure",
                  "Constrains & Minimization", "MD Final Settings"]
        for i, title in enumerate(titles, 1):
            setattr(self, 'tab_'+str(i), tk.Frame(note))
            note.add(getattr(self, 'tab_'+str(i)), text=title, state="normal")
        note.pack()

        # Tab1
        self.stage_name_lframe = tk.LabelFrame(
            self.tab_1, text='Stage Main Settings')
        self.stage_name_lframe.pack(expand=True, fill='both')

        self.stage_name_Entry = tk.Entry(
            self.tab_1, textvariable=self.stage_name)
        self.close_b3 = tk.Button(
            self.tab_1, text='Close', command=self._close_stages_window)
        self.stage_save_Button = tk.Button(
            self.tab_1, text='Save and Close', command=self._save_stages_window)

        self.stage_grid = [['Stage Name', self.stage_name_Entry],
                           ['', self.close_b3, self.stage_save_Button]]
        self.auto_grid(self.stage_name_lframe, self.stage_grid)

        # Tab2
        self.stage_temp_lframe = tk.LabelFrame(self.tab_2, text='Temperature')
        self.stage_pressure_lframe = tk.LabelFrame(self.tab_2, text='Pressure')
        frames = [[self.stage_temp_lframe, self.stage_pressure_lframe]]
        self.auto_grid(self.tab_2, frames)

        self.stage_temp_Entry = tk.Entry(
            self.tab_2, textvariable=self.stage_temp)
        self.temp_grid = [['Stage Temperature', self.stage_temp_Entry]]
        self.auto_grid(self.stage_temp_lframe, self.temp_grid)

        self.stage_pressure_Entry = tk.Entry(
            self.tab_2, state='disabled', textvariable=self.stage_pressure)
        self.stage_barostat_steps_Entry = tk.Entry(
            self.tab_2, state='disabled', textvariable=self.stage_pressure_steps)
        self.stage_barostat_check = ttk.Checkbutton(
            self.tab_2, text="Barostat", variable=self.stage_barostat,
            command=lambda: self._check_settings('stage_barostat', 'stage_pressure_Entry',
                                                 'stage_barostat_steps_Entry', 1))
        self.pres_grid = [[self.stage_barostat_check, ''],
                          ['Pressure', self.stage_pressure_Entry],
                          ['Barostat Every', self.stage_barostat_steps_Entry]]
        self.auto_grid(self.stage_pressure_lframe, self.pres_grid)

        # Tab3
        self.stage_constr_lframe = tk.LabelFrame(
            self.tab_3, text='Constrained Atoms')
        self.stage_minim_lframe = tk.LabelFrame(self.tab_3, text='Minimize:')
        frames = [[self.stage_constr_lframe, self.stage_minim_lframe]]
        self.auto_grid(self.tab_3, frames)

        self.stage_constrprot_check = ttk.Checkbutton(
            self.tab_3, text='Protein', variable=self.stage_constrprot)
        self.stage_constrback_check = ttk.Checkbutton(
            self.tab_3, text='Bakcbone', variable=self.stage_constrback)
        self.stage_constrother_Entry = tk.Entry(
            self.tab_3, width=20, textvariable=self.stage_constrother)
        self.constr_grid = [[self.stage_constrprot_check],
                            [self.stage_constrback_check],
                            ['Other', self.stage_constrother_Entry]]
        self.auto_grid(self.stage_constr_lframe, self.constr_grid)

        self.stage_minimiz_check = ttk.Checkbutton(
            self.tab_3, text="Minimization", variable=self.stage_minimiz, offvalue=False,
            onvalue= True, command=lambda: self._check_settings(
            'stage_minimiz', 'stage_minimiz_maxsteps_Entry','stage_minimiz_tolerance_Entry', True))
        self.stage_minimiz_maxsteps_Entry = tk.Entry(
            self.tab_3, state='disabled', textvariable=self.stage_minimiz_maxsteps)
        self.stage_minimiz_tolerance_Entry = tk.Entry(
            self.tab_3, state='disabled', textvariable=self.stage_minimiz_tolerance)

        self.minimiz_grid = [[self.stage_minimiz_check, ''],
                             ['Max Steps', self.stage_minimiz_maxsteps_Entry],
                             ['Tolerance', self.stage_minimiz_tolerance_Entry]]
        self.auto_grid(self.stage_minim_lframe, self.minimiz_grid)

        # Tab 4
        self.stage_mdset_lframe = tk.LabelFrame(self.tab_4)
        self.stage_mdset_lframe.pack(expand=True, fill='both')

        self.stage_steps_Entry = tk.Entry(
            self.tab_4, textvariable=self.stage_steps)
        self.stage_dcd_check = tk.Checkbutton(
            self.tab_4, text='DCD trajectory reports', variable=self.stage_dcd,
            command=lambda: self._check_settings('stage_dcd', 'stage_reportevery_Entry', 1))
        self.stage_reportevery_Entry = tk.Entry(
            self.tab_4, textvariable=self.stage_reportevery, state='disabled')

        self.stage_md = [['MD Steps', self.stage_steps_Entry],
                         ['Report every', self.stage_reportevery_Entry],
                         ['', self.stage_dcd_check]]
        self.auto_grid(self.stage_mdset_lframe, self.stage_md)

        self.stages_window.mainloop()

    def _save_stages_window(self):
        """
        Save stage on the main listbox while closing the window and reset all variables
        """
        check_variables = ["stage_minimiz", "stage_dcd", "stage_barostat",
                           "stage_constrprot", "stage_constrback"]

        if len(self.stage_name.get()) is 0:
            self.stage_name_Entry.configure(background='red')

        else:
            self.steady_scrolbox.insert('end', self.stage_name.get())
            self.stages_window.withdraw()

            for item in self.stages_strings:
                # Resetting window
                getattr(self, item + '_Entry').delete(0, 'end')

            for item in check_variables:  # Resetting check buttons
                getattr(self, item).set(0)

    def _close_stages_window(self):
        """
        Close window stages_window and reset all variables
        """
        self.stages_window.withdraw()

        for item in self.stages_strings:
            getattr(self, item + '_Entry').delete(0, 'end')
        check_variables = ["stage_minimiz", "stage_dcd", "stage_barostat"]
        for item in check_variables:
            getattr(self, item).set(0)

    def _fill_advoptions_window(self):
        """
        Create widgets on TopLevel Window to set different general
        advanced optinons inside our Molecular Dinamic Simulation
        """

        # Create TopLevel window
        self.advoptions_window = tk.Toplevel()
        self.Center('advoptions_window')
        self.advoptions_window.title("Advanced Options")

        # Create Tabs
        note = ttk.Notebook(self.advoptions_window)
        titles = ["Conditions", "OpenMM System Options", "Hardware"]
        for i, title in enumerate(titles, 1):
            setattr(self, 'tab_'+str(i), tk.Frame(note))
            note.add(getattr(self, 'tab_'+str(i)), text=title, state="normal")
        note.pack()

        # Tab1
        self.advopt_conditions_lframe = tk.LabelFrame(
            self.tab_1, text='Set Conditions')
        self.advopt_conditions_lframe.pack(expand=True, fill='both')

        self.advopt_friction_Entry = tk.Entry(
            self.tab_1, textvariable=self.advopt_friction)
        self.advopt_temp_Entry = tk.Entry(
            self.tab_1, textvariable=self.advopt_temp)
        self.advopt_barostat_check = ttk.Checkbutton(
            self.tab_1, text="Barostat", variable=self.advopt_barostat,
            onvalue= True, offvalue= False,
            command=lambda: self._check_settings(
                'advopt_barostat', 'advopt_pressure_Entry',
                'advopt_barostat_steps_Entry', True))
        self.advopt_pressure_Entry = tk.Entry(
            self.tab_1, state='disabled', textvariable=self.advopt_pressure)
        self.advopt_barostat_steps_Entry = tk.Entry(
            self.tab_1, state='disabled', textvariable=self.advopt_pressure_steps)

        self.advopt_grid = [['Friction', self.advopt_friction_Entry],
                            ['Temperature', self.advopt_temp_Entry],
                            [self.advopt_barostat_check, ''],
                            ['Pressure', self.advopt_pressure_Entry],
                            ['Maximum Steps', self.advopt_barostat_steps_Entry]]
        self.auto_grid(self.advopt_conditions_lframe, self.advopt_grid)

        # Tab2
        self.advopt_system_lframe = tk.LabelFrame(
            self.tab_2, text='Set System Options')
        self.advopt_system_lframe.pack(expand=True, fill='both')

        self.advopt_nbm_combo = ttk.Combobox(
            self.tab_2, textvariable=self.advopt_nbm)
        self.advopt_nbm_combo.config(
            values=('NoCutoff', 'CutoffNonPeriodic', 'CutoffPeriodic', 'Ewald', 'PME'))
        self.advopt_cutoff_Entry = tk.Entry(
            self.tab_2, textvariable=self.advopt_cutoff)
        self.advopt_edwalderr_Entry = tk.Entry(
            self.tab_2, textvariable=self.advopt_edwalderr, state='disabled')
        self.advopt_constr_combo = ttk.Combobox(
            self.tab_2, textvariable=self.advopt_constr)
        self.advopt_constr_combo.config(
            values=('None', 'HBonds', 'HAngles', 'AllBonds'))
        self.advopt_rigwat_combo = ttk.Combobox(
            self.tab_2, textvariable=self.advopt_rigwat)
        self.advopt_rigwat_combo.config(
            values=('True', 'False'))

        self.advopt_grid = [['Non Bonded Method', self.advopt_nbm_combo],
                            ['Edwald Tolerance', self.advopt_edwalderr_Entry],
                            ['Non Bonded Cutoff', self.advopt_cutoff_Entry],
                            ['Constraints', self.advopt_constr_combo],
                            ['Rigid Water', self.advopt_rigwat_combo]]
        self.auto_grid(self.advopt_system_lframe, self.advopt_grid)
        # Events
        self.advopt_nbm_combo.bind("<<ComboboxSelected>>", self._PME_settings)

        # Tab3

        self.advopt_hardware_lframe = tk.LabelFrame(
            self.tab_3, text='Platform')
        self.advopt_hardware_lframe.pack(expand=True, fill='both')

        self.advopt_platform_combo = ttk.Combobox(
            self.tab_3, textvariable=self.advopt_hardware)
        self.advopt_platform_combo.config(values=('CPU', 'OpenCL', 'CUDA'))
        self.advopt_precision_combo = ttk.Combobox(
            self.tab_3, textvariable=self.advopt_precision)
        self.advopt_precision_combo.config(
            values=('single', 'mixed', 'double'))

        self.advopt_platform_grid = [['', ''],
                                     ['Platform', self.advopt_platform_combo],
                                     ['Precision', self.advopt_precision_combo]]
        self.auto_grid(self.advopt_hardware_lframe, self.advopt_platform_grid)

        # Initialize Variables
        self.advopt_friction.set(0.01)
        self.advopt_temp.set(300)
        self.advopt_barostat.set(0)
        self.advopt_nbm_combo.current(0)
        self.advopt_cutoff.set(1)
        self.advopt_constr_combo.current(0)
        self.advopt_rigwat_combo.current(0)
        self.advopt_platform_combo.current(0)
        self.advopt_precision_combo.current(0)

    def _PME_settings(self, event):
        """
        Enable or Disable Edwald Error Entry when
        CutoffNonPeriodic Combobox is selected
        """
        if self.advopt_nbm.get() == 'PME':
            self.advopt_edwalderr_Entry.configure(state='normal')
        else:
            self.advopt_edwalderr_Entry.configure(state='disabled')

    def _fill_inputopt_window(self):

        # Create TopLevel window
        self.inputopt_window = tk.Toplevel()
        self.Center('inputopt_window')
        self.inputopt_window.title("Advanced Options")
        # Create lframe
        self.advopt_input_lframe = tk.LabelFrame(
            self.inputopt_window, text='Initial Files')
        self.advopt_input_lframe.pack(expand=True, fill='both')
        # Fill lframe
        self.input_vel_Entry = tk.Entry(
            self.inputopt_window, textvariable=self.input_vel)
        self.input_vel_browse = tk.Button(
            self.inputopt_window, text='...', command=lambda: self._browse_file(self.input_vel, 'vel', ''))
        self.input_box_Entry = tk.Entry(
            self.inputopt_window, textvariable=self.input_box)
        self.input_box_browse = tk.Button(
            self.inputopt_window, text='...', command=lambda: self._browse_file(self.input_box, 'xsc', 'csv'))
        self.input_charmm_Entry = tk.Entry(
            self.inputopt_window, textvariable=self.input_charmm)
        self.input_charmm_browse = tk.Button(
            self.inputopt_window, text='...', command=lambda: self._browse_file(self.input_charmm, 'par', ''))
        self.input_checkpoint_Entry = tk.Entry(
            self.inputopt_window, textvariable=self.input_checkpoint)
        self.input_checkpoint_browse = tk.Button(
            self.inputopt_window, text='...', command=lambda: self._browse_file(self.input_checkpoint, 'xml', 'rst'))

        self.input_grid = [['Velocities', self.input_vel_Entry, self.input_vel_browse,
                            'Box', self.input_box_Entry, self.input_box_browse],
                           ['Restart File', self.input_checkpoint_Entry, self.input_checkpoint_browse]]
        self.auto_grid(self.advopt_input_lframe, self.input_grid)

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
