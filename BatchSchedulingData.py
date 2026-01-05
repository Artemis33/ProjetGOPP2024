import os
import networkx as nx
class BatchSchedulingData:
	def __init__(self, fileName):
		self._name = os.path.splitext(os.path.basename(fileName))[0]
		self._nbJob = 0
		self._nbMachine = 0
		self._machineCapacity = 0
		self._jobs = [] # matrice avec couples [pj,sj]
		self._graphs = {}
		self.readData(fileName)


	def readData(self,fileName):
		try:
			with open(fileName, 'r') as file:
				# Lire la première ligne: nombre de jobs, machines et capacité des machines
				line1 = file.readline().strip().split()
				self._nbJob = int(line1[0])
				self._nbMachine = int(line1[1])
				self._machineCapacity = int(line1[2])

				# Lire la deuxième ligne: temps de traitement des jobs
				P = file.readline().strip().split()
				# Lire la troisième ligne: taille des jobs
				S = file.readline().strip().split()

				self._jobs = [[int(P[i]), int(S[i])] for i in range(len(P))]
		except Exception as e:
			print(f"An error occurred while reading the file: {e}")

	def __str__(self):
		return (f"Number of jobs: {self._nbJob}\n"
				f"Number of machines: {self._nbMachine}\n"
				f"Machine capacity: {self._machineCapacity}\n"
				f"Processing times and Job sizes: {self._jobs}")

	def createGraphs(self):
		self._graphs = {}
		P = [pj for pj, _ in self._jobs]
		S = [sj for _, sj in self._jobs]
		# Obtenir toutes les durées uniques des tâches
		unique_processing_times = list(set(P))

		# Créer Gl
		for l in range(len(unique_processing_times)):
			# Créer un nouveau graphe
			graph = nx.DiGraph()
			
			# Liste des tailles de tâches compatibles avec la durée pl
			valid_task_sizes = [S[j] for j in range(self._nbJob)
				if P[j] <= unique_processing_times[l]]
			
			# Ensemble des tailles cumulées réalisables
			reachable_sizes = {0}
			for size in valid_task_sizes:
				reachable_sizes.update({v + size for v in reachable_sizes if v + size <= self._machineCapacity})

			# Créer les nœuds
			reachable_sizes = sorted(reachable_sizes)  # Trier pour une navigation facile
			for size in reachable_sizes:
				graph.add_node(size)

			# Créer les arcs A1
			for v in reachable_sizes:
				for size in valid_task_sizes:
					v_next = v + size
					if v_next in reachable_sizes:
						graph.add_edge(v, v_next, type="A1")

			# Créer les arcs A2
			for v in reachable_sizes:
				if v < self._machineCapacity:
					graph.add_edge(v, self._machineCapacity, type="A2")

			# Ajouter le graphe 
			self._graphs[l] = graph

	def displayGraphs(self):
		for pl, graph in self._graphs.items():
			print(f"\nGraphe G_{pl} (Durée pl = {pl})")
			print(f"Noeuds : {list(graph.nodes())}")
			print("Arcs :")
			for u, v, data in graph.edges(data=True):
				print(f"  {u} -> {v} (type: {data['type']})")

