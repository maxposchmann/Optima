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
        x = np.linalg.lstsq(a,b,rcond=None)
        # Print results to screen:
        for j in range(n):
            print(f'{j} {x[j]} {coefficient[j] + steplength * x[j]}')
    except np.linalg.LinAlgError:
        print('There was a problem in solving the system of linear equations.')

broydenMatrix = np.ones([3,1])

y = np.array([0.25, 0.5, 0.75])

beta = np.array([1])
betaOld = beta

f = np.array([0.4, 0.45, 0.8])

r = f - y
rOld = r

# Compute the functional norm:
norm = functionalNorm(r)
print(norm)

beta = np.array([1.01])

s = beta - betaOld

f = np.array([0.36, 0.47, 0.79])
r = f - y
t = rOld - r

# Compute the functional norm:
norm = functionalNorm(r)
print(norm)

# Update the Broyden matrix:
broyden(broydenMatrix, t, s)
# Compute the direction vector:
directionVector(r, broydenMatrix, beta, 1, 1)

# Update vectors for succeeding iteration:
betaOld = beta
rOld = r
