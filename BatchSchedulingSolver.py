from BatchSchedulingMIPModel1 import *
from BatchSchedulingData import *
from BatchSchedulingMIPModel2 import *
from BatchSchedulingMIPFlot import *
from BatchSchedulingHeuristic import *
import time
from projectUtils import *
import sys

# Create the command line parser
parser = argparse.ArgumentParser(description="Process command line arguments.")

# Add the arguments
parser.add_argument("-d", "--dataFilePath", type=validFile, required=True, help="The path to the data file.")
parser.add_argument("-m", "--model", type=str, required=True, choices=["MIP1", "MIP2", "MIPFlot", "Heuristic"], help="The model to solve the problem.")
parser.add_argument("-t", "--timeLimit", type=positiveInt, default=600, help="The time limit. Default is 600.")
parser.add_argument("-p", "--print", action='store_true', help="Verbose output or not. Default is False.")
parser.add_argument("-f", "--solutionFolderPath", type=validFolder, required=True,
				   help="The path to the solution folder.")

# Parse the arguments
args = parser.parse_args()
print("----------- ARGUMENTS -----------")
print("Data file path =", args.dataFilePath)
print("Problem model =", args.model)
print("Time limit =", args.timeLimit)
print("Verbose output =", args.print)
print("Solution folder path =", args.solutionFolderPath)
print("------------------------------------")

# Read the data from the file
dataFileName = os.path.splitext(os.path.basename(args.dataFilePath))[0]
print(args.dataFilePath)
data = BatchSchedulingData(args.dataFilePath)
# print(data)

# Solve the problem
begin = time.time()
if args.model == "MIP1":
	if args.print:
		print("Considering model 1 of the problem")
	inst = BatchSchedulingMIPModel1()
	solution = inst.runMILPModel1(data, args.timeLimit, args.print)

elif args.model == "MIP2":
	if args.print:
		print("Considering model 2 of the problem")
	inst = BatchSchedulingMIPModel2()
	solution = inst.runMILPModel2(data, args.timeLimit, args.print)

elif args.model == "MIPFlot":
	if args.print:
		print("Considering flow model of the problem")
	inst = BatchSchedulingMIPModelFlot()
	solution = inst.runMILPModelFlot(data, args.timeLimit, args.print)

elif args.model == "Heuristic":
	if args.print:
		print("Considering heuristic of the problem")
	inst = BatchSchedulingHeuristic()
	solution = inst.runHeuristic(data)

else:
	print("Unknown model of the problem")
	sys.exit(0)
end = time.time()

### TO DO
# Check the solution
# isFeasible = checkSolution(data, solution, args.version, args.print)

# Save the solution
if (solution!=False):
	solutionFilePath = dataFileName + "_" + str(args.model) + ".txt"
	if args.solutionFolderPath != "":
		solutionFilePath = os.path.join(args.solutionFolderPath, solutionFilePath)
	print("Solution is written in the following file: ", solutionFilePath)
	solution.saveSolution(solutionFilePath)

# Print the result and exit
Instance = dataFileName
if ("instance_" in Instance):
	Instance = Instance.split("instance_")[1]
print("\nInstance =", Instance)
print("Modèle =", args.model)
if (solution!=False):print("Valeur de la solution =", round(solution._value))
print("cpuTime =", float(end - begin))
sys.exit(0)
