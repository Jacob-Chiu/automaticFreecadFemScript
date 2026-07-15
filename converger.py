"""
This converger works by running FEM simulations with decreasing mesh sizes until their maximum stresses converge. 
Each iteration, the mesh size is decreased by a factor of "meshSizeDivider". 
The maximum stresses are stored in "maxStresses". 
The maximum percent error is stored in the variable "maxError" (e.g. 5% = 0.05). The maximum number of simulations the script will 
run until it gives up is "maxIterations".
"""


import sys
import os
cwd = os.path.dirname(os.path.abspath(__file__))
sys.path.append(cwd)
from automaticFem import *

workingDir = cwd + "/testing/convergerTest"
templateName = "beamTest.FCStd"
meshSizeVar = "elementSize"
meshSizeUnit = " mm"

maxStresses  = []
meshSize = 10
meshSizeDivider = 2
iterationLimit = 6
maxError = 0.02

auto = FemScript(workingDir, templateName, [meshSizeVar], [meshSizeUnit])
auto.printLog("Max. error is: " + str(maxError))
auto.printLog("Iteration limit is: " + str(iterationLimit))

while True:
	try: 
		auto.solveCondition([meshSize])
	except: 
		auto.printLog("=" * 50)
		auto.printLog("aborting convergence study")
		break
	maxStresses.append(auto.maxShearStress)
	auto.closeFile()
	auto.printLog("-" * 50) #major separator 

	#check if convergence has been reached
	try: 
		error = abs((maxStresses[-1] - maxStresses[-2]) / maxStresses[-1])
		auto.printLog("calculated an error of " + str(error))
	except: error = 1000
	#this occurs on the first iteration
	
	if(error < maxError): 
		auto.printLog("convergence achieved!")
		auto.printLog("=" * 50)
		auto.printLog("it took " + str(len(maxStresses)) +  " runs to achieve convergence")
		auto.printLog("FINAL MAX STRESS: " + str(maxStresses[-1]))
		break
	else:
		auto.printLog("convergence not achieved")
		auto.printLog("reducing mesh size")
		meshSize = meshSize / meshSizeDivider #compute new mesh size
		
	if(len(maxStresses) >= iterationLimit):
		auto.printLog("=" * 50) #major separator 
		auto.printLog("iteration limit reached")
		auto.printLog("last stress value was " + str(maxStresses[-1]))
		break
