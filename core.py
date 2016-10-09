#!/usr/bin/env python
# encoding: utf-8

# Get used to importing this in your Py27 projects!
from __future__ import print_function, division
# Python stdlib
import os
import contextlib
# Own
import gui

"""
This module contains the business logic of your extension.
Normally, it should contain the Controller and the Model.
Read on MVC design if you don't know about it.
"""


class Controller(object):

    """
    The controller manages the communication
    between the UI (graphic interface)
    and the data model.
    Actions such as clicks on buttons,
    enabling certain areas,
    or runing external programs,
    are the responsibility of the controller.
    """

    def __init__(self, gui, model, *args, **kwargs):
        self.gui = gui
        self.model = model
        self.set_mvc()

    def set_mvc(self):
        # Tie model and gui
        self.model.variables_keys = self.model.variables.keys()
        with ignored(AttributeError):
            for item in self.model.variables_keys:
                var = getattr(self.model, '_' + item, False)
                var.trace(lambda item=item, value=var.get():
                          setattr(self.model, item, value))
        self.gui.buttonWidgets['Run'].configure(command=self.run)

    def run(self):
        self.model.parse()


class Model(object):

    """The model controls the data we work with.
    Normally, it'd be a Chimera molecule
    and some input files from other programs.
    The role of the model is to create
    a layer around those to allow the easy
    access and use to the data contained in
    those files"""

    def __init__(self, gui, *args, **kwargs):
        self.gui = gui
        self.variables = {'path': None, 'positions': None, 'forcefield': None,
                          'charmm_parameters': None, 'vel': None, 'box': None,
                          'restart': None, 'trajectory_every': None,
                          'output': None, 'stdout':None, 'integrator': None,
                          'nonbondedMethod': None, 'nonbondedCutoff': None,
                          'ewaldErrorTolerance': None, 'mdtraj':None,
                          'constraints': None, 'rigidWater': False, 'platform':None,
                          'precision':None, 'timestep': None, 'barostat': False,
                          'temperature': None, 'friction': None,'pressure': None,
                          'barostat_every': None, "stdout_every": None,
                          'trajectory_every': None, 'trajectory_new_every': None,
                          'restart_every': None, 'trajectory_atom_subset': None,
                          'report': True, 'trajectory': None}
        self.stages_name = []

    def parse(self):
        self.retrieve_settings()
        self.stages
        print(self.variables.items())
        print(self.stages)

    @property
    def stages(self):
        return self.gui.stages

    @property
    def path(self):
        return self.gui.var_path.get()

    @path.setter
    def path(self, value):
        if not os.path.isfile(value):
            raise ValueError('Cannot access file {}'.format(value))
        self.gui.var_path.set(value)

    @property
    def positions(self):
        return self.gui.var_positions.get()

    @positions.setter
    def positions(self, value):
        if not os.path.isfile(value):
            raise ValueError('Cannot access file {}'.format(value))
        self.gui.var_positions.set(value)

    @property
    def forcefield(self):
        forcefields = [os.path.join(os.path.dirname(
            self.gui.var_forcefield.get() + '.xml'),
            self.gui.var_forcefield.get() + '.xml'),
            self.gui.var_external_forc.get()]
        self.forcefields = forcefields + list(
            self.gui.var_forcefield_external.get())
        return self.forcefields

    @forcefield.setter
    def forcefield(self, value):
        self.gui.var_forcefield_external.set(value)
        self.gui.var_forcefield.set(value)

    @property
    def charmm_parameters(self):
        return self.gui.var_parametrize_forc.get()

    @charmm_parameters.setter
    def charmm_parameters(self, value):
        if not os.path.isfile(value):
            raise ValueError('Cannot access file {}'.format(value))
        self.gui.var_parametrize_forc.set(value)

    @property
    def vel(self):
        return self.gui.var_input_vel.get()

    @vel.setter
    def vel(self, value):
        if not os.path.isfile(value):
            raise ValueError('Cannot access file {}'.format(value))
        self.gui.var_input_vel.set(value)

    @property
    def box(self):
        return self.gui.var_input_box.get()

    @box.setter
    def box(self, value):
        if not os.path.isfile(value):
            raise ValueError('Cannot access file {}'.format(value))
        self.gui.var_input_box.set(value)

    @property
    def restart(self):
        return self.gui.var_input_checkpoint.get()

    @restart.setter
    def restart(self, value):
        if not os.path.isfile(value):
            raise ValueError('Cannot access file {}'.format(value))
        self.gui.var_input_checkpoint.set(value)

    @property
    def stdout(self):
        return os.path.join(self.gui.var_output.get(), self.gui.var_stdout_directory.get())

    @stdout.setter
    def stdout(self, value):
        self.gui.var_stdout_directory.set(value)

    @property
    def mdtraj(self):
        return os.path.join(self.gui.var_output.get(), self.gui.var_traj_directory.get())

    @mdtraj.setter
    def mdtraj(self, value):
        self.gui.var_traj_directory.set(value)

    @property
    def trajectory_every(self):
        return self.gui.var_output_interval.get()

    @trajectory_every.setter
    def trajectory_every(self, value):
        self.gui.var_output_interval.set(value)

    @property
    def output(self):
        return self.gui.var_output.get()

    @output.setter
    def output(self, value):
        self.gui.var_output.set(value)

    @property
    def integrator(self):
        return self.gui.var_integrator.get()

    @integrator.setter
    def integrator(self, value):
        self.gui.var_integrator.set(value)

    @property
    def nonbondedMethod(self):
        return self.gui.var_advopt_nbm.get()

    @nonbondedMethod.setter
    def nonbondedMethod(self, value):
        self.gui.var_advopt_nbm.set(value)

    @property
    def nonbondedCutoff(self):
        return self.gui.var_advopt_cutoff.get()

    @nonbondedCutoff.setter
    def nonbondedCutoff(self, value):
        self.gui.var_advopt_cutoff.set(value)

    @property
    def ewaldErrorTolerance(self):
        return self.gui.var_advopt_edwalderr.get()

    @ewaldErrorTolerance.setter
    def ewaldErrorTolerance(self, value):
        self.gui.var_advopt_edwalderr.set(value)

    @property
    def rigidWater(self):
        return self.gui.var_advopt_rigwat.get()

    @rigidWater.setter
    def rigidWater(self, value):
        self.gui.var_advopt_rigwat.set(value)

    @property
    def constraints(self):
        return self.gui.var_advopt_constr.get()

    @constraints.setter
    def constraints(self, value):
        self.gui.var_advopt_constr.set(value)

    @property
    def platform(self):
        return self.gui.var_advopt_hardware.get()

    @platform.setter
    def platform(self, value):
        self.gui.var_advopt_hardware.set(value)

    @property
    def precision(self):
        return self.gui.var_advopt_precision.get()

    @precision.setter
    def precision(self, value):
        self.gui.var_advopt_precision.set(value)

    @property
    def timestep(self):
        return self.gui.var_tstep.get()

    @timestep.setter
    def timestep(self, value):
        self.gui.tstep.var_set(value)

    @property
    def barostat(self):
        return self.gui.var_advopt_barostat.get()

    @barostat.setter
    def barostat(self, value):
        self.gui.self.var_advopt_barostat.set(value)

    @property
    def temperature(self):
        return self.gui.var_advopt_temp.get()

    @temperature.setter
    def temperature(self, value):
        self.gui.self.var_advopt_temp.set(value)

    @property
    def friction(self):
        return self.gui.var_advopt_friction.get()

    @friction.setter
    def friction(self, value):
        self.gui.self.var_advopt_friction.set(value)

    @property
    def pressure(self):
        return self.gui.var_advopt_pressure.get()

    @pressure.setter
    def pressure(self, value):
        self.gui.self.var_advopt_pressure.set(value)

    @property
    def barostat_every(self):
        return self.gui.var_advopt_pressure_steps.get()

    @barostat_every.setter
    def barostat_every(self, value):
        self.gui.self.var_advopt_pressure_steps.set(value)

    @property
    def trajectory_every(self):
        return self.gui.var_output_traj_interval.get()

    @trajectory_every.setter
    def trajectory_every(self, value):
        self.gui.self.var_output_traj_interval.set(value)

    @property
    def stdout_every(self):
        return self.gui.var_output_stdout_interval.get()

    @stdout_every.setter
    def stdout_every(self, value):
        self.gui.self.var_output_stdout_interval.set(value)

    @property
    def verbose(self):
        return self.gui.var_verbose.get()

    @verbose.setter
    def verbose(self, value):
        self.gui.self.var_verbose.set(value)

    @property
    def trajectory_new_every(self):
        return self.gui.var_traj_new_every.get()

    @trajectory_new_every.setter
    def trajectory_new_every(self, value):
        self.gui.self.var_traj_new_every.set(value)

    @property
    def restart_every(self):
        return self.gui.var_restart_every.get()

    @restart_every.setter
    def restart_every(self, value):
        self.gui.self.var_restart_every.set(value)

    @property
    def trajectory(self):
        return self.gui.var_md_reporters.get()

    @trajectory.setter
    def trajectory(self, value):
        self.gui.self.var_md_reporters.set(value)

    @property
    def trajectory_atom_subset(self):
        return self.gui.var_traj_atoms.get()

    @trajectory_atom_subset.setter
    def trajectory_atom_subset(self, value):
        self.gui.self.var_traj_atoms.set(value)

    @property
    def report(self):
        if self.gui.var_md_reporters.get() == 'None':
            return False
        else:
            return True

    def retrieve_settings(self):
        for key in self.variables:
            self.variables[key] = getattr(self, key)
        return self.variables.items()

@contextlib.contextmanager
def ignored(*exceptions):
    try:
        yield
    except exceptions:
        pass
