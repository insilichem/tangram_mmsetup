#!/usr/bin/env python
# encoding: utf-8

# Get used to importing this in your Py27 projects!
from __future__ import print_function, division
# Python stdlib
import os
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
        print(self.model.variables.values())
        return


class Model(object):

    """The model controls the data we work with. Normally, it'd be a Chimera molecule
    and some input files from other programs. The role of the model is to create
    a layer around those to allow the easy access and use to the data contained in
    those files"""

    def __init__(self, gui, *args, **kwargs):
        self.gui = gui
        self.variables = {'path': None, 'positions': None, 'forcefield': None, 'charmm_parameters': None, 
                          'vel': None, 'box': None, 'restart': None, 'stdout': None, 'mdtraj' : None,
                          'trajectory_every': None, 'output': None, 'integrator': None,
                          'nonbondedMethod': None, 'nonbondedCutoff': None, 'ewaldErrorTolerance': None,
                          'constraints': None, 'rigidWater': False, 'platform':None, 'precision':None,
                          'timestep': None, 'barostat': False, 'temperature': None, 'friction': None, 
                          'pressure': None, 'barostat_every': None}

    def parse(self):

        for item in list(self.variables.keys()):
            print(item)
            self.variables[item] = getattr(self, item)

        try:
            if all(v for v in self.variables.viewvalues()):  # Python2.7
                return self.variables.values()

        except AttributeError:
            if all(v for v in self.variables.values()):  # Python 3
                return self.variables.values()

    @property
    def path(self):
        return self.gui._path.get()

    @path.setter
    def path(self, value):
        if not os.path.isfile(value):
            raise ValueError('Cannot access file {}'.format(value))
        self.gui._path.set(value)

    @property
    def positions(self):
        return self.gui.var_positions

    @positions.setter
    def positions(self, value):
        if not os.path.isfile(value):
            raise ValueError('Cannot access file {}'.format(value))
        self.gui.var_positions(value)

    @property
    def forcefield(self):
        forcefields = [os.path.join(os.path.dirname(os.path.realpath(self.gui.forcefield.get(
        )+'.xml')), self.gui.forcefield.get()+'.xml'), self.gui.external_forc.get()]
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
        return self.gui.parametrize_forc.get()

    @charmm_parameters.setter
    def charmm_parameters(self, value):
        if not os.path.isfile(value):
            raise ValueError('Cannot access file {}'.format(value))
        self.gui.parametrize_forc.set(value)

    @property
    def vel(self):
        return self.gui.input_vel.get()

    @vel.setter
    def vel(self, value):
        if not os.path.isfile(value):
            raise ValueError('Cannot access file {}'.format(value))
        self.gui.input_vel.set(value)

    @property
    def box(self):
        return self.gui.input_box.get()

    @box.setter
    def box(self, value):
        if not os.path.isfile(value):
            raise ValueError('Cannot access file {}'.format(value))
        self.gui.input_box.set(value)

    @property
    def restart(self):
        return self.gui.input_checkpoint.get()

    @restart.setter
    def restart(self, value):
        if not os.path.isfile(value):
            raise ValueError('Cannot access file {}'.format(value))
        self.gui.input_checkpoint.set(value)

    @property
    def stdout(self):
        return (self.gui.output.get() + '/stdout')

    @stdout.setter
    def stdout(self, value):
        self.gui.output.set(value)

    @property
    def mdtraj(self):
        return (self.gui.output.get() + '/mdtraj')

    @mdtraj.setter
    def mdtraj(self, value):
        self.gui.output.set(value)

    @property
    def trajectory_every(self):
        return self.gui.output_interval.get()

    @trajectory_every.setter
    def trajectory_every(self, value):
        self.gui.output_interval.set(value)

    @property
    def output(self):
        return self.gui.output.get()

    @output.setter
    def output(self, value):
        self.gui.output.set(value)

    @property
    def integrator(self):
        return self.gui.integrator.get()

    @integrator.setter
    def integrator(self, value):
        self.gui.integrator.set(value)


    @property
    def nonbondedMethod(self):
        return self.gui.advopt_nbm.get()

    @nonbondedMethod.setter
    def nonbondedMethod(self, value):
        self.gui.advopt_nbm.set(value)

    @property
    def nonbondedCutoff(self):
        return self.gui.advopt_cutoff.get()

    @nonbondedCutoff.setter
    def nonbondedCutoff(self, value):
        self.gui.advopt_cutoff.set(value)

    @property
    def ewaldErrorTolerance(self):
        return self.gui.advopt_edwalderr.get()

    @ewaldErrorTolerance.setter
    def ewaldErrorTolerance(self, value):
        self.gui.advopt_edwalderr.set(value)


    @property
    def rigidWater(self):
        return self.gui.advopt_rigwat.get()

    @rigidWater.setter
    def rigidWater(self, value):
        self.gui.advopt_rigwat.set(value) 


    @property
    def constraints(self):
        return self.gui.advopt_constr.get()

    @constraints.setter
    def constraints(self, value):
        self.gui.advopt_constr.set(value)

    @property
    def platform(self):
        return self.gui.advopt_hardware.get()

    @platform.setter
    def platform(self, value):
        self.gui.advopt_hardware.set(value)


    @property
    def precision(self):
        return self.gui.advopt_precision.get()

    @precision.setter
    def precision(self, value):
        self.gui.advopt_precision.set(value)


    @property
    def timestep(self):
        return self.gui.tstep.get()

    @timestep.setter
    def timestep(self, value):
        self.gui.tstep.set(value)

    @property
    def barostat(self):
        return self.gui.advopt_barostat.get()

    @barostat.setter
    def barostat(self, value):
        self.gui.self.advopt_barostat.set(value)

    @property
    def temperature(self):
        return self.gui.advopt_temp.get()

    @temperature.setter
    def temperature(self, value):
        self.gui.self.advopt_temp.set(value)

    @property
    def friction(self):
        return self.gui.advopt_friction.get()

    @friction.setter
    def friction(self, value):
        self.gui.self.advopt_friction.set(value)

    @property
    def pressure(self):
        return self.gui.advopt_pressure.get()

    @pressure.setter
    def pressure(self, value):
        self.gui.self.advopt_pressure.set(value)   



    @property
    def barostat_every(self):
        return self.gui.advopt_pressure_steps.get()

    @barostat_every.setter
    def barostat_every(self, value):
        self.gui.self.advopt_pressure_steps.set(value)   









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
