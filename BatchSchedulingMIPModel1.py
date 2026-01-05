from BatchSchedulingData import *
from BatchSchedulingSolution import * 
import gurobipy as gbp
import math

class BatchSchedulingMIPModel1:
	def __init__(self):
		"""
		Initialize the scheduler with the data from the BatchSchedulingData class.
		"""
		self._model = None

	def runMILPModel1(self, data:BatchSchedulingData, timeLimit, verbose=False):
		options = {
		"WLSACCESSID": "4cdebb5b-37ae-4e6a-b2e7-7034a3a4c7f6",
		"WLSSECRET": "2ac54f8d-cb32-456d-b737-f45f48e491d2",
		"LICENSEID": 2590058,
		"OutputFlag": verbose,
		"TimeLimit": timeLimit,
			}
		
		"""
		Create and solve the scheduling problem using Gurobi.
		"""
		# Extraction des données en entrée
		name = data._name
		nbJob = data._nbJob
		nbMachine = data._nbMachine
		machineCapacity = data._machineCapacity
		processingTimes = [pj for pj,_ in data._jobs]
		jobSizes = [sj for _,sj in data._jobs]
		# nbBatch = nbJob
		nbBatch = 0
		for jobSize in jobSizes:
			nbBatch += jobSize
		nbBatch //= ((machineCapacity//2) + 1)
		nbBatch = math.ceil(nbBatch)
		pMax = max(processingTimes)
		with gbp.Env(params=options) as env, gbp.Model("MIP1", env=env) as self._model:
			
			# Variables de décision
			x = self._model.addVars(nbJob, nbBatch, vtype=gbp.GRB.BINARY, name="x")  # Affectation d'un job à un batch
			z = self._model.addVars(nbMachine, nbBatch, vtype=gbp.GRB.BINARY, name="z")  # Affectation d'un batch à une machine
			P = self._model.addVars(nbMachine, nbBatch, vtype=gbp.GRB.CONTINUOUS, name="P")  # Durée d'un batch sur une machine
			C = self._model.addVars(nbMachine, vtype=gbp.GRB.CONTINUOUS, name="C")  # Completion time pour chaque machine
			Cmax = self._model.addVar(vtype=gbp.GRB.CONTINUOUS, name="Cmax")  # Makespan
				
			# Fonction objectif: minimiser Cmax
			self._model.setObjective(Cmax, gbp.GRB.MINIMIZE)

			# Contraintes
			# 1. Chaque job est affecté à exactement un batch
			self._model.addConstrs((gbp.quicksum(x[j,b] for b in range(nbBatch)) == 1 for j in range(nbJob)), "Job Assignment")

			# 2. Total size of jobs assigned to a batch cannot exceed the machine's capacity
			self._model.addConstrs((gbp.quicksum(jobSizes[j] * x[j,b] for j in range(nbJob)) <= machineCapacity * gbp.quicksum(z[k,b] for k in range(nbMachine)) for b in range(nbBatch)), "Capacity Constraint")

			# 3. Each batch is assigned to exactly one machine
			self._model.addConstrs((gbp.quicksum(z[k,b] for k in range(nbMachine)) <= 1 for b in range(nbBatch)), "Batch Assignment")

			# 4. Each machine processes at least one batch
			self._model.addConstrs((x[j,b] <= gbp.quicksum(z[k,b] for k in range(nbMachine)) for j in range(nbJob) for b in range(nbBatch)), "Machine Used")

			# 5. Each machine processes at least one batch
			self._model.addConstrs((P[k,b] >= processingTimes[j]*x[j,b] - pMax * (1 - z[k,b]) for j in range(nbJob) for b in range(nbBatch) for k in range(nbMachine)), "Machine Used")

			# 6. Durée machine
			self._model.addConstrs((C[k] >= gbp.quicksum(P[k,b] for b in range(nbBatch)) for k in range(nbMachine)), "Makespan Constraint")

			# 7. Machine completion times must be less than or equal to Cmax
			self._model.addConstrs((C[k] <= Cmax for k in range(nbMachine)), "Makespan Constraint")

			# 8. Symétrie machine
			self._model.addConstrs((C[k] >= C[k+1] for k in range(nbMachine-1)), "Makespan Constraint")

			# 9. Symétrie batchs
			self._model.addConstrs((gbp.quicksum(P[k,b] for k in range(nbMachine)) >= gbp.quicksum(P[k,b+1] for k in range(nbMachine)) for b in range(nbBatch-1)), "Makespan Constraint")

			# 10. Fixer les durées de batchs pas utilisés à 0
			self._model.addConstrs((P[k,b] <= pMax * z[k,b] for k in range(nbMachine) for b in range(nbBatch)), "Makespan Constraint")

			# Optimize the model
			self._model.optimize()
			# self._model.write("MIP1.lp")
			print("\n----------------------------------")
			print("Temps de résolution (s) : ", self._model.Runtime)
			print("Gap: ", self._model.MIPGap)
			print("Borne Inférieure: ", round(self._model.ObjBound))
			print("Borne Supérieure: ", round(self._model.ObjVal))
			print("Valeur de la solution =", round(self._model.ObjVal))
			print("----------------------------------")
			# Retrieve the solution
			if self._model.Status == gbp.GRB.OPTIMAL or self._model.Status == gbp.GRB.TIME_LIMIT:
				solution = BatchSchedulingSolution(name)
				solution._value = round(Cmax.X)
				for k in range(nbMachine):
					machine = []
					for b in range(nbBatch):
						if (z[k, b].X >= 0.99):
							batch = []
							for j in range(nbJob):
								if (x[j, b].X >= 0.99):
									batch.append(j+1)
							machine.append(batch)
					solution._batchCompoSurMachine.append(machine)
				return solution
			else:
				return False   
			