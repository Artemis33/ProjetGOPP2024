from BatchSchedulingData import *
from BatchSchedulingSolution import * 
import gurobipy as gbp
import math

class BatchSchedulingHeuristic:

	def runHeuristic(self, data:BatchSchedulingData):
		# Extraction des données en entrée
		name = data._name
		nbJob = data._nbJob
		nbMachine = data._nbMachine
		machineCapacity = data._machineCapacity

		tasks = list(enumerate(data._jobs))
		tasksSorted = sorted(tasks, key=lambda x: x[1][0], reverse=True)
		sortedIndices = [t[0] for t in tasksSorted]
		processingTimes = [t[1][0] for t in tasksSorted]
		jobSizes = [t[1][1] for t in tasksSorted]

		solution = BatchSchedulingSolution(name)
		# Etape 1 : Création des batchs
		B = []
		batch = []
		batchSize = 0
		for j in range(nbJob):
			ogIndex = sortedIndices[j]
			if (batchSize + jobSizes[j] <= machineCapacity):
				batchSize += jobSizes[j]
				batch.append(ogIndex + 1)
			else:
				B.append(batch)
				batch = [ogIndex + 1]
				batchSize = jobSizes[j]
		if batch:
			B.append(batch)
		print(B)
		# Etape 2 : Assignation des batchs aux machines
		machines = [[] for _ in range(nbMachine)]
		for b in range(len(B)//2):
			machines[b%nbMachine].append(B[b])
		if (len(B)%2):
			machines[b%nbMachine].append(B[len(B)//2])
		for b in range(len(B)//2):
			machines[b%nbMachine].append(B[-b - 1])
		
		C = [0 for _ in range(nbMachine)]
		for k in range(nbMachine):
			machine = machines[k]
			for b in machine:
				C[k] += data._jobs[b[0] - 1][0]
		Cmax = max(C)
		solution._value = Cmax
		solution._batchCompoSurMachine = machines
		
		print("\n----------------------------------")
		print("Gap: ", "/")
		print("Borne Inférieure: ", "/")
		print("Borne Supérieure: ", "/")
		print("Valeur de la solution =", Cmax)
		print("----------------------------------")
		return solution


		