import numpy as np
import random
import optima

# Testing parameters
nTests = 1
nVal = 100
nTotalParams = 2
xrange = 1

# Optima parameters
tol = 1e-4
maxIts = 100
maxAttempts = 1
method = optima.LevenbergMarquardtBroyden
# method = optima.Bayesian

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

suc = []
for j in range(0,1):
    paramRange = [j+i for i in [0,1]]

    nSuccess = 0
    for ti in range(nTests):
        # Generate validation data using "true" parameter values
        trueParams = [paramRange[0] + (paramRange[1]-paramRange[0])*(random.random()) for i in range(nTotalParams)]
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
                if method == optima.LevenbergMarquardtBroyden:
                    for p in range(nTotalParams):
                        tags[str(trueParams[p])] = [paramRange[0] + (paramRange[1]-paramRange[0])*(random.random()),paramRange[0] + (paramRange[1]-paramRange[0])*(random.random())]
            totalIts += maxIts
        print(trueParams)
        print(totalIts)
        print(f' ---- {j} DONE {ti+1}, PASSED {nSuccess} ----')
    print(f'{nSuccess} successes out of {nTests}')
    suc.append(nSuccess)
    print(suc)
