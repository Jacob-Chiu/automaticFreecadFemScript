import sys
sys.path.append("/home/jacoby/Documents/FreeCAD/automaticFreecadFemScript")
from automaticFem import FemScript

workingDir = "/home/jacoby/Documents/FreeCAD/GRT fea stuff/automated FEM script/runFromStringTest"
templateName = "test.FCStd"
varList = ["beamLength", "beamWidth", "elementSize", "force"]
unitList = [" mm"," mm"," mm"," N"]
auto = FemScript(workingDir, templateName, varList, unitList)

conditions = ["100-10-5-100", "200-10-5-100", "100-20-5-100","100-10-2-100","100-10-5-200"]

maxVMStresses = []
maxShearStresses = []
solveTimes = []

for condString in conditions:
	try:
		auto.solveString(condString)
	except:
		auto.printLog("aborting simulation")
	maxVMStresses.append(auto.maxVmStress)
	maxShearStresses.append(auto.maxShearStress)
	solveTimes.append(auto.solveTime)
	auto.closeFile()

auto.printLog("="*50)
auto.printLog("all conditions: " + str(conditions))
auto.printLog("all max. v.m. stresses: " + str(maxVMStresses))
auto.printLog("all max shear stresses: " + str(maxShearStresses))
auto.printLog("all times: " + str(solveTimes))
