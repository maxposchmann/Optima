import numpy as np

def functionalNorm(residual):
    norm = 0
    for i in range(len(residual)):
        norm += residual[i]**2
    return norm

def broyden(broydenMatrix,dependent,objective):
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

# Make this class general. Avoid to the greatest extent possible including any application-specific code.
# Any methods required to call Thermochimica (or other) should be imported from another class.
def optimize(validationPoints,initial0,initial1,getFunctionalValuesFunction,maxIts,tol):
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

    # initialize Broyden matrix as 1s
    broydenMatrix = np.ones([m,n])

    # y is dependent true values from validation data set
    y = np.array([validationPoints[i][-1] for i in range(m)])

    # beta is array of coefficients, start with initial value 0
    beta = np.array(initial0)
    betaOld = beta

    f = getFunctionalValuesFunction(beta)

    r = f - y
    rOld = r

    # Compute the functional norm:
    norm = functionalNorm(r)

    # now change to initial value 1, then enter loop
    beta = np.array(initial1)

    for iteration in range(maxIts):
        # calculate the functional values
        # leave this call straightforward: want to be able to swap this function for any other black box
        f = getFunctionalValuesFunction(beta)

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
            print(f'{beta} after {iteration+1}')
            break

        # Update the Broyden matrix:
        broyden(broydenMatrix, t, s)
        # Compute the direction vector:
        l = 1/(iteration+1)**2
        steplength = 1
        # calculate update to coefficients
        beta = directionVector(r, broydenMatrix, beta, l, steplength)
        print(f'Current coefficients: {beta}')
