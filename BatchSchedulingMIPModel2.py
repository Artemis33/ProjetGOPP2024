import gurobipy as gbp
from BatchSchedulingData import *
from BatchSchedulingSolution import *

class BatchSchedulingMIPModel2:
	def __init__(self):
		"""
		Initialize the scheduler with the data from the BatchSchedulingData class.
		"""
		self._model = None

	def runMILPModel2(self, data: BatchSchedulingData, timeLimit, verbose=False):
		options = {
			"WLSACCESSID": "4cdebb5b-37ae-4e6a-b2e7-7034a3a4c7f6",
			"WLSSECRET": "2ac54f8d-cb32-456d-b737-f45f48e491d2",
			"LICENSEID": 2590058,
			"OutputFlag": verbose,
			"TimeLimit": timeLimit,
		}

		# Extraction des données en entrée
		name = data._name
		nbJob = data._nbJob
		nbMachine = data._nbMachine
		machineCapacity = data._machineCapacity
		# pMax = max(data._jobs[:][0])
		
		# Trier par durée décroissante
		tasks = list(enumerate(data._jobs))
		tasksSorted = sorted(tasks, key=lambda x: x[1][0], reverse=True)

		sortedIndices = [t[0] for t in tasksSorted]
		processingTimes = [t[1][0] for t in tasksSorted]
		jobSizes = [t[1][1] for t in tasksSorted]

		with gbp.Env(params=options) as env, gbp.Model("MIP2", env=env) as self._model:
			# Variables de décision
			x = self._model.addVars(nbJob, nbJob, vtype=gbp.GRB.BINARY, name="x")  # x[j, j'] affectation de j à j'
			z = self._model.addVars(nbMachine, nbJob, vtype=gbp.GRB.BINARY, name="z")  # z[k, j'] affectation à une machine
			C = self._model.addVars(nbMachine, vtype=gbp.GRB.CONTINUOUS, name="C")  # Completion time pour chaque machine
			Cmax = self._model.addVar(vtype=gbp.GRB.CONTINUOUS, name="Cmax")  # Makespan
			

			# Fonction objectif: minimiser Cmax
			self._model.setObjective(Cmax, gbp.GRB.MINIMIZE)

			# Contraintes
			# (17) Chaque job est affecté à exactement un représentant
			
			self._model.addConstrs((gbp.quicksum(x[j, j2] for j in range(nbJob)) == 1 for j2 in range(nbJob)), "Unique Reprénsentant")
			self._model.addConstr(x[0,0]==1)
			# (18) Les tailles de jobs respectent les capacités
			self._model.addConstrs((
				gbp.quicksum(jobSizes[j2] * x[j, j2] for j2 in range(nbJob)) <=
				machineCapacity * gbp.quicksum(z[k, j] for k in range(nbMachine))
				for j in range(nbJob)
			), "JobSizeCapacity")

			# (19) Chaque job est affecté à au plus une machine
			self._model.addConstrs((gbp.quicksum(z[k, j] for k in range(nbMachine)) <= 1 for j in range(nbJob)), "JobMachineAssignment")

			# (20) Contrainte d'ordre des jobs
			for j in range(nbJob):
				for j2 in range(1,j):
					self._model.addConstr((x[j, j2] == 0), "JobOrder")

			# (21) Limite d'affectation par machine
			self._model.addConstrs((x[j, j] == gbp.quicksum(z[k, j] for k in range(nbMachine)) for j in range(nbJob)), "MachineAssignmentLimit")

			self._model.addConstrs((C[k] == gbp.quicksum(z[k, j] * processingTimes[j] for j in range(nbJob)) for k in range(nbMachine)), "CompletionTime")

			# (24) Makespan
			self._model.addConstrs((C[k] <= Cmax for k in range(nbMachine)), "Makespan")

			# 8. Symétrie machine
			self._model.addConstrs((C[k] >= C[k+1] for k in range(nbMachine-1)), "Makespan Constraint")

			# Résolution
			self._model.optimize()

			print("\n----------------------------------")
			print("Temps de résolution (s) : ", self._model.Runtime)
			print("Gap: ", self._model.MIPGap)
			print("Borne Inférieure: ", round(self._model.ObjBound))
			print("Borne Supérieure: ", round(self._model.ObjVal))
			print("Valeur de la solution =", round(self._model.ObjVal))
			print("----------------------------------")

			# Vérification de la solution et extraction
			if self._model.Status == gbp.GRB.OPTIMAL or self._model.Status == gbp.GRB.TIME_LIMIT:
				solution = BatchSchedulingSolution(name)
				solution._value = Cmax.X
				for k in range(nbMachine):
					machine = []
					print("Ck:", C[k].X)
					for j in range(nbJob):
						if z[k, j].X > 0.5:
							batch = []
							for j2 in range(nbJob):
								if x[j, j2].X > 0.5:
									ogIndex = sortedIndices[j2]
									batch.append(ogIndex + 1)
							machine.append(batch)
					solution._batchCompoSurMachine.append(machine)
				return solution
			else:
				return False
