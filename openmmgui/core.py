#!/usr/bin/env python
# encoding: utf-8

# Get used to importing this in your Py27 projects!
from __future__ import print_function, division
# Python
import os
import sys
from threading import Thread
from Queue import LifoQueue, Empty
from tkFileDialog import asksaveasfilename
import pickle
import numpy as np
import yaml
import chimera
from chimera.SubprocessMonitor import Popen, PIPE, SubprocessTask
from chimera.tasks import Task
from Movie.gui import MovieDialog


def enqueue_output(out, queue):
    while True:
        line = out.readline()
        if line == b'STARTOFCHUNK\n':
            lines = []
            for line in iter(out.readline, b'ENDOFCHUNK\n'):
                lines.append(line)
            queue.put(b''.join(lines))
        elif line == b'':
            break


class Controller(object):

    def __init__(self, gui, model, *args, **kwargs):
        self.gui = gui
        self.model = model
        self.set_mvc()
        self.task = None
        self.subprocess = None
        self.queue = None
        self.progress = None
        self.ensemble = None
        self.movie_dialog = None
        self._last_steps = 0

    def set_mvc(self):
        self.gui.buttonWidgets['Save Input'].configure(command=self.saveinput)
        self.gui.buttonWidgets['Run'].configure(command=self.run)

    def run(self):
        env = os.environ.copy()
        env['OMMPROTOCOL_SLAVE'] = '1'
        env['PYTHONIOENCODING'] = 'latin-1'
        self.saveinput()
        self.task = Task("OMMProtocol for {}".format(self.filename), cancelCB=self._clear_cb,
                         statusFreq=((1,),1))
        self.subprocess = Popen(['ommprotocol', self.filename], stdout=PIPE, stderr=PIPE,
                                progressCB=self._progress_cb, #universal_newlines=True,
                                bufsize=1, env=env)
        self.progress = SubprocessTask("OMMProtocol", self.subprocess,
                                       task=self.task, afterCB=self._after_cb)
        self.task.updateStatus("Running OMMProtocol")
        self.queue = LifoQueue()
        thread = Thread(target=enqueue_output, args=(self.subprocess.stdout, self.queue))
        thread.daemon = True  # thread dies with the program
        thread.start()
        m = self.gui.ui_chimera_models.getvalue()
        self.ensemble = _TrajProxy()
        self.ensemble.molecule = m
        self.ensemble.name = 'Trajectory for {}'.format(m.name)
        self.ensemble.startFrame = 1
        self.ensemble.endFrame = 1
        self.movie_dialog = MovieDialog(self.ensemble, externalEnsemble=True)

    def _clear_cb(self, *args):
        self.task.finished()
        self.task, self.subprocess, self.queue, self.progress = None, None, None, None

    def _after_cb(self, aborted):
        if aborted:
            self.task.finished()
            self._clear_cb()
            return
        if self.subprocess.returncode:
            last = self.subprocess.stderr.readlines()[-1]
            chimera.statusline.show_message(last)
            self.task.updateStatus("OMMProtocol calculation failed! Reason: {}".format(last))
            self._clear_cb()
            return
        self.task.finished()
        chimera.statusline.show_message('Yay! MD Done!')

    def _progress_cb(self, process):
        try:
            chunk = self.queue.get_nowait()
        except Empty:
            return self._last_steps / self.model.total_steps 
        
        steps, positions = pickle.loads(chunk)
        if steps == self._last_steps:
            self._last_steps / self.model.total_steps

        self._last_steps = steps        
        coordinates = np.array(positions) * 10.
        molecule = self.gui.ui_chimera_models.getvalue()
        coordsets_so_far = len(molecule.coordSets)
        cs = molecule.newCoordSet(coordsets_so_far)
        cs.load(coordinates)
        self.ensemble.endFrame = self.movie_dialog.endFrame = coordsets_so_far + 1
        self.movie_dialog.moreFramesUpdate('', [], self.movie_dialog.endFrame)
        self.movie_dialog.plusCallback()

        return self._last_steps / self.model.total_steps 

    def saveinput(self, path=None):
        self.model.parse()
        if path is None:
            path = asksaveasfilename(defaultextension='.yaml', filetypes=[('YAML', '*.yaml')])
        if not path:
            return
        self.write(path)
        self.gui.status('Written to {}'.format(path), color='blue', blankAfter=4)

    def write(self, output):
        # Write input
        self.filename = output
        with open(self.filename, 'w') as f:
            f.write('# Yaml input for OpenMM MD\n\n')
            f.write('# input\n')
            yaml.dump(self.model.md_input, f, default_flow_style=False)
            f.write('\n')
            f.write('# output\n')
            yaml.dump(self.model.md_output, f, default_flow_style=False)
            if self.model.md_hardware:
                f.write('\n# hardware\n')
                yaml.dump(self.model.md_hardware, f, default_flow_style=False)
            f.write('\n# conditions\n')
            yaml.dump(self.model.md_conditions, f, default_flow_style=False)
            f.write('\n# OpenMM system options\n')
            yaml.dump(self.model.md_systemoptions, f, default_flow_style=False)
            f.write('\n\nstages:\n')
            for stage in self.model.stages:
                yaml.dump([stage], f, indent=8, default_flow_style=False)
                f.write('\n')


