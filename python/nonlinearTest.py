import numpy as np
import random
import optima

# Testing parameters
nTests = 1000
nVal = 100
nTotalParams = 5
paramRange = 2
# Optima parameters
tol = 1e-4
maxIts = 100
maxAttempts = 1
method = optima.LevenbergMarquardtBroyden
# method = optima.Bayesian

# Create a "black-box" function that meets Optima's requirements
def nonlinearFunction(validation, tags, beta):
    f = []
    for i in range(len(validation)):
        calcValues = 0
        for j in range(len(beta)):
            calcValues += validation[i][j]**beta[j]
        f.append(calcValues)
    f = np.array(f)
    return f

nSuccess = 0
for n in range(nTests):
    # Generate validation data using "true" parameter values
    trueParams = [paramRange*(random.random()) for i in range(nTotalParams)]
    print(trueParams)
    values = []
    for n in range(nVal):
        values.append([random.random() for i in range(nTotalParams)])

    # Combine validation data with function
    def getValues(tags, beta):
        return nonlinearFunction(values, tags, beta)

    y = getValues([], trueParams)

    # Set up Optima
    tags = dict([])
    totalIts = 0
    for p in range(nTotalParams):
        tags[str(trueParams[p])] = [0,paramRange]
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
                    tags[str(trueParams[p])] = [paramRange*(random.random()),paramRange*(random.random())]
        totalIts += maxIts
        # else:
        #     for p in range(nTotalParams):
        #         tags[str(p)] = [beta[p],beta[p]]
    print(trueParams)
    print(totalIts)
print(f'{nSuccess} successes out of {nTests}')
