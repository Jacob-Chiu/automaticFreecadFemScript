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
workingDir = "/home/jacoby/Public/FEM/spherePlateConvergence/autoConvergerTest" #the directory that all the files are stored in
print("\n\n\nSTARTING AUTOMATIC FEM SCRIPT")
print("Working directory is:", workingDir)
baseFile = App.openDocument(workingDir + "/test.FCStd")

elementSize = 100
clearanceAdjust = 16
contactStiff = 500
conditions = []
maxVMStresses = []
maxShearStresses = []
solveTimes = []

state = 1
# 1 = converging clearance adjust + element size
# 2 = converging contact stiffness
maxError = 0.05
print("maximum error is", maxError)

while True:
	conditionString = str(elementSize) + "-" + str(clearanceAdjust) + "-" + str(contactStiff)
	conditions.append(conditionString)
	filePath = workingDir + "/" + conditionString + ".FCStd"
	file = makeFile(baseFile, filePath)
	
	varset = file.getObject("VarSet")
	varset.elementSize = str(elementSize) + " um"
	varset.clearanceAdjustment = str(clearanceAdjust) + " um"
	varset.contactStiffness = str(contactStiff) + "*1000 GPa/m"
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
	
	try:
		error = (maxShearStresses[-1] - maxShearStresses[-2]) / maxShearStresses[-2]
		print("calculated an error of", error)
	except: 
		error = 100 #this occurs for the first iteration, and also on the first iteration after decreasing element size
		print("could not determine error")
		
	if(maxShearStresses[-1] == "NONE"): #if not solved
		print("Decreasing element size and reverting clearance adjustment.")
		elementSize = elementSize / 2
		clearanceAdjust = clearanceAdjust * 2
		state = 1
	elif(state == 1):
		if(abs(error) > maxError): #if not converged
			print("Clearance adjustment not converged, reducing clearance adjustment.")
			clearanceAdjust = clearanceAdjust / 2
		else:
			print("Clearance adjustment converged, now converging contact stiffness. Reverting clearance adjustment and increasing contact stiffness.")
			clearanceAdjust = clearanceAdjust * 2
			contactStiff = contactStiff * 2
			state = 2
	else: #state == 2
		if(abs(error) > maxError):
			print("Contact stiffness not converged, checking clearance adjustment convergence. Reducing clearance adjustment.")
			clearanceAdjust = clearanceAdjust / 2
			state = 1
		else:
			print("Contact stiffness converged. DONE!!! YAY!!!!")
			print("FINAL MAX SHEAR STRESS:", maxShearStress)

print("="*50)
print("all conditions:", conditions)
print("all max. v.m. stresses:", maxVMStresses)
print("all max shear stresses:", maxShearStresses)
print("all times:", solveTimes)