class _TrajProxy:

    def __len__(self):
        return len(self.molecule.coordSets)

    def __getitem__(self, key):
        return None


class Model(object):

    def __init__(self, gui, *args, **kwargs):
        self.gui = gui
        self.total_steps = None
        self.md_input = {'topology': None,
                         'positions': None,
                         'forcefield': None,
                         'charmm_parameters': None,
                         'velocities': None,
                         'box_vectors': None,
                         'checkpoint': None}

        self.md_output={'project_name': None,
                        'restart': None,
                        'trajectory_every': None,
                        'outputpath': None,
                        'report_every': None,
                        'trajectory_every': None,
                        'trajectory_new_every': None,
                        'restart_every': None,
                        'trajectory_atom_subset': None,
                        'report': True,
                        'trajectory': None}

        self.md_hardware={'platform':None,
                          'precision': None}

        self.md_conditions={'timestep': None,
                            'integrator': None,
                            'barostat': False,
                            'temperature': None,
                            'friction': None,
                            'pressure': None,
                            'barostat_interval': None}

        self.md_systemoptions ={'nonbondedMethod': None,
                                'nonbondedCutoff': None,
                                'ewaldErrorTolerance': None,
                                'constraints': None,
                                'rigidWater': False}

    @property
    def stages(self):
        return self.gui.stages

    @property
    def project_name(self):
        return self.gui.var_output_projectname.get()

    @property
    def topology(self):
        if self.gui.ui_input_note.index(self.gui.ui_input_note.select()):
            return self.gui.var_path.get()
        # else:
        model = self.gui.ui_chimera_models.getvalue()
        if model:
            sanitized_path = '{0[0]}{1}{0[1]}'.format(os.path.splitext(model.name), '_fixed')
            if os.path.isfile(sanitized_path):
                return sanitized_path
            else:
                output = getattr(model, 'openedAs', (model.name + '.pdb',))[0]
                chimera.pdbWrite([model], chimera.Xform(), output)
                return output

    @topology.setter
    def topology(self, value):
        if not os.path.isfile(value):
            raise ValueError('Cannot access file {}'.format(value))
        self.gui.var_path.set(value)

    @property
    def positions(self):
        if self.gui.ui_input_note.index(self.gui.ui_input_note.select()) == 0:
            return self.topology
        elif self.gui.ui_input_note.index(self.gui.ui_input_note.select()) == 1:
            return self.gui.var_positions.get()

    @positions.setter
    def positions(self, value):
        if not os.path.isfile(value):
            raise ValueError('Cannot access file {}'.format(value))
        self.gui.var_positions.set(value)

    @property
    def forcefield(self):
        return [self.gui.var_forcefield.get() + '.xml', ] + self.gui.additional_force

    @forcefield.setter
    def forcefield(self, value):
        self.gui.additional_force.set(value)
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
    def velocities(self):
        return self.gui.var_input_vel.get()

    @velocities.setter
    def velocities(self, value):
        if not os.path.isfile(value):
            raise ValueError('Cannot access file {}'.format(value))
        self.gui.var_input_vel.set(value)

    @property
    def box_vectors(self):
        return self.gui.var_input_box.get()

    @box_vectors.setter
    def box_vectors(self, value):
        if not os.path.isfile(value):
            raise ValueError('Cannot access file {}'.format(value))
        self.gui.var_checkpoint.set(value)

    @property
    def checkpoint(self):
        return self.gui.var_checkpoint.get()

    @checkpoint.setter
    def checkpoint(self, value):
        if not os.path.isfile(value):
            raise ValueError('Cannot access file {}'.format(value))
        self.gui.var_checkpoint.set(value)

    @property
    def restart(self):
        return self.gui.var_output_restart.get()

    @restart.setter
    def restart(self, value):
        if not os.path.isfile(value):
            raise ValueError('Cannot access file {}'.format(value))
        self.gui.var_output_restart.set(value)

    @property
    def outputpath(self):
        return self.gui.var_output.get()

    @outputpath.setter
    def outputpath(self, value):
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
        value = self.gui.var_advopt_hardware.get()
        if value.lower() != 'auto':
            return value

    @platform.setter
    def platform(self, value):
        self.gui.var_advopt_hardware.set(value)

    @property
    def precision(self):
        if self.platform:
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
    def barostat_interval(self):
        return self.gui.var_advopt_pressure_steps.get()

    @barostat_interval.setter
    def barostat_interval(self, value):
        self.gui.self.var_advopt_pressure_steps.set(value)

    @property
    def trajectory(self):
        return self.gui.var_md_reporters.get()

    @trajectory.setter
    def trajectory(self, value):
        self.gui.self.var_md_reporters.set(value)

    @property
    def trajectory_every(self):
        if self.trajectory != 'None':
            return self.gui.var_output_traj_interval.get()

    @trajectory_every.setter
    def trajectory_every(self, value):
        self.gui.self.var_output_traj_interval.set(value)

    @property
    def report(self):
        return self.gui.var_verbose.get()

    @property
    def report_every(self):
        if self.report.lower()== 'true':
            return self.gui.var_output_stdout_interval.get()

    @report_every.setter
    def report_every(self, value):
        self.gui.self.var_output_stdout_interval.set(value)

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
    def trajectory_atom_subset(self):
        return self.gui.var_traj_atoms.get()

    @trajectory_atom_subset.setter
    def trajectory_atom_subset(self, value):
        self.gui.self.var_traj_atoms.set(value)

    def parse(self):
        self.reset_variables()
        self.retrieve_settings()
        if self.md_hardware.get('platform'):
            precision = self.md_hardware.get('precision')
            if precision:
                self.md_hardware['platform_properties'] = {'Precision': precision }
        self.retrieve_stages()
        if not self.stages:
            raise ValueError('Add at least one stage')

    def retrieve_settings(self):
        dictionaries=[self.md_input, self.md_output, self.md_hardware,
                      self.md_conditions, self.md_systemoptions]
        for dictionary in dictionaries:
            for key, value in dictionary.items():
                # Some combobox just returns boolean as a string so we fix that
                value_to_store = getattr(self, key)
                if value_to_store == 'True':
                    value_to_store = True
                elif value_to_store == 'False':
                    value_to_store = False
                if isinstance(value_to_store, bool):
                    dictionary[key] = value_to_store
                elif value_to_store == 'None':
                    del dictionary[key]
                elif value_to_store:
                    dictionary[key] = value_to_store
                else:
                    del dictionary[key]

    def retrieve_stages(self):
        steps = 0
        for dictionary in self.stages:
            steps += int(dictionary['steps'])
            for key, value in dictionary.items():
                if value == 'True':
                    value = True
                    dictionary[key] = value
                elif value == 'False':
                    value = False
                    dictionary[key] = value
                elif value in [None,'None']:
                    del dictionary[key]
        self.total_steps = steps

    def reset_variables(self):
        self.md_input = {'topology': None,
                         'positions': None,
                         'forcefield': None,
                         'charmm_parameters': None,
                         'velocities': None,
                         'box_vectors': None,
                         'checkpoint': None}

        self.md_output = {'project_name': None,
                          'restart': None,
                          'trajectory_every': None,
                          'outputpath': None,
                          'report_every': None,
                          'trajectory_every': None,
                          'trajectory_new_every': None,
                          'restart_every': None,
                          'trajectory_atom_subset': None,
                          'report': True,
                          'trajectory': None}

        self.md_hardware = {'platform': None,
                            'precision': None}

        self.md_conditions = {'timestep': None,
                              'integrator': None,
                              'barostat': False,
                              'temperature': None,
                              'friction': None,
                              'pressure': None,
                              'barostat_interval': None}

        self.md_systemoptions = {'nonbondedMethod': None,
                                 'nonbondedCutoff': None,
                                 'ewaldErrorTolerance': None,
                                 'constraints': None,
                                 'rigidWater': False}
