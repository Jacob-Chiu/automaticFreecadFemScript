# An Automatic FreeCAD FEM Macro!!!

This is a Python library for FreeCAD that is meant to eliminate the tedious monkey-work associated with running iterations of the same basic FEM simulation. For example, it can be used to run convergence studies automatically, or do parametric studies. 

The intended workflow of this library is to:
	- make copies of a template simulation file
	- modify some variables in a Variable Set to set simulation/model parameters (e.g. dimensions, mesh size, etc.)
	- mesh and run the simulation
	- record the results
	- close the simulation file so that another can be opened. 

Documentation of methods and instance variables is here in documentation.txt

Read more about it at https://jacobchiu.com/automatic-freecad-fem-library/

