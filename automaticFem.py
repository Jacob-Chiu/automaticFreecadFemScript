#this is a test change
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore
import time
from femtools.ccxtools import CcxTools
	
class CcxToolsScripted(CcxTools):
	def run(self): #basically the same as the parent "run" function, but does not create messages boxes for errors. 
		self.update_objects()
		self.setup_working_dir()

		message = self.check_prerequisites()
		if message:
			text = "CalculiX can not be started due to missing prerequisites:\n"
			error_app = f"{text}{message}"
			error_gui = f"{text}\n{message}"
			App.Console.PrintError(error_app)
			return False

		self.write_inp_file()
		if self.inp_file_name == "":
			error_message = "Error on writing CalculiX input file.\n"
			App.Console.PrintError(error_message)
			return False

		App.Console.PrintLog("Writing CalculiX input file completed.\n")
		ret_code = self.ccx_run()
		if ret_code is None:
			error_message = "CalculiX has not been run. The CalculiX binary search returned: {}.\n".format(self.ccx_binary_present)
			App.Console.PrintError(error_message)
			return False
		if ret_code != 0:
			error_message = f"CalculiX finished with error {ret_code}.\n"
			App.Console.PrintError(error_message)
			return False
		App.Console.PrintLog("Try to read result files\n")
		self.load_results()
		return True

class FemScript:
	
	def __init__(self, workingDir, templateName, varList, unitList):
		self.workingDir = workingDir
		self.templateFile = App.openDocument(workingDir + "/" + templateName)
		self.currentDoc = None
		if(len(varList) != len(unitList)):
			raise Exception("The list of variables and the list of units have different lengths!")
		self.varList = varList
		self.unitList = unitList
	
	def printLog(self, message):
		print(message)
		with open(self.workingDir + "/log.txt", "a") as logFile:
			logFile.write(message)
			logFile.write("\n")
	
	def makeFile(self, fileName):
		self.printLog("=" * 50) #major separator
		path = self.workingDir + "/" + fileName
		self.printLog("writing file: " + path)
		self.templateFile.saveCopy(path)
		self.currentDoc = App.openDocument(path)
	
	def setVars(self, condList):
		varset = self.currentDoc.getObject("VarSet")
		if(len(condList) != len(self.unitList)):
			raise Exception("The list of conditions is the wrong length!")
		for i in range(len(condList)):
			varset.__setattr__(self.varList[i], str(condList[i]) + self.unitList[i])
	
	def makeMesh(self):
		maxTime = 60 * 1000 # 60000 ms
		mesh = self.currentDoc.getObject('FEMMeshGmsh')
		mesh.ViewObject.doubleClicked() #it is necessary to open the mesh task panel to create the "Tool" object
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
				self.printLog("done meshing. took " + str(time.time()-startTime) + " seconds")
				break
			else:
				self.printLog("meshing timed out at " + str(maxTime/1000) + " seconds. aborting and restarting...")
				mesh.Tool.process.kill() #kill and restart process
				maxTime = maxTime * 4
		
		self.printLog("exit status was " + mesh.Tool.process.exitStatus().name)
		if(not(mesh.Tool.process.exitCode() == 0)): #if error code thrown
			self.printLog("meshing failed! suppressing mesh object")
			mesh.Suppressed = True #this indicates that meshing failed
		else:
			self.printLog("meshing succeeded! recomputed " + str(self.currentDoc.recompute()) + " objects")
		Gui.Control.closeDialog() #close task panel
	
	def runSolver(self):
		solver = self.currentDoc.getObject('SolverCcxTools')
		if(solver.Proxy.Type != 'Fem::SolverCcxTools'): return
		App.Console.PrintMessage("Run of CalxuliX ccx tools solver started.\n")
		fea = CcxToolsScripted(solver)
		fea.reset_mesh_purge_results_checked()
		fea.run() # standard, no working dir is given in solver
		App.Console.PrintMessage("Run of CalxuliX ccx tools solver finished.\n")
	
	def solveMesh(self):
		mesh = self.currentDoc.getObject("FEMMeshGmsh")
		done = False
		def runUpdateSolver(): #runs the solver and updates "done" when it is done
			nonlocal done
			self.runSolver()
			done = True
		
		if(mesh.Suppressed == True): #if meshing failed, do not solve
			self.printLog("Cancelling solver")
			return
			
		self.printLog("-" * 50) #minor separator
		self.printLog("solving...")
		startTime = time.time() #record solver start time
		QtCore.QTimer.singleShot(0, lambda: runUpdateSolver()) #start solver thread
		#for reasons mysterious to me, the solver runs really slowly unless you do it in a Qt thread...
		while(not done): #wait for solver to finish
			time.sleep(0.001)
		solveTime = time.time()-startTime
		self.printLog("done solving. took " + str(solveTime) + " seconds")
		return solveTime

	def closeFile(self):
		Gui.SendMsgToActiveView("Save") #save file
		App.closeDocument(self.currentDoc.Name) #close file
		self.currentDoc = None
		self.printLog("saved and closed file")
		
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
			
	def solveCondition(self, condList):
		fileName = "-".join([str(i) for i in condList]) + ".FCStd"
		self.makeFile(fileName)
		self.setVars(condList)
		self.makeMesh()
		self.solveMesh()
		self.closeFile()
		
auto = FemScript("/home/jacoby/Documents/FreeCAD/GRT fea stuff/automated FEM script/runFromStringTest", "test.FCStd", ["beamLength", "beamWidth", "elementSize", "force"], [" mm"," mm"," mm"," N"])
auto.solveCondition([100,10,2,100])
