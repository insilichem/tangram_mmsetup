#!/usr/bin/env python
# encoding: utf-8

# Get used to importing this in your Py27 projects!
from __future__ import print_function, division
# Python stdlib
import os
import collections
import contextlib
# Chimera stuff
# Additional 3rd parties
# Own
import gui

"""
This module contains the business logic of your extension. Normally, it should
contain the Controller and the Model. Read on MVC design if you don't know about it.
"""


class Controller(object):

    """ 
    The controller manages the communication between the UI (graphic interface)
    and the data model. Actions such as clicks on buttons, enabling certain areas, 
    or runing external programs, are the responsibility of the controller.
    """

    def __init__(self, gui, model, *args, **kwargs):
        self.gui = gui
        self.model = model
        self.set_mvc()

    def set_mvc(self):
        # Tie model and gui
        self.model.variables_keys = list(self.model.variables.keys())
        for item in self.model.variables_keys:
            with ignored(AttributeError):
                var = getattr(self.model, '_' + item)
                var.trace(lambda *args: setattr(self.model, item, var.get()))

        self.gui.buttonWidgets['Run'].configure(command=self.run)

    def run(self):
        self.model.parse()
        print(self.model.variables)
        print('\n')
        return


class Model(object):

    """The model controls the data we work with. Normally, it'd be a Chimera molecule
    and some input files from other programs. The role of the model is to create
    a layer around those to allow the easy access and use to the data contained in
    those files"""

    def __init__(self, gui, *args, **kwargs):
        self.gui = gui
        self.variables= collections.OrderedDict()
        self.variables_stage = collections.OrderedDict()
        self.variables = {'path': None, 'positions': None, 'forcefield': None, 'charmm_parameters': None, 
                          'vel': None, 'box': None, 'restart': None, 'stdout': None, 'mdtraj' : None,
                          'trajectory_every': None, 'output': None, 'integrator': None,
                          'nonbondedMethod': None, 'nonbondedCutoff': None, 'ewaldErrorTolerance': None,
                          'constraints': None, 'rigidWater': False, 'platform':None, 'precision':None,
                          'timestep': None, 'barostat': False, 'temperature': None, 'friction': None, 
                          'pressure': None, 'barostat_every': None, "stdout_every": None,
                          'trajectory_every': None, 'trajectory_new_every': None, 'restart_every': None,
                          'trajectory_atom_subset': None, 'report': True, 'trajectory': None}
        self.variables_stage = {'name': None, 'temperature': None, 'pressure': None,
                                'barostat_every': None, 'barostat': False, 'constraint': None,
                                'constraint2': None, 'constraint3':None, 'minimization': False,
                                'minimization_max_steps': None, 'minimization_tolerance': None,
                                'reporters': False, 'steps': None, 'report_every': None }

    def parse(self):

        for item in self.variables.keys():
            self.variables[item] = getattr(self, item)

        try:
            if all(v for v in self.variables.viewvalues()):  # Python2.7
                return self.variables.values()

        except AttributeError:
            if all(v for v in self.variables.values()):  # Python 3
                return self.variables.values()

        self.stages()

    def stages(self):
        for name in self.gui.names:
            for i, variable in enumerate(getattr(self.gui, 'stage_' + name)):
                key = sorted(self.variables_stage.keys())
                self.variables_stage[key[i]] = variable
            setattr(self, 'variable_stage_' + name, self.variables_stage.copy())
            print(getattr(self, 'variable_stage_' + name))
            print('\n')


                   

    @property
    def path(self):
        return self.gui.var__path.get()

    @path.setter
    def path(self, value):
        if not os.path.isfile(value):
            raise ValueError('Cannot access file {}'.format(value))
        self.gui.var__path.set(value)

    @property
    def positions(self):
        return self.gui.var_positions.get()

    @positions.setter
    def positions(self, value):
        if not os.path.isfile(value):
            raise ValueError('Cannot access file {}'.format(value))
        self.gui.var_positions(value)

    @property
    def forcefield(self):
        forcefields = [os.path.join(os.path.dirname(os.path.realpath(self.gui.var_forcefield.get(
        )+'.xml')), self.gui.var_forcefield.get()+'.xml'), self.gui.var_external_forc.get()]
        return forcefields
    """No funciona real path"""

    """@path.setter
    def path(self, value):
        for f in forcefields:
            if not os.path.isfile(value):
                raise ValueError('Cannot access file {}'.format(value))
            setattr(self, .forcefield,value)"""

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
        return (self.gui.var_output.get() + '/stdout')

    @stdout.setter
    def stdout(self, value):
        self.gui.var_output.set(value)

    @property
    def mdtraj(self):
        return (self.gui.var_output.get() + '/mdtraj')

    @mdtraj.setter
    def mdtraj(self, value):
        self.gui.var_output.set(value)

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









    """
    Stages

    @property
    def minimization(self):
        return self.gui.stage_minimiz.get()

    @minimization.setter
    def minimization(self, value):
        self.gui.stage_minimiz.set(value)

    @property
    def tolerance(self):
        return self.gui.stage_minimiz_tolerance.get()

    @tolerance.setter
    def tolerance(self, value):
        self.gui.stage_minimiz_tolerance.set(value)

    @property
    def max_iterations(self):
        return self.gui.stage_minimiz_maxsteps.get()

    @max_iterations.setter
    def max_iterations(self, value):
        self.gui.stage_minimiz_maxsteps.set(value)    """


@contextlib.contextmanager
def ignored(*exceptions):
    try:
        yield
    except exceptions:
        pass
