from BatchSchedulingData import *

class BatchSchedulingSolution:
    """
    A class used to represent the Batch Scheduling Solution

    Attributes
    ----------
    _value : int 
        an integer that holds the value of the solution

    Methods
    -------
    __init__(self, fileName)
        Initializes the BatchSchedulingSolution with the provided filename.

    """
    def __init__(self, name):
        self._name = name
        self._value = 0 # Cmax
        self._batchCompoSurMachine = [] # matrix with for each batch the jobs it contains

    def saveSolution(self, fileName):
        if self is None:
            print("Solution vide")
            return None
        m = len(self._batchCompoSurMachine)
        with open(fileName, 'w') as file:
            file.write(str(int(self._value)) + "\n")
            for k in range(m):
                for b in self._batchCompoSurMachine[k]:
                    if b:
                        for j in b:
                            file.write(str(j) + " ")
                        file.write("|")
                file.write("\n")
            

    def readSolution(self, fileName):
        try:
            with open(fileName, 'r') as file:
                line = file.readline()
                self._value = int(line)
                while(line!=""):
                    line = file.readline()
                    if line:
                        batchTab = line.split("|")
                        machine = []
                        for b in batchTab:
                            machine.append(b.split())
                        self._batchCompoSurMachine.append(machine)

        except Exception as e:
            print(f"An error occurred while reading the file: {e}")

    def __str__(self):
        return (f"Name of the instance:{self._name}\n"
                f"Makespan: {self._value}\n"
                f"Composition of the batches: {self._batchCompoSurMachine}\n")

    # def checkSolution(self, data:BatchSchedulingData, verbose=False): 
        # affectation job batch
        # affetation batch machine
        # Ck <= Cmax
        # Ck = somme Pbk
