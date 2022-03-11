import numpy as np

# Levenberg-Marquardt non-linear optimizer using Broyden approximation for Jacobian.
# Make this class general. Avoid to the greatest extent possible including any application-specific code.
# Any methods required to call Thermochimica (or other) should be imported from another class.
# validationPoints is a dict containing points with system state and values to compare.
# tags is a dict containing coefficient names and two initial guesses for each
# functional is a function that returns an array of values corresponding to the validationPoints
# maxIts and tol are convergence parameters
def LevenbergMarquardtBroyden(validationPoints,tags,functional,maxIts,tol):
    # get problem dimensions
    m = len(validationPoints)
    n = len(tags)

    # check that we have enough data to go ahead
    if n == 0:
        print('No tags with unknown values')
        return
    if m == 0:
        print('No validation points')
        return

    # initialize Broyden matrix as 1s
    broydenMatrix = np.ones([m,n])

    # y is dependent true values from validation data set
    y = np.array([validationPoints[pointLabel]['gibbs'] for pointLabel in validationPoints.keys()])

    # beta is array of coefficients, start with initial value 0
    beta = np.array([tags[tag][0] for tag in tags])
    betaOld = beta

    try:
        f = functional(tags,beta)
    except OptimaException:
        return
    r = f - y
    rOld = r

    # Compute the functional norm:
    norm = functionalNorm(r)

    # now change to initial value 1, then enter loop
    beta = np.array([tags[tag][1] for tag in tags])
    # ensure initial values don't repeat
    for i in range(n):
        if beta[i] == betaOld[i]:
            if beta[i] == 0:
                beta[i] = -7
            else:
                beta[i] = 1.007 * betaOld[i]

    for iteration in range(maxIts):
        # calculate the functional values
        # leave this call straightforward: want to be able to swap this function for any other black box
        try:
            f = functional(tags,beta)
        except OptimaException:
            beta = 0.999 * betaOld + 0.001 * beta
            try:
                f = functional(tags,beta)
            except OptimaException:
                return

        # residuals and deltas
        s = beta - betaOld
        r = f - y
        t = rOld - r

        # Update vectors for succeeding iteration:
        betaOld = beta
        rOld = r

        # Compute the functional norm:
        norm = functionalNorm(r)
        print(f'Iteration {iteration}, Norm {norm}')
        if norm < tol:
            # Converged
            print()
            print('Converged')
            print(f'{beta} after {iteration+1}')
            return

        # Update the Broyden matrix:
        broydenUpdate(broydenMatrix, t, s)
        # Compute the direction vector:
        l = 1/(iteration+1)**2
        steplength = 1
        # calculate update to coefficients
        try:
            beta = directionVector(r, broydenMatrix, beta, l, steplength, s)
        except OptimaException:
            return
        print(f'Current coefficients: {beta}')
    print('Reached maximum iterations without converging')

# Functional norm calculation
def functionalNorm(residual):
    norm = 0
    for i in range(len(residual)):
        norm += residual[i]**2
    return norm

# Updates to Broyden matric based on current function values
def broydenUpdate(broydenMatrix,dependent,objective):
    m = len(dependent)
    n = len(objective)

    # Compute Bs:
    update = np.zeros(m)
    for j in range(n):
        for i in range(m):
            update[i] += broydenMatrix[i][j] * objective[j]

    # Compute sTs:
    sMag = 0
    for j in range(n):
        sMag += objective[j]**2

    # Compute (y - Bs) / sTs
    for i in range(m):
        update[i] = (dependent[i] - update[i]) / sMag

    # Update the Broyden matrix:
    for j in range(n):
        for i in range(m):
            broydenMatrix[i][j] = broydenMatrix[i][j] + update[i] * objective[j]

# New direction vector given current residual
def directionVector(functional, broydenMatrix, coefficient, l, steplength, lastChange):
    m = len(functional)
    n = len(coefficient)

    a = np.zeros([n,n])
    b = np.zeros(n)

    # Compute the (J^T J) matrix:
    for j in range(n):
        for i in range(j,n):
            # Compute the coefficient for the A matrix:
            for k in range(m):
                a[i][j] += broydenMatrix[k][i] * broydenMatrix[k][j]
            # Apply symmetry:
            a[j][i] = a[i][j]

    # Compute the right hand side vector:
    for j in range(n):
        for i in range(m):
            b[j] = b[j] + broydenMatrix[i][j] * functional[i]
        a[j][j] = a[j][j] + l

    # Call the linear equation solver:
    try:
        [x, residuals, rank, singular] = np.linalg.lstsq(a,b,rcond=None)
        betaNew = np.zeros(n)
        # Print results to screen:
        for j in range(n):
            if abs(x[j]) > 1e2 * abs(lastChange[j]):
                x[j] = 1e2 * x[j] / (abs(x[j]) / abs(lastChange[j]))
            betaNew[j] = coefficient[j] + steplength * x[j]
        return betaNew
    except np.linalg.LinAlgError:
        print('There was a problem in solving the system of linear equations.')
        raise OptimaException

# Bayesian optimization
# arguments match those in LevenbergMarquardtBroyden so a common interface can be used
def Bayesian(validationPoints,tags,functional,maxIts,tol):
    from sklearn.svm import SVC
    from sklearn.preprocessing import MinMaxScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import r2_score
    from bayes_opt import BayesianOptimization, UtilityFunction
    from scipy.stats import norm

    # get problem dimensions
    m = len(validationPoints)
    n = len(tags)

    # check that we have enough data to go ahead
    if n == 0:
        print('No tags with unknown values')
        return
    if m == 0:
        print('No validation points')
        return
    for tag in tags:
        if tags[tag][0] >= tags[tag][1]:
            print('Cannot run Bayesian solver with bound 1 >= bound 2')
            print(f'Check tag {tag}')
            return

    # y is dependent true values from validation data set
    y = np.array([validationPoints[pointLabel]['gibbs'] for pointLabel in validationPoints.keys()])

    # Use provided functional to get trial values, then calculate R2 score
    # Need to take an unknown number of tags+values pairs as arguments.
    def functionalR2(**pairs):
        beta = list(pairs.values())
        f = functional(tags, beta)
        score = r2_score(y, f)
        return score

    # Create a BayesianOptimization optimizer and optimize the given black_box_function.
    try:
        optimizer = BayesianOptimization(f = functionalR2, pbounds = tags)
        optimizer.maximize(init_points = 10, n_iter = max(maxIts - 10,0))
    except OptimaException:
        return
    # format for output
    results = list(optimizer.max['params'].items())

    print('Best result:')
    for i in range(n):
        print(f'{results[i][0]} = {results[i][1]}')
    print(f'f(x) = {optimizer.max["target"]}')

class OptimaException(Exception):
    pass
