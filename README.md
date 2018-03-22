# Tangram OpenMM GUI

A graphical interface to run OpenMM simulations in UCSF Chimera.

# Dependencies

This extension relies on [ommprotocol](https://github.com/insilichem/ommprotocol), which in turn depends on OpenMM, PDBFixer, MDTraj, ParmEd, OpenMolTools and some more. All of these requirements should be handled by the main [Tangram installer](https://github.com/insilichem/tangram).

# Quick Usage

1. Open any molecule on UCSF Chimera
2. Click on `Sanitize` to fix common problems with PDB files.
3. Add a new stage for the simulation. `ommprotocol` is designed to run all the steps of a MD protocol in the same job, saving you from the effort of chaining output and input files for each stage. However, in trivial cases, a single stage with minimization is enough.
4. Finally, the interface can be used for two different purposes:
    - Clicking on `Run`, OMMProtocol will be launched within UCSF Chimera with realtime coordinates updating (useful for teaching, for example).
    - Clicking on `Save Input`, an OMMProtocol input file (.yaml) will be generated so you can run `ommprotocol` separately (suitable for long runs in cluster computers).