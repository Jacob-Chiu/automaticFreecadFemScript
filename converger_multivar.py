import sys
import os
cwd = os.path.dirname(os.path.abspath(__file__))
sys.path.append(cwd)
from automaticFem import *

workingDir = cwd + "/testing/convergerMultivarTest"
templateName = "spherePlateTest.FCStd"
varList = ["elementSize", "clearanceAdjustment", "contactStiffness"]
unitList = [" um", " um", "*1000 GPa/m"]

elementSize = 100
elementSizeDivider = 2
clearanceAdjust = 16
clearanceAdjustDivider = 2
contactStiff = 500
contactStiffMultiplier = 2
maxError = 0.05
iterationLimit = 20
maxStresses = []

auto = FemScript(workingDir, templateName, varList, unitList)
auto.printLog("Max. error is: " + str(maxError))
auto.printLog("Iteration limit is: " + str(iterationLimit))

state = 1
while True:
	try:
		auto.solveCondition([elementSize, clearanceAdjust, contactStiff])
	except SolverError:
		pass
	except: 
		auto.printLog("=" * 50)
		auto.printLog("aborting convergence study")
		break
	
	maxStresses.append(auto.maxShearStress)
	auto.closeFile()
	auto.printLog("-" * 50)
	
	try:
		error = abs((maxStresses[-1] - maxStresses[-2]) / maxStresses[-1])
		auto.printLog("calculated an error of " + str(error))
	except: error = 1000 
	#this occurs for the first iteration, and also on the first iteration after decreasing element size
	
	if(maxStresses[-1] == None): #if solver failed
		auto.printLog("Decreasing element size and reverting clearance adjustment")
		elementSize = elementSize / elementSizeDivider
		clearanceAdjust = clearanceAdjust * clearanceAdjustDivider
		state = 1
	elif(state == 1): #converging clearance adjust + element size
		if(error > maxError): #if not converged
			auto.printLog("Clearance adjustment not converged, continue converging clearance adjustment")
			auto.printLog("Reducing clearance adjustment")
			clearanceAdjust = clearanceAdjust / clearanceAdjustDivider
		else:
			auto.printLog("Clearance adjustment converged, now converging contact stiffness.")
			auto.printLog("Reverting clearance adjustment and increasing contact stiffness.")
			clearanceAdjust = clearanceAdjust * clearanceAdjustDivider
			contactStiff = contactStiff * contactStiffMultiplier
			state = 2
	else: #state == 2; converging contact stiffness
		if(error > maxError):
			auto.printLog("Contact stiffness not converged, checking clearance adjustment convergence.")
			auto.printLog("Reducing clearance adjustment.")
			clearanceAdjust = clearanceAdjust / clearanceAdjustDivider
			state = 1
		else:
			auto.printLog("Contact stiffness converged. DONE!!! YAY!!!!")
			auto.printLog("=" * 50)
			auto.printLog("FINAL MAX STRESS: " + str(maxStresses[-1]))
			break
	
	if(len(maxStresses) >= iterationLimit):
		auto.printLog("=" * 50) #major separator 
		auto.printLog("iteration limit reached")
		auto.printLog("last stress value was " + str(maxStresses[-1]))
		break
