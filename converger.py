"""
This converger works by running FEM simulations with decreasing mesh sizes until their maximum stresses converge. 
Each iteration, the mesh size is decreased by a factor of "meshSizeDivider". 
A list of the mesh sizes in each simulation is stored in "meshSizes". The corresponding maximum stresses are stored in "maxStresses". 
The maximum percent error is stored in the variable "maxError" (e.g. 5% = 0.05). The maximum number of simulations the script will 
run until it gives up is "maxIterations".
"""


import sys
import os
cwd = os.path.dirname(os.path.abspath(__file__))
sys.path.append(cwd)
from automaticFem import FemScript

workingDir = cwd + "/testing/convergerTest"
templateName = "test.FCStd"
meshSizeVar = "elementSize"
meshSizeUnit = " mm"

maxStresses  = []
meshSize = 10
meshSizes = []
meshSizeDivider = 2
iterationLimit = 6
maxError = 0.02

auto = FemScript(workingDir, templateName, [meshSizeVar], [meshSizeUnit])
auto.printLog("Max. error is:" + str(maxError))
auto.printLog("Iteration limit is: " + str(iterationLimit))

while True:
	meshSizes.append(meshSize)
	try: 
		auto.solveCondition([meshSize])
	except: 
		auto.printLog("-" * 50)
		auto.printLog("aborting simulation")
		break
	maxStresses.append(auto.maxShearStress)
	auto.closeFile()

	#check if convergence has been reached
	try: err = abs((maxStresses[-1] - maxStresses[-2]) / maxStresses[-1])
	except: err = 1000
	if(err < maxError): 
		auto.printLog("=" * 50) #major separator 
		auto.printLog(	"convergence reached between latest stress value of " + str(maxStresses[-1]) + 
						" and previous stress value of " + str(maxStresses[-2]))
		auto.printLog("it took " + str(len(maxStresses)) +  " runs to achieve convergence")
		break
	elif(len(maxStresses) >= iterationLimit):
		auto.printLog("=" * 50) #major separator 
		auto.printLog(	"convergence was not reached. last stress values were " + 
						str(maxStresses[-1]) + " and " + str(maxStresses[-2]))
		break
	else:
		meshSize = meshSize / meshSizeDivider #compute new mesh size
	
print("\n\nall max. stresses:", maxStresses)
print("all conditions:" , meshSizes)
