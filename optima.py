import numpy as np
import os
import re
import PySimpleGUI as sg
import shutil
import subprocess
import json

timeout = 50
inputSize = 16

futureBlue = '#003C71'
simcoeBlue = '#0077CA'
techTangerine = '#E75D2A'
coolGrey = '#A7A8AA'
sg.theme_add_new('OntarioTech', {'BACKGROUND': futureBlue,
                                 'TEXT': 'white',
                                 'INPUT': 'white',
                                 'TEXT_INPUT': 'black',
                                 'SCROLL': coolGrey,
                                 'BUTTON': ('white', techTangerine),
                                 'PROGRESS': ('#01826B', '#D0D0D0'),
                                 'BORDER': 1,
                                 'SLIDER_DEPTH': 0,
                                 'PROGRESS_DEPTH': 0})
sg.theme('OntarioTech')

atomic_number_map = [
    'H','He','Li','Be','B','C','N','O','F','Ne','Na','Mg','Al','Si','P',
    'S','Cl','Ar','K','Ca','Sc','Ti','V','Cr','Mn','Fe','Co','Ni','Cu','Zn',
    'Ga','Ge','As','Se','Br','Kr','Rb','Sr','Y','Zr','Nb','Mo','Tc','Ru','Rh',
    'Pd','Ag','Cd','In','Sn','Sb','Te','I','Xe','Cs','Ba','La','Ce','Pr','Nd',
    'Pm','Sm','Eu','Gd','Tb','Dy','Ho','Er','Tm','Yb','Lu','Hf','Ta','W','Re',
    'Os','Ir','Pt','Au','Hg','Tl','Pb','Bi','Po','At','Rn','Fr','Ra','Ac','Th',
    'Pa','U','Np','Pu','Am','Cm','Bk','Cf','Es','Fm','Md','No','Lr','Rf','Db',
    'Sg','Bh','Hs','Mt','Ds','Rg','Cn','Nh','Fl','Mc','Lv','Ts', 'Og'
]

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
        betaNew = np.zeros(n)
        # Print results to screen:
        for j in range(n):
            print(f'{j} {x[j]} {coefficient[j] + steplength * x[j]}')
            betaNew[j] = coefficient[j] + steplength * x[j]
        return betaNew
    except np.linalg.LinAlgError:
        print('There was a problem in solving the system of linear equations.')

tol = 1e-3
maxIts = 10

broydenMatrix = np.ones([6,1])

y = np.array([-1.5318396900905138E+003,
              -2.1601132664119210E+004,
              -4.6885671070912082E+004,
              -7.5678723908701446E+004,
              -1.0721653913730988E+005,
              -1.4109338905291763E+005])

beta = np.array([1])
betaOld = beta

shutil.copy('fcctest.dat','optima.dat')
subprocess.call(['sed', '-i', '-e',  f's/<mix 1>/{beta[0]}/g', 'optima.dat'])
subprocess.run(['../../thermochimicastuff/thermochimica/bin/InputScriptMode','fcctest.ti'])

jsonFile = open('../../thermochimicastuff/thermochimica/thermoout.json',)
try:
    data = json.load(jsonFile)
    jsonFile.close()
except:
    jsonFile.close()
    print('Data load failed')

f = np.zeros(6)
for i in list(data.keys()):
    f[int(i)-1] = data[i]['integral Gibbs energy']

print(f)
# f = np.array([0.4, 0.45, 0.8])

r = f - y
rOld = r

# Compute the functional norm:
norm = functionalNorm(r)
print(norm)

beta = np.array([1.01])

for n in range(maxIts):
    shutil.copy('fcctest.dat','optima.dat')
    subprocess.call(['sed', '-i', '-e',  f's/<mix 1>/{beta[0]}/g', 'optima.dat'])
    subprocess.run(['../../thermochimicastuff/thermochimica/bin/InputScriptMode','fcctest.ti'])

    jsonFile = open('../../thermochimicastuff/thermochimica/thermoout.json',)
    try:
        data = json.load(jsonFile)
        jsonFile.close()
    except:
        jsonFile.close()
        print('Data load failed')

    f = np.zeros(6)
    for i in list(data.keys()):
        f[int(i)-1] = data[i]['integral Gibbs energy']

    print(f)

    s = beta - betaOld
    r = f - y
    t = rOld - r

    # Update vectors for succeeding iteration:
    betaOld = beta
    rOld = r

    # Compute the functional norm:
    norm = functionalNorm(r)
    print(norm)
    if norm < tol:
        break

    # Update the Broyden matrix:
    broyden(broydenMatrix, t, s)
    # Compute the direction vector:
    beta = directionVector(r, broydenMatrix, beta, 1, 1)
    print(beta)


print(beta)
