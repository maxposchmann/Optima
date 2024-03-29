import json
import numpy as np
import optima
import optimaData
import thermoOptima
import dictTools
import random
import time

# Set global optimization parameters
tol = 1e-4
maxIts = 100
nTests = 100
for nParams in range(1,17):

    # Choose files to use
    testDatFile = 'MoPd-testTemplate.dat'
    testParamFile = 'MoPd-values.json'
    validationTestsFile = 'generatedValidationPoints.json'
    outputFile = f'ucb-{nParams}vars-{nTests}tests.json'

    # Set units
    tunit = 'K'
    punit = 'atm'
    munit = 'moles'
    elements = ['Pd', 'Ru', 'Tc', 'Mo']

    # Read file with known coefficient values and calculate ranges for testing
    jsonFile = open(testParamFile,)
    params = json.load(jsonFile)
    jsonFile.close()

    for param in params:
        value = params[param]['value']
        if value != 0:
            scale = np.ceil(np.log10(abs(value)))
        else:
            # The only one of these is a T**3, so set for that case same as it would normally be
            scale = -6
        params[param]['scale'] = 10**scale
        params[param]['lob'] = -(10**scale)
        params[param]['upb'] = +(10**scale)

    # Load validation data
    jsonFile = open(validationTestsFile,)
    validationPoints = json.load(jsonFile)
    jsonFile.close()

    # Get tags
    tagWindow = optimaData.TagWindow(testDatFile,[])
    tagWindow.close()

    # Set method and params
    method = optima.Bayesian
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

    # Test loop
    testDetails = dict([])
    for ti in range(nTests):
        # Choose n parameters at random to use
        selectedParams = random.sample([*params],k=nParams)
        print(selectedParams)

        for param in params:
            tagWindow.tags[param]['scale'] = params[param]['scale']
            tagWindow.tags[param]['initial'][0] = params[param]['lob'] * (1 + 0.1 * random.random())
            tagWindow.tags[param]['initial'][1] = params[param]['upb'] * (1 + 0.1 * random.random())
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

        st = time.time()
        norm, iterations, beta = method(y,intertags,getValues,maxIts,tol,weight = weight,scale = scale,**extraParams)
        et = time.time()
        testDetails[ti] = dict([('norm',norm),('iterations',iterations),('time',et-st)])

        print(f' ---- DONE {ti+1} ----')

    with open(outputFile, 'w') as outfile:
        json.dump(testDetails, outfile, indent=2)
