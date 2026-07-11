#this is a test change
import FreeCAD as App
import FreeCADGui as Gui
import time
from femtaskpanels.task_solver_ccxtools import _TaskPanel as solverPanel
from femtaskpanels.task_mesh_gmsh import _TaskPanel as meshPanel
import psutil
import os 
from PySide import QtCore
import datetime

class FemScript:
	
	def __init__(self, workingDir, templateName, varList, unitList):
		#workingDir: a string specifying the working directory's path; template file, test cases, and log file all go in this directory
		#templateName: the name of the template file, including ".FCStd"
		#varList: a list of the names (strings) of the variables which must be set
		#unitList: a list of the units (strings) corresponding to the variables in varList
				# this can include mathematical expressions, for example "*10 mm"
				
		self.workingDir = workingDir
		self.templateFile = App.openDocument(workingDir + "/" + templateName)
		if(len(varList) != len(unitList)):
			self.printError("The list of variables and the list of units have different lengths!")
		self.varList = varList 
		self.unitList = unitList 
		
		self.printLog("\n\n\n")
		self.printLog("============NEW AUTOMATIC FEM SCRIPT============")
		self.printLog("Python script: " + __file__)
		self.printLog("working directory: " + workingDir)
		self.printLog("template file: " + templateName)
		self.printLog("variables: " + str(varList))
		self.printLog("units: " + str(unitList))
		
		self.currentDoc = None #the current document that is being modified/solved (a copy of the template)
		self.meshTime = None #time taken to create mesh
		self.meshExitCode = None #mesher exit code
		self.solveTime = None #time taken to solve simulation
		self.solveExitCode = None #solver exit code
		self.maxVmStress = None #max. von mises stress
		self.maxShearStress = None # max. shear stress
	
	def printLog(self, message): #prints a message to the shell, and also appends it to a log file
		print(message)
		message = str(datetime.datetime.now()) + "    " + str(message)
		with open(self.workingDir + "/log.txt", "a") as logFile:
			logFile.write(message)
			logFile.write("\n")

	def printError(self, message):
		errorMessage = "ERROR: " + str(message)
		self.printLog(errorMessage)
		raise Exception(message)
		
	def makeFile(self, fileName): #fileName should include the ".FCStd" extension
		self.printLog("=" * 50) #major separator
		if(self.currentDoc != None):
			self.printLog("previous file was open! closing it and writing new file")
			closeFile()
		path = self.workingDir + "/" + fileName
		self.printLog("writing file: " + path)
		if(os.path.isfile(path)):
			self.printError("file already exists.")
		self.templateFile.saveCopy(path)
		self.currentDoc = App.openDocument(path)
	
	def setVars(self, condList): 
	#sets the variables in varList to the numerical values in condList, with the units in unitList
		varset = self.currentDoc.getObject("VarSet")
		if(len(condList) != len(self.unitList)):
			self.printError("setVars was called with a list of conditions of the wrong length")
		for i in range(len(condList)):
			varset.__setattr__(self.varList[i], str(condList[i]) + self.unitList[i])
		self.currentDoc.recompute()
	
	def makeMesh(self): #meshes the file
		mesh = self.currentDoc.getObject('FEMMeshGmsh')
		panel = meshPanel(mesh) #this is necessary to create the meshing methods in mesh.Tool
		
		#occasionally, the mesher freezes. this code restarts the mesher if it runs for too long without exiting. 
		maxTime = 60 * 1000 # 60 * 1000 ms; sorry this is a handwavey magic number
		secondTry = False
		while True:
			self.printLog("-" * 50) #minor separator
			self.printLog("preparing mesh...")
			startTime = time.time() #record when preparation started
			mesh.Tool.prepare()
			self.printLog("done preparing. took " + str(time.time()-startTime) + " seconds")
			
			self.printLog("meshing...")
			startTime = time.time() #record when the meshing started
			mesh.Tool.compute()
			
			mesh.Tool.process.waitForFinished(maxTime) #wait until meshing finished, for a max. of maxTime milliseconds
			if(mesh.Tool.process.state().name == "NotRunning"): # if process finished
				self.meshTime = time.time()-startTime
				self.meshExitCode = mesh.Tool.process.exitCode()
				self.printLog("done meshing. took " + str(self.meshTime) + " seconds")
				self.printLog("exit status was " + mesh.Tool.process.exitStatus().name)
				self.printLog("exit code was " + str(self.meshExitCode))
				
				if(self.meshExitCode == 0): #if error code was not thrown
					self.printLog("meshing succeeded! recomputed " + str(self.currentDoc.recompute()) + " objects")
					break
				elif(secondTry == False): #if this is the first try
					mesh.Suppressed = True #this indicates that meshing failed
					self.printError("meshing failed on second try! suppressing mesh object")
					break
				else: #try again, and reset the max time. 
					secondTry = True
					maxTime = 60 * 1000 #60 * 1000 ms; magic number
					self.printLog("meshing failed! trying again")
			else: #if meshing timed out
				self.printLog("meshing timed out at " + str(maxTime/1000) + " seconds. killing and restarting...")
				mesh.Tool.process.kill() #kill and restart process
				mesh.Tool.process.waitForFinished(-1) #wait for it to actually stop running
				
				maxTime = maxTime * 4
				#large meshes will take a long time, and may trigger the timeout
				#so the timeout increases for subsequent attempts to allow large meshes to complete.
	
	def solveMesh(self):
		self.printLog("-" * 50) #minor separator
		
		solver = self.currentDoc.getObject("SolverCcxTools")
		panel = solverPanel(solver) #methods to write input file + run/stop solver are contained in a task panel
		
		startTime = time.time() #record start time
		self.printLog("writing input file...")
		panel.write_input_file_handler()
		self.printLog("done writing input file. took " + str(time.time() - startTime) + " seconds")
		
		startTime = time.time()
		vm = psutil.virtual_memory()
		self.printLog("solving...")
		
		done = False
		def helper():
			panel.runCalculix()
			while panel.Calculix.state().name != "NotRunning":
				panel.Calculix.waitForFinished(100) #check free memory every 10 seconds
				vm = psutil.virtual_memory()
				if(vm.available / vm.total < 0.05): #if >95% of memory is used, kill the solver
					panel.stopCalculix()
					self.solveExitCode = "OOM"
					self.printError("ran out of memory! killing solver")
			nonlocal done
			done = True
		
		QtCore.QTimer.singleShot(0, helper)
		#for reasons mysterious to me, the solver runs really slowly unless you do it in a Qt thread...
		while(not done): #wait for solver to finish
			time.sleep(0.001)
		
		self.solveTime = time.time() - startTime
		self.solveExitCode = panel.Calculix.exitCode()
		self.printLog("done solving. took " + str(self.solveTime) + " seconds")
		self.printLog("exit status was " + panel.Calculix.exitStatus().name)
		self.printLog("exit code was " + str(self.solveExitCode))
		
		
		if(self.solveExitCode != 0):
			self.printError("solving failed")
		else:
			self.maxVmStress = self.getMaxVmStress()
			self.maxShearStress = self.getMaxShearStress()
			self.printLog("solving succeeded!")
			self.printLog("max von Mises stress was " + str(self.maxVmStress))
			self.printLog("max shear stress was " + str(self.maxShearStress))
	
	def getMaxVmStress(self):
		try: 
			result = self.currentDoc.getObject('CCX_Results')
			return(max(result.vonMises))
		except:
			return None 
			
	def getMaxShearStress(self):
		try: 
			result = self.currentDoc.getObject('CCX_Results')
			return(max(result.MaxShear))
		except:
			return None
	
	def closeFile(self):
		if(self.currentDoc == None):
			return() #return if no test file is currently open
		Gui.SendMsgToActiveView("Save") #save file
		App.closeDocument(self.currentDoc.Name) #close file
		
		self.currentDoc = None
		self.meshTime = None
		self.meshExitCode = None
		self.solveTime = None
		self.solveExitCode = None
		self.maxVmStress = None
		self.maxShearStress = None
		
		self.printLog("saved and closed file")
	
	def solveCondition(self, condList):
	#creates and solves a simulation with variables in varList set to the values in condList
		if(len(condList) != len(self.unitList)):
			self.printError("solveCondition was called with a list of conditions of the wrong length")

		fileName = "-".join([str(i) for i in condList]) + ".FCStd"
		# solveCondition([1,2,3,4]) → "1-2-3-4.FCStd"
		self.makeFile(fileName)
		self.setVars(condList)
		self.makeMesh()
		self.solveMesh()
		
	def solveString(self, condString):
	#creates and solves a simulation with variables in varList defined by condString
	#condString is formatted with values separated by dashes, e.g. "1-2-3-4"
		condList = condString.split("-")
		self.solveCondition(condList)

if __name__ == "__main__":
	import sys
	import os
	cwd = os.path.dirname(os.path.abspath(__file__))
	sys.path.append(cwd)
	from automaticFem import FemScript
	
	workingDir = cwd + "/testing/automaticFemTest"
	templateName = "test.FCStd"
	varList = ["beamLength", "beamWidth", "elementSize", "force"]
	unitList = [" mm"," mm"," mm"," N"]
	auto = FemScript(workingDir, templateName, varList, unitList)
	auto.solveCondition([100,10,2,100])

