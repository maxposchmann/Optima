import json
from random import random
import thermoOptima
import subprocess

# Set units
tunit = 'K'
punit = 'atm'
munit = 'moles'
elements = ['Pd', 'Ru', 'Tc', 'Mo']

nSample = 100

tl = 300
th = 3000
p = 1
xl = 0.01
xh = 0.99

# Generate random states
states = []
for s in range(nSample):
    xPd = xl+random()*(xh-xl)
    states.append([tl+random()*(th-tl), p, xPd, 0, 0, 1-xPd])


# Generate input file for random points
with open('generatedPoints.ti', 'w') as inputFile:
    inputFile.write('! Optima-generated input file for validation points\n')
    inputFile.write(f'data file         = MoPd-filled.dat\n')
    inputFile.write(f'temperature unit         = {tunit}\n')
    inputFile.write(f'pressure unit          = {punit}\n')
    inputFile.write(f'mass unit          = {munit}\n')
    inputFile.write(f'nEl         = {len(elements)} \n')
    inputFile.write(f'iEl         = {" ".join([str(thermoOptima.atomic_number_map.index(element)+1) for element in elements])}\n')
    inputFile.write(f'nCalc       = {nSample}\n')
    for s in range(nSample):
        inputFile.write(f'{" ".join([str(states[s][i]) for i in range(len(elements)+2)])}\n')

# Run it
subprocess.run(['thermochimica/bin/RunCalculationList','generatedPoints.ti'])

# Load results and create validation file
jsonFile = open('thermochimica/thermoout.json',)
try:
    data = json.load(jsonFile)
    jsonFile.close()
except:
    jsonFile.close()
    print('Data load failed')

validationPoints = dict([])
for i in range(nSample):
    if len(data[str(i+1)].keys()) == 0:
        print('Thermochimica calculation failed to converge')
    validationPoints[str(i)] = dict([])
    validationPoints[str(i)]['state'] = states[i]
    validationPoints[str(i)]['values'] = dict([])
    validationPoints[str(i)]['values']['integral Gibbs energy'] = data[str(i+1)]['integral Gibbs energy']

with open('generatedValidationPoints.json', 'w') as outfile:
    json.dump(validationPoints, outfile, indent=2)
