# LAMMPS

## what is lammps

LAMMPS is a classical molecular dynamics simulation code designed to
run efficiently on parallel computers.  It was developed at Sandia
National Laboratories, a US Department of Energy facility, with
funding from the DOE.  It is an open-source code, distributed freely
under the terms of the GNU Public License (GPL) version 2.


## what is the output of lammps
log file of thermodynamic info, text dump files of atom coordinates, velocities, other per-atom quantities, dump output on fixed and variable intervals, based timestep or simulated time, binary restart files, parallel I/O of dump and restart files, per-atom quantities (energy, stress, centro-symmetry parameter, CNA, etc.). user-defined system-wide (log file) or per-atom (dump file) calculations
custom partitioning (chunks) for binning, and static or dynamic grouping of atoms for analysis spatial, time, and per-chunk averaging of per-atom quantities time averaging and histogramming of system-wide quantities atom snapshots in native, XYZ, XTC, DCD, CFG, NetCDF, HDF5, ADIOS2, YAML formats on-the-fly compression of output and decompression of read in files.

## lammps tutorial
Please refer to this [website](https://docs.lammps.org/) for more details.