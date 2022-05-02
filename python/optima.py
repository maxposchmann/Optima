import numpy as np
import copy

# Levenberg-Marquardt non-linear optimizer using Broyden approximation for Jacobian.
# Make this class general. Avoid to the greatest extent possible including any application-specific code.
# Any methods required to call Thermochimica (or other) should be imported from another class.
# y is dependent true values from validation data set.
# tags is a dict containing coefficient names and two initial guesses for each
# functional is a function that returns an array of values corresponding to the validationPoints
# maxIts and tol are convergence parameters
def LevenbergMarquardtBroyden(y,tags,functional,maxIts,tol,weight = [], scale = [], **extraParams):
    # get problem dimensions
    m = len(y)
    n = len(tags)

    if not len(weight) == m:
        weight = np.ones(m)

    if not len(scale) == n:
        scale = np.ones(n)

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
    betaInit0 = np.array([float(tags[tag][0]) for tag in tags])
    betaInit1 = np.array([float(tags[tag][1]) for tag in tags])

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
            l = 1/(iteration + 1 - n)**2
            steplength = 1
            # Calculate update to coefficients
            try:
                beta = directionVector(r, broydenMatrix, beta, l, steplength, weight)
            except OptimaException:
                return

        # Calculate the functional values
        # Leave this call straightforward: want to be able to swap this function for any other black box
        beta = beta * scale
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
        beta = beta / scale
        # Compute the functional norm:
        rscale = 1e6
        r = rscale * (f - y) / abs(y)
        norm = functionalNorm(r / rscale)
        # Print current status
        print(f'Iteration: {iteration + 1}')
        print(f'Current coefficients: {beta * scale}')
        print(f'Norm: {norm}')
        print()
        # Check if converged
        if norm < tol:
            # Converged, print and return
            print()
            print('Converged')
            print(f'{beta * scale} after {iteration + 1}')
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
# Arguments match those in LevenbergMarquardtBroyden so a common interface can be used
def Bayesian(y,tags,functional,maxIts,tol,weight = [], scale = [], **extraParams):
    from sklearn.metrics import r2_score
    import sys
    sys.path.append('.')
    from BayesianOptimization.bayes_opt import BayesianOptimization, SequentialDomainReductionTransformer

    # Set default values for optional parameters
    acq = 'ucb'
    init_points = 10
    eta = 1
    kappa = 2.576
    kappa_decay = 1
    kappa_decay_delay = 0
    for param, value in extraParams.items():
        if param == 'acq':
            acq = value
        elif param == 'init_points':
            init_points = value
        elif param == 'eta':
            eta = value
        elif param == 'kappa':
            kappa = value
        elif param == 'kappa_decay':
            kappa_decay = value
        elif param == 'kappa_decay_delay':
            kappa_decay_delay = value

    # Get problem dimensions
    m = len(y)
    n = len(tags)

    if not len(weight) == m:
        weight = np.ones(m)

    if not len(scale) == n:
        scale = np.ones(n)

    # check that we have enough data to go ahead
    if n == 0:
        print('No tags with unknown values')
        return
    if m == 0:
        print('No validation points')
        return
    for tag in tags:
        # Check and adjust tags to be legal
        if tags[tag][0] > tags[tag][1]:
            print('Cannot run Bayesian solver with bound 1 > bound 2')
            print(f'Check tag {tag}')
            print('Bounds will be swapped automatically')
            tempbound = tags[tag][0]
            tags[tag][0] = tags[tag][1]
            tags[tag][1] = tempbound
        elif tags[tag][0] == tags[tag][1]:
            print('Cannot run Bayesian solver with bound 1 == bound 2')
            print(f'Check tag {tag}')
            print('Upper bound will be increased automatically')
            if tags[tag][1] == 0:
                tags[tag][1] = 7
            else:
                tags[tag][1] += abs(tags[tag][1])

    # Use provided functional to get trial values, then calculate R2 score
    # Need to take an unknown number of tag+value pairs as arguments.
    def functionalR2(**pairs):
        beta = list(pairs.values())
        f = functional(tags, beta)
        score = r2_score(y, f, sample_weight = weight)
        return score

    def functionalNormNegative(**pairs):
        beta = list(pairs.values())
        f = functional(tags, beta)
        rscale = 1e6
        r = rscale * (f - y) / abs(y)
        norm = functionalNorm(r / rscale)
        return -norm

    def functionalLogNorm(**pairs):
        beta = list(pairs.values())
        f = functional(tags, beta)
        rscale = 1e6
        r = rscale * (f - y) / abs(y)
        norm = functionalNorm(r / rscale)
        return -np.log(norm)

    # Create a BayesianOptimization optimizer and optimize the given black_box_function.
    try:
        bounds_transformer = SequentialDomainReductionTransformer(eta = eta)
        optimizer = BayesianOptimization(f = functionalNormNegative, pbounds = tags, bounds_transformer = bounds_transformer)
        optimizer.maximize(init_points = init_points,
                           n_iter = max(maxIts - init_points,0),
                           acq = acq,
                           kappa = kappa,
                           kappa_decay = kappa_decay,
                           kappa_decay_delay = kappa_decay_delay,
                           y_limit = 0)
    except OptimaException:
        return
    except ValueError:
        print('Internal bayes_opt error, run cancelled (retry may yield different results)')
    # Format for output
    results = list(optimizer.max['params'].items())

    print('Best result:')
    for i in range(n):
        print(f'{results[i][0]} = {results[i][1]}')
    print(f'f(x) = {optimizer.max["target"]}')

