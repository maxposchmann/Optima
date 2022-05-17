import numpy as np
import random
import optima

# Testing parameters
nTests = 100
nVal = 100
nTotalParams = 2
xrange = 1
nRanges = 10

# Optima parameters
tol = 1e-4
maxIts = 10
maxAttempts = 500
method = optima.LevenbergMarquardtBroyden
method = optima.Bayesian
method = optima.Combined

# Create a mysterious "black-box" function
def blackBox(testValues, parameters):
    output = 0
    for j in range(len(parameters)):
        output += testValues[j]**parameters[j]
    return output

# A test evaluator that meets Optima's requirements
def testEvaluator(validation, tags, beta):
    f = []
    for i in range(len(validation)):
        f.append(blackBox(validation[i],beta))
    f = np.array(f)
    return f

# Loop over range of inputs
suc = []
grandTotalIts = []
for j in range(0,nRanges):
    paramRange = [0,1+j]

    nSuccess = 0
    grandTotalIts.append(0)
    # Loop over tests per input range
    for ti in range(nTests):
        # Generate validation data using "true" parameter values
        trueParams = [paramRange[0] + (paramRange[1]-paramRange[0])*(random.random()) for i in range(nTotalParams)]
        # trueParams = [5.22851767329473, 4.010085210407342]
        print(trueParams)
        values = []
        for n in range(nVal):
            values.append([xrange * random.random() for i in range(nTotalParams)])

        # Combine validation data with function
        def getValues(tags, beta):
            return testEvaluator(values, tags, beta)

        y = getValues([], trueParams)

        # Set up Optima
        tags = dict([])
        totalIts = 0
        for p in range(nTotalParams):
            tags[str(trueParams[p])] = [paramRange[0],paramRange[1]]
        for r in range(maxAttempts):
            try:
                norm, iterations, beta = method(y,tags,getValues,maxIts,tol)
                if norm < tol:
                    totalIts += iterations
                    nSuccess += 1
                    break
            except ValueError:
                pass
            if method == optima.LevenbergMarquardtBroyden:
                for p in range(nTotalParams):
                    tags[str(trueParams[p])] = [paramRange[0] + (paramRange[1]-paramRange[0])*(random.random()),paramRange[0] + (paramRange[1]-paramRange[0])*(random.random())]
            totalIts += iterations
        print(trueParams)
        print(totalIts)
        print(f' ---- 0-{j+1} DONE {ti+1}, PASSED {nSuccess} ----')
        grandTotalIts[-1] += totalIts
        print(f'Grand Total iterations: {grandTotalIts}')
    print(f'{nSuccess} successes out of {nTests}')
    suc.append(nSuccess)
    print(suc)
print(f'Average iterations: {[grandTotalIts[i]/suc[i] for i in range(0,nRanges)]}')
