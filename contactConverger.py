import sys
import os
cwd = os.path.dirname(os.path.abspath(__file__))
sys.path.append(cwd)
from automaticFem import *

workingDir = cwd + "/testing/contactConverger"
templateName = "spherePlate.FCStd"
varList = ["elementSize", "clearanceAdjustment", "contactStiffness"]
unitList = [" um", " um", "*1000 GPa/m"]

elementSize = 100
elementSizeDivider = 2
minElementSize = 5

clearanceAdjust = 4
clearanceAdjustDivider = 2
minClearanceAdjust = 0.1

contactStiff = 1000
contactStiffMultiplier = 2
maxContactStiff = 10000

maxError = 0.05
iterationLimit = 30
maxStresses = []

auto = FemScript(workingDir, templateName, varList, unitList)
auto.printLog("Max. error is: " + str(maxError))
auto.printLog("Iteration limit is: " + str(iterationLimit))
auto.printLog("Minimum element size is: " + str(minElementSize))
auto.printLog("Minimum clearance adjustment is: " + str(minClearanceAdjust))
auto.printLog("Maximum contact stiffness is: " + str(maxContactStiff))

state = 10
while True:
	#check for exceeding limits
	if(len(maxStresses) >= iterationLimit):
		auto.printLog("ERROR: Iteration limit reached, aborting convergence study")
		break
	if(elementSize < minElementSize): 
		auto.printLog("ERROR: Minimum element size reached, aborting convergence study")
		break
	if(clearanceAdjust < minClearanceAdjust): 
		auto.printLog("ERROR: Minimum clearance adjustment reached, aborting convergence study")
		break
	if(contactStiff > maxContactStiff): 
		auto.printLog("ERROR: Maximum contact stiffness reached, aborting convergence study")
		break
	
	#run the solver
	try:
		auto.solveValues([elementSize, clearanceAdjust, contactStiff])
	except SolverError:
		pass
	except: 
		auto.printLog("aborting convergence study")
		break
	
	maxStresses.append(auto.maxShearStress)
	auto.closeFile()
	auto.printLog("-" * 50)
	
	#STATES: 
		#10 = converging clearance adjustment
		#20 = converging element size
		#21 = element size not converged; checking clearance adjustment
		#30 = converging stiffness
		#31 = stiffness not converged; checking clearance adjustment
		#40 = stiffness converged; checking element size
	
	#IF SOLVER FAILED
	if(maxStresses[-1] is None): 
		if(state == 10 or state == 21 or state == 31 or state == 30): #if failed after reducing clearance adjustment, or after increasing contact stiffness
			auto.printLog("Decreasing element size")
			elementSize = auto.roundSigFigs(elementSize / elementSizeDivider, 3)
		elif(state == 20): #if failed after reducing element size
			auto.printLog("Decreasing clearance adjustment")
			clearanceAdjust = auto.roundSigFigs(clearanceAdjust / clearanceAdjustDivider, 3)
		continue #try running the simulation again
	
	#IF SOLVER DID NOT FAIL
	
	#calculate error and convergence
	converged = False
	try:
		lastStress = maxStresses[-1]
		secondLastStress = next(stress for stress in reversed(maxStresses[0:-1]) if stress is not None) #find the second-last valid stress (not None)
		error = abs((lastStress - secondLastStress) / lastStress)
		auto.printLog("calculated an error of " + str(error))
	except(IndexError, StopIteration): error = 1000 #if only one successful simulation exists
	
	if(error < maxError):
		converged = True
		auto.printLog("Convergence was achieved")
	else:
		auto.printLog("Convergence was not achieved")
	
	#determine the new state
	if(state in (10,20,30)):
		if(converged):
			if(state == 20): elementSize = auto.roundSigFigs(elementSize * elementSizeDivider, 3)
			#revert element size to save computing time.
			state = state + 10
		else:
			state = state + 1
			if(state == 11): state = 10 #there is no state 11
	elif(state in (21,31)):
		if(converged):
			auto.printLog("Reverting clearance adjustment")
			clearanceAdjust = auto.roundSigFigs(clearanceAdjust * clearanceAdjustDivider, 3)
			state = state - 1
		else:
			state = 10
	elif(state == 40):
		if(converged):
			auto.printLog("FINAL CONVERGENCE ACHIEVED!!! YAY!!!")
			break
		else:
			state = 21
	else: raise ValueError("the variable 'state' equals " + str(state) + ", which is not a valid state value")
	
	#change simulation parameters based on the new state
	if(state in (10,21,31)):
		auto.printLog("Decreasing clearance adjustment")
		clearanceAdjust = auto.roundSigFigs(clearanceAdjust / clearanceAdjustDivider, 3)
	elif(state in (20,40)):
		auto.printLog("Decreasing element size.")
		elementSize = auto.roundSigFigs(elementSize / elementSizeDivider, 3)
	elif(state == 30):
		auto.printLog("Increasing contact stiffness.")
		contactStiff = auto.roundSigFigs(contactStiff * contactStiffMultiplier, 3)
		
auto.printLog("=" * 50)
auto.printLog("FINAL STRESS: " + str(maxStresses[-1]))
