"""
This is a script that iteratively runs FEM simulations of a single 3D model under different test conditions,
by changing variables of interest between simulations. Each test condition is stored as a string, 
containing the value for each variable of interest, and the variables of interest (e.g. the length and width 
of a beam) are recorded in a Variable Set. 

The script works by making a copy of the "base file", which contains the essential geometry and FEM constraints.
Then it modifies the variables in the copied file's Variable Set to match those of the test-condition string. 
Additionally, this program can modify the material of a simulation. After changing the variables, the script
re-meshes the mesh (so that the mesh reflects the changed geometry), and re-runs the simulation. Finally, it 
saves and closes the file. 

"condition" is a list of all the condition strings, with each variable separated by a "-"
"units" is a list of the units corresponding with each variable in the condition string.
	Since each unit is merely appended to the condition string's value (for example "10" + " mm" = "10 mm") and 
	given to FreeCAD to parse, you can also write expressions into the units. 
	For example, FreeCAD can parse "10" + "*10 mm" as 100 mm. 
"values" is a list of all the variable-plus-unit combinations, e.g. ["10 mm", "500 N", "12*5 mm"]. 
Assigning each variable in the condition string to one in the Variable Set must be done manually. 
	For example, "varset.beamWidth = values[1]" assigns beamWidth to the first variable. 
"""

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore
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
workingDir = "/home/jacoby/Public/FEM/spherePlateConvergence/timeTest" #the directory that all the files are stored in
print("\n\n\nSTARTING AUTOMATIC FEM SCRIPT")
print("Working directory is:", workingDir)
baseFile = App.openDocument(workingDir + "/test.FCStd")

conditions = ["50-4-2000","50-2-2000","50-1-2000","50-0.5-2000","50-0.25-2000","25-4-2000","25-2-2000","25-1-2000","25-0.5-2000","25-0.25-2000","12.5-4-2000","12.5-2-2000","12.5-1-2000","12.5-0.5-2000","12.5-0.25-2000"]

unit = [" um", " um", "*1000 GPa/m"]
maxVMStresses = []
maxShearStresses = []
solveTimes = []

for conditionString in conditions:
	filePath = workingDir + "/" + conditionString + ".FCStd"
	file = makeFile(baseFile, filePath)
	
	condition = conditionString.split("-")
	varset = file.getObject("VarSet")
	values = [condition[i] + unit[i] for i in range(len(condition))]
	print("simulation conditions are:", values)
	varset.elementSize = values[0]
	varset.clearanceAdjustment = values[1]
	varset.contactStiffness = values[2]
	print("recomputed" , file.recompute(), "objects")
	makeMesh(file)
	
	solveTimes.append(solveMesh(file))
	
	print("-" * 50) #minor separator  	
    
	try: 
		result = file.getObject('CCX_Results')
		maxVMStress = max(result.vonMises)
		maxShearStress = max(result.MaxShear)
		print("max. v.m. stress was", maxVMStress)
		print("max shear stress was", maxShearStress)
	except:
		maxVMStress = "NONE"
		maxShearStress = "NONE"
		print("ERROR: could not find maximum stress, probably some solver error.")
	maxVMStresses.append(maxVMStress)
	maxShearStresses.append(maxShearStress)
	closeFile(file)

print("="*50)
print("all conditions:", conditions)
print("all max. v.m. stresses:", maxVMStresses)
print("all max shear stresses:", maxShearStresses)
print("all times:", solveTimes)