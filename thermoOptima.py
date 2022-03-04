import numpy as np
import os
import re
import PySimpleGUI as sg
import shutil
import subprocess
import json
import optimaData
import optima
import math
import functools

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

def getPointValidationValues(tags, beta):
    shutil.copy('fcctest.dat','optima.dat')
    for i in range(len(tags)):
        subprocess.call(['sed', '-i', '-e',  f's/<{tags[i]}>/{beta[i]}/g', 'optima.dat'])
    subprocess.run(['../../thermochimicastuff/thermochimica/bin/RunCalculationList','validationPoints.ti'])

    jsonFile = open('../../thermochimicastuff/thermochimica/thermoout.json',)
    try:
        data = json.load(jsonFile)
        jsonFile.close()
    except:
        jsonFile.close()
        print('Data load failed')
        return

    m = len(list(data.keys()))
    f = np.zeros(m)
    for i in list(data.keys()):
        f[int(i)-1] = data[i]['integral Gibbs energy']
    return f

class ThermochimicaOptima:
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
        # Automatically open a window for initial conditions
        self.tagWindow = optimaData.TagWindow(self.datafile,windowList)
        self.children.append(self.tagWindow)
        self.validationPoints = []
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
        if event == 'Add Validation Data':
            # Get the number of points to be added. This window will (should) be blocking.
            npoints = 0
            npointsLayout = [[sg.Text('Number of validation calculations:'),sg.Input(key = '-npoints-',size = [inputSize,1])],
                             [sg.Button('Accept'),sg.Button('Cancel')]]
            npointsWindow = sg.Window('Invalid value notification',npointsLayout,location=[400,0],finalize=True,keep_on_top=True)
            while True:
                event, values = npointsWindow.read(timeout=timeout)
                if event == sg.WIN_CLOSED or event == 'Cancel':
                    break
                if event == 'Accept':
                    try:
                        npoints = int(values['-npoints-'])
                        if npoints >= 0:
                            break
                        else:
                            npoints = 0
                    except ValueError:
                        pass
                    print('Invalid number of points')
            npointsWindow.close()
            if npoints > 0:
                self.pointWindow = optimaData.PointValidationWindow(npoints,self.elements,self.validationPoints,windowList)
                self.children.append(self.pointWindow)
        if event == 'Run':
            self.run()
    def run(self):
        # get problem dimensions
        m = len(self.validationPoints)
        n = len(self.tagWindow.tags)
        # check that we have enough data to go ahead
        if not self.tagWindow.valid:
            print('Initial estimates for coefficients not completed')
            return
        if m == 0:
            print('Validation points not completed')
            return

        # Use currying to send tags to getPointValidationValues, so we don't have to pass more stuff to Optima
        validationFunction = functools.partial(getPointValidationValues,self.tagWindow.tags)
        # call Optima
        optima.optimize(self.validationPoints,
                        self.tagWindow.initialValues[0],
                        self.tagWindow.initialValues[1],
                        validationFunction,
                        self.maxIts,
                        self.tol)

windowList = []
ThermochimicaOptima()
while len(windowList) > 0:
    for window in windowList:
        window.read()
