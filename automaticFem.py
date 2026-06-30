#this is a test change
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore
import time
from femtools.ccxtools import CcxTools
	
class CcxToolsScripted(CcxTools):
	def run(self): #basically the same as the parent "run" function, but does not create messages boxes for errors, so that it can continue afte running. 
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

def run_solver_scripted(solver):
	if(solver.Proxy.Type != 'Fem::SolverCcxTools'): return
	App.Console.PrintMessage("Run of CalxuliX ccx tools solver started.\n")
	fea = CcxToolsScripted(solver)
	fea.reset_mesh_purge_results_checked()
	fea.run() # standard, no working dir is given in solver
	App.Console.PrintMessage("Run of CalxuliX ccx tools solver finished.\n")

def makeFile(base, path):
	print("=" * 50) #major separator
	print("writing file:", path)
	base.saveCopy(path)
	return(App.openDocument(path))

def makeMesh(doc):
	maxTime = 60 * 1000 # 60000 ms
	mesh = doc.getObject('FEMMeshGmsh')
	mesh.ViewObject.doubleClicked() #it is necessary to open the mesh task panel to create the "Tool" object
	while True:
		print("-" * 50) #minor separator
		print("preparing mesh...")
		startTime = time.time() #record when preparation started
		mesh.Tool.prepare()
		print("done preparing. took" , time.time()-startTime, "seconds")
		
		print("meshing...")
		startTime = time.time() #record when the meshing started
		mesh.Tool.compute()
		
		mesh.Tool.process.waitForFinished(maxTime) #wait until meshing finished, for a max. of maxTime milliseconds
		if(mesh.Tool.process.state().name == "NotRunning"): # if process finished
			print("done meshing. took" , time.time()-startTime, "seconds")
			break
		else:
			print("meshing timed out at", maxTime/1000, "seconds. aborting and restarting...")
			mesh.Tool.process.kill() #kill and restart process
			maxTime = maxTime * 4

	if(not(mesh.Tool.process.exitCode() == 0 and mesh.Tool.process.exitStatus().name == "NormalExit")): #if error code thrown
		print("meshing failed! suppressing mesh object")
		mesh.Suppressed = True #this indicates to solveMesh that meshing failed
	else:
		print("recomputed" , doc.recompute(), "objects")
	Gui.Control.closeDialog() #close task panel

def solveMesh(doc):
	done = False
	def runSolver(doc): #runs the solver and updates "done" when it is done
		nonlocal done
		run_solver_scripted(doc.getObject('SolverCcxTools'))
		done = True
	
	if(doc.getObject("FEMMeshGmsh").Suppressed == True): #if meshing failed, do not solve
		print("mesh object suppressed, cancelling solver")
		return
		
	print("-" * 50) #minor separator
	print("solving...")
	startTime = time.time() #record solver start time
	QtCore.QTimer.singleShot(0, lambda: runSolver(doc)) #start solver thread
	#for reasons mysterious to me, the solver runs really slowly unless you do it in a Qt thread...
	while(not done): #wait for solver to finish
		time.sleep(0.001)
	solveTime = time.time()-startTime
	print("done solving. took", solveTime, "seconds")
	return solveTime

def closeFile(doc):
	Gui.SendMsgToActiveView("Save") #save file
	App.closeDocument(doc.Name) #close file
	print("saved and closed file")
