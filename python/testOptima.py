import json
import numpy as np
import optima
import optimaData
import thermoOptima
import dictTools
import random

# Choose files to use
testDatFile = 'MoPd-testTemplate.dat'
testParamFile = 'MoPd-values.json'
validationTestsFile = 'validationData.json'

# Set units
tunit = 'K'
punit = 'atm'
munit = 'moles'
elements = ['Pd', 'Ru', 'Tc', 'Mo']

# Set global optimization parameters
tol = 1e-4
maxIts = 30
nParams = 3

# Read file with known coefficient values and calculate ranges for testing
jsonFile = open(testParamFile,)
params = json.load(jsonFile)
jsonFile.close()

for param in params:
    value = params[param]['value']
    if value != 0:
        scale = np.ceil(np.log10(abs(value)))
    else:
        scale = 1
    params[param]['scale'] = scale
    params[param]['lob'] = -10**scale
    params[param]['upb'] = +10**scale


# Load validation data
jsonFile = open(validationTestsFile,)
validationPoints = json.load(jsonFile)
jsonFile.close()

# Get tags
tagWindow = optimaData.TagWindow(testDatFile,[])
tagWindow.close()

# Set method and params
method = optima.LevenbergMarquardtBroyden
extraParams = {}
# Get initial problem dimensions
m = len(validationPoints)
n = len(tagWindow.tags)
# Write input file
with open('validationPoints.ti', 'w') as inputFile:
    inputFile.write('! Optima-generated input file for validation points\n')
    inputFile.write(f'data file         = optima.dat\n')
    inputFile.write(f'temperature unit         = {tunit}\n')
    inputFile.write(f'pressure unit          = {punit}\n')
    inputFile.write(f'mass unit          = {munit}\n')
    inputFile.write(f'nEl         = {len(elements)} \n')
    inputFile.write(f'iEl         = {" ".join([str(thermoOptima.atomic_number_map.index(element)+1) for element in elements])}\n')
    inputFile.write(f'nCalc       = {len(validationPoints)}\n')
    for point in validationPoints.keys():
        inputFile.write(f'{" ".join([str(validationPoints[point]["state"][i]) for i in range(len(elements)+2)])}\n')

# Choose n parameters at random to use
selectedParams = random.choices([*params],k=nParams)
print(selectedParams)

for param in params:
    tagWindow.tags[param]['scale'] = params[param]['scale']
    tagWindow.tags[param]['initial'][0] = params[param]['lob']
    tagWindow.tags[param]['initial'][1] = params[param]['upb']
    tagWindow.tags[param]['optimize'] = True
    if param not in selectedParams:
        tagWindow.tags[param]['optimize'] = False
        tagWindow.tags[param]['initial'][0] = params[param]['value']

# Call tag preprocessor
intertags = thermoOptima.createIntermediateDat(tagWindow.tags,testDatFile)
# Use currying to package validationPoints with getPointValidationValues
def getValues(tags, beta):
    return thermoOptima.getPointValidationValues(validationPoints, tags, beta)
# Get validation value/weight pairs
validationPairs = []
validationKeys = list(validationPoints.keys())
for i in range(m):
    calcValues = []
    dictTools.getParallelDictValues(validationPoints[validationKeys[i]]['values'],
                                    validationPoints[validationKeys[i]]['values'],
                                    calcValues)
    validationPairs.extend(calcValues)
# Real problem size is number of value/weight pairs x number of tags to be optimized
m = len(validationPairs)
n = len(intertags)
# Setup validation and weights arrays
y = np.zeros(m)
weight = np.ones(m)
for i in range(m):
    if isinstance(validationPairs[i],list):
        y[i] = validationPairs[i][0]
        weight[i] = validationPairs[i][1]
    else:
        y[i] = validationPairs[i]
weight = np.ones(m)
scale = []
for tag in intertags.keys():
    scale.append(tagWindow.tags[tag]['scale'])
scale = np.array(scale)

method(y,intertags,getValues,maxIts,tol,weight = weight,scale = scale,**extraParams)
