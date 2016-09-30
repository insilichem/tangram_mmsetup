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
    def __init__(self,gui, model, *args, **kwargs):
        self.gui=gui
        self.model=model
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
        self.gui= gui
        self.variables = {'path' : None, 'positions' : None, 'forcefield' : None, 'charmm_parameters' : None, 'vel' : None, 
                            'box' : None, 'restart' : None, 'stdout': None, 'mdtraj' : None, 'interval' : None,
                            'output' : None}

    def parse(self):
        
        for item in list(self.variables.keys()):
            print(item)
            self.variables[item]= getattr(self, item)

        try:
            if all(v for v in self.variables.viewvalues()): #Python2.7
                return self.variables.values()
        
        except AttributeError:
            if all(v for v in self.variables.values()): #python 3
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
            return self.gui.var_positions.get()

            

    @positions.setter
    def positions(self, value):
        if not os.path.isfile(value):
            raise ValueError('Cannot access file {}'.format(value))
        self.gui.var_positions(value)


    @property
    def forcefield(self):
        forcefields = [os.path.join(os.path.dirname(os.path.realpath(self.gui.forcefield.get()+'.xml')),self.gui.forcefield.get()+'.xml'), self.gui.external_forc.get()]
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
        if not os.path.isfile(value):
            raise ValueError('Cannot access file {}'.format(value))
        self.gui.output.set(value)

    @property
    def mdtraj(self):
        return (self.gui.output.get() + '/mdtraj')
    
    @mdtraj.setter
    def mdtraj(self, value):
        if not os.path.isfile(value):
            raise ValueError('Cannot access file {}'.format(value))
        self.gui.output.set(value)

    @property
    def interval(self):
        return self.gui.output_interval.get()
    
    @interval.setter
    def interval(self, value):
        if not os.path.isfile(value):
            raise ValueError('Cannot access file {}'.format(value))
        self.gui.output_interval.set(value)

    @property
    def output(self):
        return self.gui.output.get()
    
    @output.setter
    def output(self, value):
        if not os.path.isfile(value):
            raise ValueError('Cannot access file {}'.format(value))
        self.gui.output.set(value)





@contextlib.contextmanager
def ignored(*exceptions):
    try:
        yield
    except exceptions:
        pass
    
        
