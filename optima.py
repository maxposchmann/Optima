import numpy as np
import os
import re
import PySimpleGUI as sg
import shutil
import subprocess
import json
import optimaData
import math

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
        [x, residuals, rank, singular] = np.linalg.lstsq(a,b,rcond=None)
        betaNew = np.zeros(n)
        # Print results to screen:
        for j in range(n):
            betaNew[j] = coefficient[j] + steplength * x[j]
        return betaNew
    except np.linalg.LinAlgError:
        print('There was a problem in solving the system of linear equations.')

def getFuntionalValues(tags, beta):
    shutil.copy('fcctest.dat','optima.dat')
    for i in range(len(tags)):
        subprocess.call(['sed', '-i', '-e',  f's/<{tags[i]}>/{beta[i]}/g', 'optima.dat'])
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
    return f

class Optima:
    def __init__(self):
        self.tol = 1e-4
        self.maxIts = 300
        self.datafile = 'fcctest.dat'
        self.elements = []
        # Get element names so that we can set up the calculation and windows
        with open(self.datafile) as f:
            f.readline() # read comment line
            line = f.readline() # read first data line (# elements, # phases, n*# species)
            nElements = int(line[1:5])
            nSoln = int(line[6:10])
            while True:
                line = f.readline() # read the rest of the # species but don't need them)
                if any(c.isalpha() for c in line):
                    break
            elLen = 25 # element names are formatted 25 wide
            els = line # get the first line with letters in it
            for i in range(math.ceil(nElements/3)):
                for j in range(3):
                    self.elements.append(els[1+j*elLen:(1+j)*elLen].strip())
                els = f.readline() # read a line of elements (3 per line)
                # It doesn't matter now, but this reads one more line than required
        for el in self.elements:
            try:
                index = atomic_number_map.index(el)+1 # get element indices in PT (i.e. # of protons)
            except ValueError:
                if len(el) > 0:
                    if el[0] != 'e':
                        print(el+' not in list') # if the name is bogus (or e(phase)), discard
                self.elements = list(filter(lambda a: a != el, self.elements))
        windowList.append(self)
        buttonLayout = [[sg.Button('Edit Coefficients')],
                        [sg.Button('Add Validation Data')],
                        [sg.Button('Remove Validation Data')],
                        [sg.Button('Edit Validation Data')],
                        [sg.Button('Run')]]
        self.sgw = sg.Window('Optima', [buttonLayout], location = [0,0], finalize=True)
        self.children = []
        self.tagWindow = optimaData.TagWindow(self.datafile,windowList)
        self.children.append(self.tagWindow)
    def close(self):
        for child in self.children:
            child.close()
        self.sgw.close()
        if self in windowList:
            windowList.remove(self)
    def read(self):
        event, values = self.sgw.read(timeout=timeout)
        if event == sg.WIN_CLOSED or event == 'Cancel':
            self.close()
        if event == 'Edit Coefficients':
            self.tagWindow.close()
            self.tagWindow.open()
        if event == 'Run':
            self.run()
    def run(self):
        if not self.tagWindow.valid:
            print('Initial estimates for coefficients not completed')
            return
        m = 6
        n = len(self.tagWindow.tags)
        broydenMatrix = np.ones([m,n])

        y = np.array([-1.5318396900905138E+003,
                      -2.1601132664119210E+004,
                      -4.6885671070912082E+004,
                      -7.5678723908701446E+004,
                      -1.0721653913730988E+005,
                      -1.4109338905291763E+005])

        beta = np.array(self.tagWindow.initialValues[0])
        betaOld = beta

        f = getFuntionalValues(self.tagWindow.tags,beta)

        r = f - y
        rOld = r

        # Compute the functional norm:
        norm = functionalNorm(r)

        beta = np.array(self.tagWindow.initialValues[1])

        for iteration in range(self.maxIts):
            f = getFuntionalValues(self.tagWindow.tags,beta)

            s = beta - betaOld
            r = f - y
            t = rOld - r

            # Update vectors for succeeding iteration:
            betaOld = beta
            rOld = r

            # Compute the functional norm:
            norm = functionalNorm(r)
            print(norm)
            if norm < self.tol:
                print(f'{beta} after {iteration+1}')
                break

            # Update the Broyden matrix:
            broyden(broydenMatrix, t, s)
            # Compute the direction vector:
            l = 1/(iteration+1)**2
            steplength = 1
            beta = directionVector(r, broydenMatrix, beta, l, steplength)
            print(beta)

windowList = []
Optima()
while len(windowList) > 0:
    for window in windowList:
        window.read()
