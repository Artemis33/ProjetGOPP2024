import gurobipy as gbp
from BatchSchedulingData import BatchSchedulingData
from collections import defaultdict
from BatchSchedulingSolution import *

class BatchSchedulingMIPModelFlot:
	def __init__(self):
		self._model = None

	def runMILPModelFlot(self, data: BatchSchedulingData, timeLimit, verbose=False):
		options = {
			"WLSACCESSID": "4cdebb5b-37ae-4e6a-b2e7-7034a3a4c7f6",
			"WLSSECRET": "2ac54f8d-cb32-456d-b737-f45f48e491d2",
			"LICENSEID": 2590058,
			"OutputFlag": verbose,
			"TimeLimit": timeLimit,
		}

		processingTimes = [pj for pj,_ in data._jobs]
		jobSizes = [sj for _,sj in data._jobs]
		
		unique_sizes = sorted(set(jobSizes))
		unique_processing_times = list(sorted(set(processingTimes)))

		# Créer un dictionnaire pour stocker les indices des tâches par combinaison de taille et de durée
		task_indices = defaultdict(list)

		# Remplir le dictionnaire avec les indices des tâches pour récupérer la solution 
		for idx, (size, processing_time) in enumerate(zip(jobSizes, processingTimes)):
			l = unique_processing_times.index(processing_time)
			task_indices[(size, l)].append(idx+1)

		# Initialisation de N avec des valeurs par défaut pour toutes les combinaisons
		N = defaultdict(int)

		# Ajouter explicitement toutes les combinaisons (q, l) avec une valeur initiale de 0
		for q in unique_sizes:
			for l in range(len(unique_processing_times)):
				N[(q, l)] = 0  # Par défaut, 0 tâche

		# Parcours des tâches pour incrémenter les combinaisons observées
		for size, processing_time in zip(jobSizes, processingTimes):
			if size in unique_sizes and processing_time in unique_processing_times:
				l = unique_processing_times.index(processing_time)
				N[(size, l)] += 1  # Incrémenter la valeur pour cette combinaison

		# Create the task graphs
		data.createGraphs()

		# Create the model
		with gbp.Env(params=options) as env, gbp.Model("BatchSchedulingMIP", env=env) as self._model:
			# Decision variables
			x = self._model.addVars(len(unique_processing_times), data._nbMachine, vtype=gbp.GRB.INTEGER, lb =0, name="x")
			f = {}
			y = self._model.addVars(unique_sizes, len(unique_processing_times), vtype=gbp.GRB.INTEGER, lb = 0, name="y")
			Cmax = self._model.addVar(vtype=gbp.GRB.CONTINUOUS, name="Cmax", lb =0)

			for l in range(len(unique_processing_times)):
				graph = data._graphs[l]
				f[l] = self._model.addVars(graph.edges, vtype=gbp.GRB.INTEGER, name=f"f_{l}")

			# Objective function: minimize Cmax
			self._model.setObjective(Cmax, gbp.GRB.MINIMIZE)

			# Constraints

			# Makespan constraints
			self._model.addConstrs(
				(
					gbp.quicksum(unique_processing_times[l] * x[l, k] for l in range(len(unique_processing_times)))
					<= Cmax for k in range(data._nbMachine)
				),
				"MakespanConstraint",
			)

			for l in range(len(unique_processing_times)):
				self._model.addConstr(gbp.quicksum(f[l][edges] for edges in list(data._graphs[l].out_edges(0))) == gbp.quicksum(x[l,k] for k in range(data._nbMachine)))

			for l in range(len(unique_processing_times)):
				self._model.addConstr(gbp.quicksum(f[l][edges] for edges in list(data._graphs[l].in_edges(data._machineCapacity))) == gbp.quicksum(x[l,k] for k in range(data._nbMachine)))

			# Flow conservation
			for l in range(len(unique_processing_times)):
				nodes = [n for n in data._graphs[l].nodes if n != 0 and n != data._machineCapacity]
				for n in nodes:
					self._model.addConstr(gbp.quicksum(f[l][edges] for edges in list(data._graphs[l].in_edges(n))) 
										  == gbp.quicksum(f[l][edges] for edges in list(data._graphs[l].out_edges(n))))
					

			# Initial flow constraints
			
			self._model.addConstrs(
				(
					y[q, 0] == N[(q, 0)] - sum(
						f[0][(v, v_next)] for v, v_next in data._graphs[0].edges if v_next - v == q
					)
					for q in unique_sizes
				),
				"InitialFlow",
			)

			#Final flow constraints
			self._model.addConstrs(
				(y[q, len(unique_processing_times) - 1] == 0 for q in unique_sizes), "FinalFlow"
			)

			for l in range(1,len(unique_processing_times)):
				self._model.addConstrs(
					(y[q, l] == y[q, l-1] + N[(q, l)] - gbp.quicksum(f[l][(v1,v1+q)] if (v1,v1 + q) in data._graphs[l].edges else 0
					for v1 in data._graphs[l].nodes)) for q in unique_sizes)

			
			self._model.optimize()

			print("\n----------------------------------")
			print("Temps de résolution (s) : ", self._model.Runtime)
			print("Gap: ", self._model.MIPGap)
			print("Borne Inférieure: ", round(self._model.ObjBound))
			print("Borne Supérieure: ", round(self._model.ObjVal))
			print("----------------------------------")

			if self._model.status == gbp.GRB.OPTIMAL:
				print(f"Optimal solution found with Cmax = {Cmax.X}")
				solution = BatchSchedulingSolution(data._name)
				solution._value = Cmax.X
				
				# Stockage des chemins par durée
				pathsDuration = {}
				batchsDuration = {}
				machine = [[] for _ in range(data._nbMachine)]
				for l in range(len(unique_processing_times)):
					flow_edges = {(v, v_next): f[l][(v, v_next)].X for v, v_next in data._graphs[l].edges if f[l][(v, v_next)].X > 0}
					paths = []
					batchs = []
					if not flow_edges:
						continue  # Passer au prochain l si aucun flot

					while flow_edges:
						b = []
						current_path = [0]  # Commence toujours à la source
						current_node = 0

						while current_node != data._machineCapacity:
							for (v, v_next), flow_value in list(flow_edges.items()):
								if v == current_node:
									q = v_next - v
									for lb in range(l, -1, -1):
										if task_indices.get((q, lb), []):
											b.append(task_indices[(q, lb)].pop(0))
									current_path.append(v_next)
									current_node = v_next
									if flow_value > 1:
										flow_edges[(v, v_next)] -= 1
									else:
										del flow_edges[(v, v_next)]
									break
							
						paths.append(list(current_path))  # Ajouter une copie du chemin pour chaque unité de flot
						batchs.append(list(b))
							
						# Stocker les chemins pour cette durée
						pathsDuration[l] = paths
						batchsDuration[l] = batchs					
					
					for k in range(data._nbMachine):
						if x[l,k].X >= 0.90:
							for b in range(int(x[l,k].X)):
								machine[k].append(batchsDuration[l][0])
								batchsDuration[l].pop(0)
				solution._batchCompoSurMachine = machine
				return solution
			else:
				return None 
