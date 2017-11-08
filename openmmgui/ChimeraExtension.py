#!/usr/bin/env python
# encoding: utf-8

# get used to importing this in your Py27 projects!
from __future__ import print_function, division
import chimera.extension


# Edit the name
class OpenMMExtension(chimera.extension.EMO):

    def name(self):
        # Always prefix with 'Plume'
        return 'Plume OpenMM GUI'

    def description(self):
        # Something short but meaningful
        return "Run MD simulations with OpenMM"

    def categories(self):
        # Don't touch
        return ['InsiliChem']

    def icon(self):
        # To be implemented
        return

    def activate(self):
        # Don't edit unless you know what you're doing
        self.module('gui').showUI()

# Remember to edit the class name in this call!
chimera.extension.manager.registerExtension(OpenMMExtension(__file__))