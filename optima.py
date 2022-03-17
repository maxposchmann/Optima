import numpy as np
import copy

# Levenberg-Marquardt non-linear optimizer using Broyden approximation for Jacobian.
# Make this class general. Avoid to the greatest extent possible including any application-specific code.
# Any methods required to call Thermochimica (or other) should be imported from another class.
# y is dependent true values from validation data set.
# tags is a dict containing coefficient names and two initial guesses for each
# functional is a function that returns an array of values corresponding to the validationPoints
# maxIts and tol are convergence parameters
def LevenbergMarquardtBroyden(y,tags,functional,maxIts,tol,weight):
    # get problem dimensions
    m = len(y)
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

    # beta is array of coefficients, start with initial value 0
    betaInit0 = np.array([tags[tag][0] for tag in tags])
    betaInit1 = np.array([tags[tag][1] for tag in tags])

    for iteration in range(maxIts):
        # Get beta
        if iteration == 0:
            # Start with first initial guess
            beta = copy.deepcopy(betaInit0)
        elif iteration < n + 1:
            # Update to second set of initial values one-by-one
            # Ensure initial values don't repeat
            i = iteration - 1
            if betaInit1[i] == betaInit0[i]:
                if betaInit1[i] == 0:
                    # If everything is left blank, mix the values around a bit
                    beta[i] = (-1)**i * (7 * i + 1)
                else:
                    # Otherwise try a small step from the value provided
                    beta[i] = 1.007 * betaInit0[i]
            else:
                # If there is a usable value, use it
                beta[i] = betaInit1[i]
        else:
            # Otherwise use directionVector method to update beta
            l = 1/(iteration+1)**2
            l = 1/(iteration + 1 - n)**2
            steplength = 1
            # Calculate update to coefficients
            try:
                beta = directionVector(r, broydenMatrix, beta, l, steplength, weight)
            except OptimaException:
                return

        # Calculate the functional values
        # Leave this call straightforward: want to be able to swap this function for any other black box
        try:
            f = functional(tags,beta)
        except OptimaException:
            if iteration == 0:
                return
            # If a calculation fails, try shrinking step drastically
            beta = 0.999 * betaOld + 0.001 * beta
            try:
                f = functional(tags,beta)
            except OptimaException:
                return

        # Compute the functional norm:
        scale = 1e6
        r = scale * (f - y) / abs(y)
        norm = functionalNorm(r / scale)
        # Print current status
        print(f'Iteration: {iteration + 1}')
        print(f'Current coefficients: {beta}')
        print(f'Norm: {norm}')
        print()
        # Check if converged
        if norm < tol:
            # Converged, print and return
            print()
            print('Converged')
            print(f'{beta} after {iteration + 1}')
            return

        # Update the Broyden matrix:
        if iteration > 0:
            # Residuals and deltas
            s = beta - betaOld
            t = rOld - r
            broydenUpdate(broydenMatrix, t, s)

        # Update vectors for succeeding iteration:
        betaOld = copy.deepcopy(beta)
        rOld = copy.deepcopy(r)

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
def directionVector(residual, broydenMatrix, coefficient, l, steplength, weight):
    m = len(residual)
    n = len(coefficient)

    a = np.zeros([n,n])
    b = np.zeros(n)

    # Compute the (J^T J) matrix:
    for j in range(n):
        for i in range(j,n):
            # Compute the coefficient for the A matrix:
            for k in range(m):
                a[i][j] += broydenMatrix[k][i] * broydenMatrix[k][j] * weight[k]
            # Apply symmetry:
            a[j][i] = a[i][j]

    # Compute the right hand side vector:
    for j in range(n):
        for i in range(m):
            b[j] = b[j] + broydenMatrix[i][j] * residual[i]
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
        raise OptimaException

# Bayesian optimization
# arguments match those in LevenbergMarquardtBroyden so a common interface can be used
def Bayesian(y,tags,functional,maxIts,tol,weight):
    from sklearn.svm import SVC
    from sklearn.preprocessing import MinMaxScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import r2_score
    from bayes_opt import BayesianOptimization, UtilityFunction
    from scipy.stats import norm

    # get problem dimensions
    m = len(y)
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

    # Use provided functional to get trial values, then calculate R2 score
    # Need to take an unknown number of tags+values pairs as arguments.
    def functionalR2(**pairs):
        beta = list(pairs.values())
        f = functional(tags, beta)
        score = r2_score(y, f, sample_weight = weight)
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
