"""
This converger works by running FEM simulations with decreasing mesh sizes until their maximum stresses converge. 
Each iteration, the mesh size is decreased by a factor of "meshSizeDivider". 
A list of the mesh sizes in each simulation is stored in "meshSizes". The corresponding maximum stresses are stored in "maxStresses". 
The maximum percent error is stored in the variable "maxError" (e.g. 5% = 0.05). The maximum number of simulations the script will 
run until it gives up is "maxIterations".
"""


import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore
from PySide6.QtCore import QProcess
from femsolver.run import run_fem_solver
import time

#the following code allows automaticFem to be imported
import os
import sys
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)
from automaticFem import *

#OTHER VARIABLES + SETUP
workingDir = "/home/jacoby/Public/FEM/convergerTest/100000-2" #the directory that all the files are stored in
print("\n\n\nSTARTING AUTOMATIC FEM SCRIPT")
print("Working directory is:", workingDir)
baseFile = App.openDocument(workingDir + "/100000-2.FCStd")

maxStresses  = []
meshSizes = [0.2]
meshSizeDivider = 2
meshSizeUnit = " mm"
iterationLimit = 6
maxError = 0.05
print("Max. error is:", maxError)
print("Iteration limit is:", iterationLimit)

for i in range(iterationLimit):
	meshSize = str(meshSizes[-1]) + meshSizeUnit
	filePath = workingDir + "/" + meshSize + ".FCStd"
	
	file = makeFile(baseFile, filePath)

	#set mesh size in variable set
	varset = file.getObject("VarSet")
	varset.elementSize = meshSize
	print("recomputed" , file.recompute(), "objects")
	
	makeMesh(file)
	solveMesh(file)
	
	maxStress = max(file.getObject('CCX_Results').vonMises)	
	print("max. stress was", maxStress)
	maxStresses.append(maxStress)

	closeFile(file)

	#check if convergence has been reached
	try: err = abs((maxStress - maxStresses[-2]) / maxStress)
	except: err = 1000
	if(err < maxError): 
		print("=" * 50) #major separator 
		print("convergence reached between latest stress value of", maxStress, "and previous stress value of", maxStresses[-2])
		print("it took", len(maxStresses), "runs to achieve convergence")
		break

	meshSizes.append(meshSizes[-1] / meshSizeDivider) #compute new mesh size
	
if(not(err < maxError)):
	print("convergence was not reached. last stress values were", maxStresses[-1], "and", maxStresses[-2])

print("\n\nall max. stresses:", maxStresses)
print("all conditions:" , meshSizes)
