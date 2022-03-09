import numpy as np

# Levenberg-Marquardt non-linear optimizer using Broyden approximation for Jacobian.
# Make this class general. Avoid to the greatest extent possible including any application-specific code.
# Any methods required to call Thermochimica (or other) should be imported from another class.
def LevenbergMarquardtBroyden(validationPoints,initial0,initial1,functional,tags,maxIts,tol):
    # get problem dimensions
    m = len(validationPoints)
    n = len(initial0)
    # check that we have enough data to go ahead
    if n == 0:
        print('No initial values')
        return
    if m == 0:
        print('No validation points')
        return

    # make sure initial guesses are not equal
    for i in range(n):
        if initial0[i] == initial1[i]:
            if initial1[i] == 0:
                initial1[i] = 7
            else:
                initial1[i] = 1.007 * initial0[i]

    # initialize Broyden matrix as 1s
    broydenMatrix = np.ones([m,n])

    # y is dependent true values from validation data set
    y = np.array([validationPoints[i][-1] for i in range(m)])

    # beta is array of coefficients, start with initial value 0
    beta = np.array(initial0)
    betaOld = beta

    f = functional(tags,beta)

    r = f - y
    rOld = r

    # Compute the functional norm:
    norm = functionalNorm(r)

    # now change to initial value 1, then enter loop
    beta = np.array(initial1)

    for iteration in range(maxIts):
        # calculate the functional values
        # leave this call straightforward: want to be able to swap this function for any other black box
        f = functional(tags,beta)

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
            break

        # Update the Broyden matrix:
        broydenUpdate(broydenMatrix, t, s)
        # Compute the direction vector:
        l = 1/(iteration+1)**2
        steplength = 1
        # calculate update to coefficients
        beta = directionVector(r, broydenMatrix, beta, l, steplength)
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
def directionVector(functional, broydenMatrix, coefficient, l, steplength):
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
            betaNew[j] = coefficient[j] + steplength * x[j]
        return betaNew
    except np.linalg.LinAlgError:
        print('There was a problem in solving the system of linear equations.')

# Bayesian optimization
def Bayesian(validationPoints,initial0,initial1,functional,tags,maxIts,tol):
    from sklearn.svm import SVC
    from sklearn.preprocessing import MinMaxScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import r2_score
    from bayes_opt import BayesianOptimization, UtilityFunction
    from scipy.stats import norm

    # get problem dimensions
    m = len(validationPoints)
    n = len(initial0)
    # y is dependent true values from validation data set
    y = np.array([validationPoints[i][-1] for i in range(m)])

    # Use provided functional to get trial values, then calculate R2 score
    # Need to take an unknown number of tags+values pairs as arguments.
    def functionalR2(**pairs):
        tags = list(pairs.keys())
        beta = list(pairs.values())
        f = functional(tags, beta)
        score = r2_score(y, f)
        return score

    # Set range to optimize within.
    # bayes_opt requires this to be a dictionary.
    tagsAndBounds = dict([(tags[i], [initial0[i],initial1[i]]) for i in range(n)])

    # Create a BayesianOptimization optimizer and optimize the given black_box_function.
    optimizer = BayesianOptimization(f = functionalR2, pbounds = tagsAndBounds)
    optimizer.maximize(init_points = 10, n_iter = max(maxIts - 10,0))
    # format for output
    results = list(optimizer.max['params'].items())

    print('Best result:')
    for i in range(n):
        print(f'{results[i][0]} = {results[i][1]}')
    print(f'f(x) = {optimizer.max["target"]}')