def BoTorchBayesian(y,tags,functional,maxIts,tol,weight = [], scale = [], **extraParams):
    import torch
    from botorch.models import SingleTaskGP
    from botorch.fit import fit_gpytorch_model
    from gpytorch.mlls import ExactMarginalLogLikelihood
    from botorch.acquisition import UpperConfidenceBound
    from botorch.optim import optimize_acqf

    # Get problem dimensions
    m = len(y)
    n = len(tags)

    if not len(weight) == m:
        weight = np.ones(m)

    if not len(scale) == n:
        scale = np.ones(n)

    # check that we have enough data to go ahead
    if n == 0:
        print('No tags with unknown values')
        return
    if m == 0:
        print('No validation points')
        return
    for tag in tags:
        # Check and adjust tags to be legal
        if tags[tag][0] > tags[tag][1]:
            print('Cannot run Bayesian solver with bound 1 > bound 2')
            print(f'Check tag {tag}')
            print('Bounds will be swapped automatically')
            tempbound = tags[tag][0]
            tags[tag][0] = tags[tag][1]
            tags[tag][1] = tempbound
        elif tags[tag][0] == tags[tag][1]:
            print('Cannot run Bayesian solver with bound 1 == bound 2')
            print(f'Check tag {tag}')
            print('Upper bound will be increased automatically')
            if tags[tag][1] == 0:
                tags[tag][1] = 7
            else:
                tags[tag][1] += abs(tags[tag][1])

    def functionalNormNegative(beta):
        f = functional(tags, beta)
        rscale = 1e6
        r = rscale * (f - y) / abs(y)
        norm = functionalNorm(r / rscale)
        return -norm

    def functionalLogNorm(beta):
        f = functional(tags, beta)
        rscale = 1e6
        r = rscale * (f - y) / abs(y)
        norm = functionalNorm(r / rscale)
        return -np.log(norm)

    init_points = 10
    train_X = torch.rand(init_points, n, dtype=torch.float64)
    bounds = torch.stack([torch.zeros(n), torch.ones(n)])
    j = 0
    for tag in tags:
        train_X[:,j] = tags[tag][0] + (tags[tag][1] - tags[tag][0]) * train_X[:,j]
        bounds[0,j] = tags[tag][0]
        bounds[1,j] = tags[tag][1]
        j += 1
    train_Y = torch.zeros(init_points,1)
    for i in range(init_points):
        train_Y[i] = functionalLogNorm(train_X[i,:])
    print(train_X)
    print(train_Y)
    print(bounds)

    bestNorm = -np.Inf
    for i in range(maxIts-init_points):
        gp = SingleTaskGP(train_X, train_Y)
        mll = ExactMarginalLogLikelihood(gp.likelihood, gp)
        fit_gpytorch_model(mll);

        UCB = UpperConfidenceBound(gp, beta=3)

        candidate, acq_value = optimize_acqf(UCB, bounds=bounds, q=1, num_restarts=5, raw_samples=20)
        norm = functionalLogNorm(candidate[0])

        print(f'Iteration {i + init_points + 1}: {candidate}, {np.exp(-norm)}')
        train_X = torch.cat((train_X,candidate),0)
        train_Y = torch.cat((train_Y,torch.tensor([[norm]])),0)
        if norm > bestNorm:
            bestNorm = norm
            bestCand = candidate

    print()
    print(f'Best candidate is {bestCand} with norm {np.exp(-bestNorm)}')

class OptimaException(Exception):
    pass
