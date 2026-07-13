import sys
import os
cwd = os.path.dirname(os.path.abspath(__file__))
sys.path.append(cwd)
from automaticFem import FemScript

workingDir = cwd + "/testing/runFromStringTest"
templateName = "beamTest.FCStd"
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
		auto.printLog("-" * 50)
		auto.printLog("aborting simulation")
	auto.closeFile()
