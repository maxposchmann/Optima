import numpy as np
import os
import re
import PySimpleGUI as sg
import shutil
import subprocess
import json
import dataThermoOptima
import optima
import math
import dictTools

timeout = 50
inputSize = 8,
buttonSize = 20
keyNameWidth = 18

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

def getPointValidationValues(updateInputFunction, validation, tags, beta, thermochimica_path, database):
    # Call update function
    updateInputFunction(tags, beta)

    # Run input files and store data
    f = []
    for n_val in range(len(validation)):
        validationKeys = list(validation[n_val].keys())
        if validation[n_val]['type'] == 'point':
            subprocess.run([thermochimica_path + '/bin/RunCalculationList',f'validationPoints-{n_val}.ti'])

            jsonFile = open(thermochimica_path + '/outputs/thermoout.json',)
            try:
                data = json.load(jsonFile)
                jsonFile.close()
            except:
                jsonFile.close()
                print('Data load failed')
                raise optima.OptimaException

            for i in range(len(validationKeys)):
                if validationKeys[i] == 'type':
                    continue
                if len(data[str(i+1)].keys()) == 0:
                    print('Thermochimica calculation failed to converge')
                    raise optima.OptimaException
                # Get all comparison values per calculation
                calcValues = []
                dictTools.getParallelDictValues(validation[n_val][validationKeys[i]]['values'],data[str(i+1)],calcValues)
                f.extend(calcValues)
        elif validation[n_val]['type'] == 'mixing':
            import sys
            sys.path.append(f'{thermochimica_path}/python')
            import propertyOfMixing

            for i in range(len(validationKeys)):
                if validationKeys[i] == 'type':
                    continue

                phase = validation[n_val][validationKeys[i]]['phase']
                temperature = validation[n_val][validationKeys[i]]['temperature']
                # Get default values if not specified
                if 'tunit' in validation[n_val][validationKeys[i]].keys():
                    tunit = validation[n_val][validationKeys[i]]['tunit']
                else:
                    tunit = 'K'
                if 'munit' in validation[n_val][validationKeys[i]].keys():
                    munit = validation[n_val][validationKeys[i]]['munit']
                else:
                    munit = 'moles'
                if 'punit' in validation[n_val][validationKeys[i]].keys():
                    punit = validation[n_val][validationKeys[i]]['punit']
                else:
                    punit = 'atm'
                if 'pressure' in validation[n_val][validationKeys[i]].keys():
                    pressure = validation[n_val][validationKeys[i]]['pressure']
                else:
                    pressure = 1
                endpoints = validation[n_val][validationKeys[i]]['endpoints']
                mixtures = validation[n_val][validationKeys[i]]['mixtures']

                # Loop over all properties used
                for property in validation[n_val][validationKeys[i]]['properties']:
                    calcValues = propertyOfMixing.propertyOfMixing(property,
                                                                   phase,
                                                                   temperature,
                                                                   endpoints,
                                                                   mixtures,
                                                                   database,
                                                                   tunit = tunit,
                                                                   munit = munit,
                                                                   punit = punit,
                                                                   pressure = pressure,
                                                                   thermochimica_path = thermochimica_path)
                    f.extend(calcValues)

    f = np.array(f)
    return f

def updateDat(tags, beta):
    shutil.copy('optima-inter.dat','optima.dat')
    keys = list(tags.keys())
    for i in range(len(tags)):
        subprocess.call(['sed', '-i', '-e',  f's/<{keys[i]}>/{beta[i]}/g', 'optima.dat'])

def createIntermediateDat(tags,filename):
    shutil.copy(filename,'optima-inter.dat')
    tagCheck = []
    for tag in tags:
        if tags[tag]['optimize']:
            tagCheck.append((tag, tags[tag]['initial']))
        else:
            subprocess.call(['sed', '-i', '-e',  f's/<{tag}>/{tags[tag]["initial"][0]}/g', 'optima-inter.dat'])
    return dict(tagCheck)

class ThermochimicaOptima:
    def __init__(self):
        self.children = []
        # Default parameters
        self.tol = 1e-4
        self.maxIts = 30
        # self.datafile = 'fcctest.dat'
        self.datafile = 'kaye-drivingForce.dat'
        self.thermochimica_path = 'thermochimica'
        # Parse datafile
        self.parseDatabase()
        # Set up window
        windowList.append(self)
        buttonLayout   = [
                         [sg.Button('Choose Database', size = buttonSize)],
                         [sg.Button('Edit Coefficients', size = buttonSize)],
                         [sg.Button('Add Validation Data', size = buttonSize)],
                         [sg.Button('Clear Validation Data', size = buttonSize)],
                         [sg.Button('Edit Validation Data', size = buttonSize)],
                         [sg.Button('Save Validation Data', size = buttonSize), sg.Input(key='-saveValidationName-',size=16), sg.Text('.json')],
                         [sg.Button('Load Validation Data', size = buttonSize), sg.Input(key='-loadValidationName-',size=16), sg.Text('.json')],
                         [sg.Button('Run', size = buttonSize)]
                         ]
        broydenLayout  = sg.Column([
                                   [sg.Radio('Levenberg-Marquardt + Broyden', 'methods', default=True, enable_events=True, key='LMB')],
                                   [sg.Text('Tolerance:', size = keyNameWidth),sg.Input(key = '-tol-', size = inputSize)],
                                   [sg.Text('Max Iterations:', size = keyNameWidth),sg.Input(key = '-maxIts-', size = inputSize)]
                                   ], expand_x=True, expand_y=True)
        bayesianLayout = sg.Column([
                                   [sg.Radio('Bayesian optimization', 'methods', default=False, enable_events=True, key='Bayes')],
                                   [sg.Text('Total Iterations:', size = keyNameWidth),sg.Input(key = '-totalIts-', size = inputSize)],
                                   [sg.Text('Startup iterations:', size = keyNameWidth),sg.Input(key = '-startIts-', size = inputSize)],
                                   [sg.Text('Acquisition Function:', size = keyNameWidth),sg.Combo(['Upper Confidence Bounds', 'Expected Improvement', 'Probability of Improvement'], default_value = 'Upper Confidence Bounds', key = '-acq-')],
                                   [sg.Text('Eta:', size = keyNameWidth),sg.Input(key = '-eta-', size = inputSize)],
                                   [sg.Text('Kappa:', size = keyNameWidth),sg.Input(key = '-kappa-', size = inputSize)],
                                   [sg.Text('Kappa Decay:', size = keyNameWidth),sg.Input(key = '-kappa_decay-', size = inputSize)],
                                   [sg.Text('Kappa Decay Delay:', size = keyNameWidth),sg.Input(key = '-kappa_decay_delay-', size = inputSize)]
                                   ], expand_x=True, expand_y=True)
        methodLayout   = [[sg.Text('Select Optimization Method:')],[broydenLayout,bayesianLayout]]
        self.sgw = sg.Window('Optima', [buttonLayout,methodLayout], location = [0,0], finalize=True)

        self.validationPoints = [] #dict([])
        # Set default method to Levenberg-Marquardt + Broyden
        self.method = optima.LevenbergMarquardtBroyden
        # stuff for writing input file (hardcode values for now)
        self.datfile = f'{os.getcwd()}/optima.dat'
        self.tunit = 'K'
        self.punit = 'atm'
        self.munit = 'moles'
        self.extraParams = {}
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
        elif event == 'Choose Database':
            databaseWindow = DatabaseWindow(self)
            self.children.append(databaseWindow)
        elif event == 'Edit Coefficients':
            self.tagWindow.close()
            self.tagWindow.open()
        elif event == 'Add Validation Data':
            # Get the number of points to be added. This window will (should) be blocking.
            npoints = 0
            npointsLayout = [[sg.Text('Number of validation calculations:'),sg.Input(key = '-npoints-',size = [inputSize,1])],
                             [sg.Combo(['Points','Mixtures'], default_value = 'Points', key = '-valType-')],
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
                if values['-valType-'] == 'Points':
                    self.pointWindow = dataThermoOptima.PointValidationWindow(npoints,self.elements,self.phaseData,self.validationPoints,windowList)
                elif values['-valType-'] == 'Mixtures':
                    self.pointWindow = dataThermoOptima.MixtureValidationWindow(npoints,self.elements,self.phaseData,self.validationPoints,windowList)
                self.children.append(self.pointWindow)
        elif event == 'Clear Validation Data':
            self.validationPoints = [] #dict([])
            print('Validation data cleared')
        elif event == 'Edit Validation Data':
            editDataWindow = EditDataWindow(self.validationPoints,self.elements,self.phaseData)
            self.children.append(editDataWindow)
        elif event == 'Save Validation Data':
            if values['-saveValidationName-'] == '':
                filename = 'validationData.json'
            else:
                filename = f'{values["-saveValidationName-"]}.json'
            self.saveValidation(filename)
        elif event == 'Load Validation Data':
            if values['-loadValidationName-'] == '':
                filename = 'validationData.json'
            else:
                filename = f'{values["-loadValidationName-"]}.json'
            self.loadValidation(filename)
        elif event == 'Run':
            try:
                if values['-tol-'] == '':
                    # let blank reset to default
                    self.tol = 1e-4
                else:
                    tol = float(values['-tol-'])
                    if tol > 0:
                        self.tol = tol
            except ValueError:
                print('Invalid tolerance')
                return
            try:
                if self.method == optima.LevenbergMarquardtBroyden:
                    if values['-maxIts-'] == '':
                        # let blank reset to default
                        self.maxIts = 30
                    else:
                        maxIts = int(values['-maxIts-'])
                        if maxIts > 0:
                            self.maxIts = maxIts
                elif self.method == optima.Bayesian:
                    if values['-totalIts-'] == '':
                        # let blank reset to default
                        self.maxIts = 30
                    else:
                        maxIts = int(values['-totalIts-'])
                        if maxIts > 0:
                            self.maxIts = maxIts
            except ValueError:
                print('Invalid iterations')
                return
            # Bayesian already has default values for optional parameters, so only load valid values in
            self.extraParams = {}
            try:
                start = int(values['-startIts-'])
                if start > 0:
                    self.extraParams['init_points'] = start
            except ValueError:
                pass
            try:
                eta = float(values['-eta-'])
                if eta > 0 and eta <= 1:
                    self.extraParams['eta'] = eta
            except ValueError:
                pass
            try:
                kappa = float(values['-kappa-'])
                if kappa > 0:
                    self.extraParams['kappa'] = kappa
            except ValueError:
                pass
            try:
                kappa_decay = float(values['-kappa_decay-'])
                if kappa_decay > 0 and kappa_decay <= 1:
                    self.extraParams['kappa_decay'] = kappa_decay
            except ValueError:
                pass
            try:
                kappa_decay_delay = int(values['-kappa_decay_delay-'])
                if kappa_decay_delay >= 0:
                    self.extraParams['kappa_decay_delay'] = kappa_decay_delay
            except ValueError:
                pass
            if values['-acq-'] == 'Upper Confidence Bounds':
                self.extraParams['acq'] = 'ucb'
            elif values['-acq-'] == 'Expected Improvement':
                self.extraParams['acq'] = 'ei'
            elif values['-acq-'] == 'Probability of Improvement':
                self.extraParams['acq'] = 'poi'
            self.run()
        elif event == 'LMB':
            # Set method to Levenberg-Marquardt + Broyden
            self.method = optima.LevenbergMarquardtBroyden
        elif event == 'Bayes':
            # Set method to Bayesian optimization
            self.method = optima.Bayesian
    def run(self):
        # Get initial problem dimensions
        m = np.sum([len(points) for points in self.validationPoints])
        n = len(self.tagWindow.tags)
        # Check that we have enough data to go ahead
        if m == 0:
            print('Validation points not completed')
            return
        if n == 0:
            print('Initial estimates for coefficients not completed')
            return
        # Write input file
        self.writeFile()
        # Call tag preprocessor
        intertags = createIntermediateDat(self.tagWindow.tags,self.datafile)
        # Use currying to package validationPoints with getPointValidationValues
        def getValues(tags, beta):
            return getPointValidationValues(updateDat, self.validationPoints, tags, beta, self.thermochimica_path, self.datfile)
        # Get validation value/weight pairs
        validationPairs = []
        for points in self.validationPoints:
            validationKeys = list(points.keys())
            if points['type'] == 'point':
                for i in range(len(points)):
                    if validationKeys[i] == 'type':
                        continue
                    calcValues = []
                    dictTools.getParallelDictValues(points[validationKeys[i]]['values'],
                                                    points[validationKeys[i]]['values'],
                                                    calcValues)
                    validationPairs.extend(calcValues)
            elif points['type'] == 'mixing':
                for i in range(len(points)):
                    if validationKeys[i] == 'type':
                        continue
                    for property in points[validationKeys[i]]['values']:
                        validationPairs.extend(property)
        # Real problem size is number of value/weight pairs x number of tags to be optimized
        m = len(validationPairs)
        n = len(intertags)
        # Setup validation and weights arrays
        y = np.zeros(m)
        weight = np.ones(m)
        for i in range(m):
            if isinstance(validationPairs[i],list):
                y[i] = validationPairs[i][0]
                weight[i] = validationPairs[i][1]
            else:
                y[i] = validationPairs[i]
        # Get scale from tags dict
        scale = []
        for tag in intertags.keys():
            scale.append(self.tagWindow.tags[tag]['scale'])
        scale = np.array(scale)

        # Call Optima
        norm, iterations, beta = self.method(y,
                                 intertags,
                                 getValues,
                                 self.maxIts,
                                 self.tol,
                                 weight = weight,
                                 scale = scale,
                                 **self.extraParams)
        print(f'Best norm: {norm}')
        print(f'With beta: {beta}')
    def saveValidation(self, filename):
        if len(self.validationPoints) == 0:
            print('Cannot save empty validation set')
            return
        with open(filename, 'w') as outfile:
            json.dump(self.validationPoints, outfile, indent=4)
    def loadValidation(self, filename):
        jsonFile = open(filename,)
        try:
            newVal = json.load(jsonFile)
            jsonFile.close()
        except:
            jsonFile.close()
            print('Data load failed')
            return
        # Want to be able to save/load multiple validation dicts per file
        # But also just the old single
        # So if an old single dict, just turn it into an array
        if isinstance(newVal,dict):
            newVal = [newVal]
        for newPoints in newVal:
            if len(newPoints) > 0:
                startIndex = 0
                i = 0
                oldKeys = list(newPoints.keys())
                # create a new dict to edit the keys to avoid overlapping keys
                rekeyedPoints = dict([])
                for point in oldKeys:
                    if point == 'type':
                        rekeyedPoints['type'] = newPoints.pop(point)
                    else:
                        rekeyedPoints[startIndex + i] = newPoints.pop(point)
                        i += 1
                # Set default type as a point calculation
                if 'type' not in rekeyedPoints.keys():
                    rekeyedPoints['type'] = 'point'
                self.validationPoints.append(rekeyedPoints)
                print(f'{len(rekeyedPoints) - 1} validation points loaded')
            else:
                print('No entries in validation JSON')
    def writeFile(self):
        for n_val in range(len(self.validationPoints)):
            if self.validationPoints[n_val]['type'] == 'point':
                with open(f'validationPoints-{n_val}.ti', 'w') as inputFile:
                    inputFile.write('! Optima-generated input file for validation points\n')
                    inputFile.write(f'data file         = {self.datfile}\n')
                    inputFile.write(f'temperature unit  = {self.tunit}\n')
                    inputFile.write(f'pressure unit     = {self.punit}\n')
                    inputFile.write(f'mass unit         = {self.munit}\n')
                    inputFile.write(f'nEl               = {len(self.elements)} \n')
                    inputFile.write(f'iEl               = {" ".join([str(atomic_number_map.index(element)+1) for element in self.elements])}\n')
                    inputFile.write(f'nCalc             = {len(self.validationPoints[n_val])}\n')
                    for point in self.validationPoints[n_val].keys():
                        if point == 'type':
                            continue
                        inputFile.write(f'{" ".join([str(self.validationPoints[n_val][point]["state"][i]) for i in range(len(self.elements)+2)])}\n')
    def parseDatabase(self):
        self.elements = []
        if self.datafile == '':
            return
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

        # Parse phase/species names
        subprocess.run([f'{self.thermochimica_path}/bin/ParseDataOnly',self.datafile])
        jsonFile = open(f'{self.thermochimica_path}/phaseLists.json',)
        try:
            self.phaseData = json.load(jsonFile)
            jsonFile.close()
        except:
            jsonFile.close()
            print('Phase data load failed')
            return

        # Automatically open a window for initial conditions
        try:
            # Close old tagWindow if exists
            self.tagWindow.close()
        except AttributeError:
            pass
        self.tagWindow = dataThermoOptima.TagWindow(self.datafile,windowList)
        self.children.append(self.tagWindow)

class EditDataWindow:
    def __init__(self,points,elements,phaseData):
        self.points = points
        self.elements = elements
        self.phaseData = phaseData
        windowList.append(self)

        self.maxValueDepth = 5
        self.valueOptions = [[] for _ in range(self.maxValueDepth)]
        self.valueOptions[0] = ['integral Gibbs energy','heat capacity','enthalpy','entropy','solution phases','pure condensed phases','elements']

        self.open()

        self.tlo = -np.Inf
        self.thi = np.Inf
        self.getData()
        self.children = []
    def close(self):
        for child in self.children:
            child.close()
        self.sgw.close()
        if self in windowList:
            windowList.remove(self)
    def open(self):
        dataColumn = [
            [sg.Text('Data Points')],
            [sg.Listbox(values=[], enable_events=True, size=(30, 50), key='-dataList-')]
        ]
        outputColumn = [
            [sg.Text('Validation Point Details')],
            [sg.Multiline(key='-details-', size=(80,20))],
            [sg.Text(key = '-status-')],
            [sg.Text('Change Values', font='underline')],
            [sg.Text('Temperature'), sg.Input(key='-temp-',size=(inputSize,1))],
            [sg.Text('Pressure'), sg.Input(key='-pres-',size=(inputSize,1))]
            ]
        # Create mass rows
        outputColumn.extend([[sg.Text(f'{self.elements[i]} concentration'),sg.Input(key=f'-{self.elements[i]}-',size=(inputSize,1))] for i in range(len(self.elements))])
        # Buttons for state
        outputColumn.extend([[sg.Button('Update State', disabled = True), sg.Button('Delete Point', disabled = True)]])
        # Dropdowns for values
        outputColumn.extend([[sg.Combo(self.valueOptions[row], key = f'-type-{row}-', enable_events = True, size = 25)] for row in range(self.maxValueDepth)])
        outputColumn.extend([
            [sg.Input(key=f'-value-',size=inputSize)],
            [sg.Button('Update Value', disabled = True), sg.Button('Delete Value', disabled = True)],
            [sg.Text('Filter Points', font='underline')],
            [sg.Text('Temperature Range:')],
            [sg.Input(key='-tfilterlow-',size=(inputSize,1)),sg.Input(key='-tfilterhi-',size=(inputSize,1))],
            [sg.Button('Apply Filter')]
            ])
        self.sgw = sg.Window('Data inspection',
            [[sg.Pane([
                sg.Column(dataColumn, element_justification='l', expand_x=True, expand_y=True),
                sg.Column(outputColumn, element_justification='c', expand_x=True, expand_y=True)
            ], orientation='h', k='-PANE-')]],
            location = [100,0], finalize=True)
    def read(self):
        event, values = self.sgw.read(timeout=timeout)
        if event == sg.WIN_CLOSED or event == 'Exit':
            self.close()
        elif event == '-dataList-':
            if not values['-dataList-']:
                return
            self.setIndex = values['-dataList-'][0][0]
            self.point = values['-dataList-'][0][1]
            self.updateDetails()
            self.sgw.Element('Update State').Update(disabled = False)
            self.sgw.Element('Delete Point').Update(disabled = False)
            self.sgw.Element('Update Value').Update(disabled = False)
            self.sgw.Element('Delete Value').Update(disabled = False)
        elif event == 'Apply Filter':
            try:
                self.tlo = float(values['-tfilterlow-'])
            except:
                if values['-tfilterlow-'] == '':
                    self.tlo = -np.Inf
                else:
                    return
            try:
                self.thi = float(values['-tfilterhi-'])
            except:
                if values['-tfilterhi-'] == '':
                    self.thi = np.Inf
                else:
                    return
            self.getData()
        elif event == 'Delete Point':
            del self.points[self.setIndex][self.point]
            self.getData()
            self.sgw.Element('Update State').Update(disabled = True)
            self.sgw.Element('Delete Point').Update(disabled = True)
            self.sgw.Element('Update Value').Update(disabled = True)
            self.sgw.Element('Delete Value').Update(disabled = True)
        elif event == 'Update State':
            try:
                self.points[self.setIndex][self.point]['state'][0] = float(values['-temp-'])
            except ValueError:
                pass
            try:
                self.points[self.setIndex][self.point]['state'][1] = float(values['-pres-'])
            except ValueError:
                pass
            for i in range(len(self.elements)):
                try:
                    self.points[self.setIndex][self.point]['state'][i+2] = float(values[f'-{self.elements[i]}-'])
                except ValueError:
                    pass
            self.getData()
            self.updateDetails()
        elif event == 'Update Value':
            keyList = ['values'] + [values[f'-type-{row}-'] for row in range(self.maxValueDepth)]
            try:
                value = float(values[f'-value-'])
            except ValueError:
                # Blank/invalid values will be skipped
                pass
            else:
                dictTools.nestedDictWriter(self.points[self.setIndex][self.point],value,*keyList)
            self.updateDetails()
        elif event == 'Delete Value':
            if not values['-type-0-']:
                return
            keyList = ['values'] + [values[f'-type-{row}-'] for row in range(self.maxValueDepth)]
            try:
                dictTools.nestedDictDeleter(self.points[self.setIndex][self.point],*keyList)
            except KeyError:
                # Skip if key not present
                pass
            self.updateDetails()
        elif '-type-' in event:
            # Recover indices from event key
            eventSplit = event.split('-')
            row = int(eventSplit[2])
            def resetFromRow():
                for r in range(row + 1,self.maxValueDepth):
                    self.sgw[f'-type-{r}-'].update(value='', values=[])

            if values[event] == 'elements':
                resetFromRow()
                self.sgw[f'-type-{row+1}-'].update(value='', values=self.elements)
                if row == 0:
                    self.sgw[f'-type-{row+2}-'].update(value='element potential', values=['element potential'])
                elif row == 2:
                    self.sgw[f'-type-{row+2}-'].update(value='', values=['moles of element in phase','mole fraction of phase by element','mole fraction of element by phase'])
            elif values[event] == 'solution phases':
                resetFromRow()
                self.sgw[f'-type-{row+1}-'].update(value='', values=list(self.phaseData['solution phases'].keys()))
                self.sgw[f'-type-{row+2}-'].update(value='', values=['moles','driving force','species','sublattices','elements'])
            elif values[event] == 'pure condensed phases':
                resetFromRow()
                self.sgw[f'-type-{row+1}-'].update(value='', values=self.phaseData['pure condensed phases'])
                self.sgw[f'-type-{row+2}-'].update(value='', values=['moles','chemical potential','driving force','elements'])
            elif values[event] == 'species':
                resetFromRow()
                self.sgw[f'-type-{row+1}-'].update(value='', values=list(self.phaseData['solution phases'][values[f'-type-{1}-']]['species']))
                self.sgw[f'-type-{row+2}-'].update(value='', values=['mole fraction','moles','chemical potential'])
            elif row == 0:
                resetFromRow()
    def getData(self):
        self.data = []
        i = -1
        for pointSet in self.points:
            i += 1
            if pointSet['type'] not in ('point'):
                continue
            for point in pointSet:
                if point == 'type':
                    continue
                if self.tlo <= pointSet[point]["state"][0] and self.thi >= pointSet[point]["state"][0]:
                    self.data.append([i, point, f'{pointSet[point]["state"][0]:6.2f} K'
                                            +f'{pointSet[point]["state"][1]:6.2f} atm'
                                 ])
        self.sgw['-dataList-'].update(self.data)
    def updateDetails(self):
        elementDetails = ''.join([f'{self.elements[i]} concentration: {self.points[self.setIndex][self.point]["state"][i+2]:6.2f}\n' for i in range(len(self.elements))])
        valValues = []
        try:
            dictTools.getParallelDictValues(self.points[self.setIndex][self.point]['values'],self.points[self.setIndex][self.point]['values'],valValues)
            actStr = ''
            valKeys = []
            dictTools.getDictKeyString(self.points[self.setIndex][self.point]['values'],actStr,valKeys)
            validationDetails = '\n'.join([f'{valKeys[i]}: {str(valValues[i])}' for i in range(len(valValues))])
        except KeyError:
            validationDetails = ''
        details = (
                    'Calculated State:\n'
                  +f'Temperature: {self.points[self.setIndex][self.point]["state"][0]:6.2f} K\n'
                  +f'Pressure: {self.points[self.setIndex][self.point]["state"][1]:6.2f} atm\n'
                  +elementDetails
                  +'\nValidation Data:\n'
                  +validationDetails
                 )
        self.sgw['-details-'].update(details)

class DatabaseWindow:
    def __init__(self,parent):
        windowList.append(self)
        self.parent = parent
        file_list_column = [
            [
                sg.Text("Database Folder"),
                sg.In(size=(25, 1), enable_events=True, key="-FOLDER-"),
                sg.FolderBrowse(),
            ],
            [
                sg.Listbox(
                    values=[], enable_events=True, size=(40, 20), key="-FILE LIST-"
                )
            ],
            [
                sg.Button('Accept', size = buttonSize)
            ]
        ]
        self.folder = os.getcwd()
        try:
            file_list = os.listdir(self.folder)
        except:
            file_list = []
        fnames = [
            f
            for f in file_list
            if os.path.isfile(os.path.join(self.folder, f))
            and f.lower().endswith((".dat", ".DAT"))
        ]
        fnames = sorted(fnames, key=str.lower)
        self.sgw = sg.Window('Thermochimica database selection', file_list_column, location = [0,0], finalize=True)
        self.sgw["-FILE LIST-"].update(fnames)
        self.children = []
    def close(self):
        for child in self.children:
            child.close()
        self.sgw.close()
        if self in windowList:
            windowList.remove(self)
    def read(self):
        event, values = self.sgw.read(timeout=timeout)
        if event == sg.WIN_CLOSED or event == 'Exit':
            self.close()
        elif event == "-FOLDER-":
            self.folder = values["-FOLDER-"]
            try:
                file_list = os.listdir(self.folder)
            except:
                file_list = []

            fnames = [
                f
                for f in file_list
                if os.path.isfile(os.path.join(self.folder, f))
                and f.lower().endswith((".dat", ".DAT"))
            ]
            fnames = sorted(fnames, key=str.lower)
            self.sgw["-FILE LIST-"].update(fnames)
        elif event == "-FILE LIST-":  # A file was chosen from the listbox
            try:
                self.parent.datafile = os.path.join(self.folder, values["-FILE LIST-"][0])
            except:
                return
        elif event == 'Accept':
            self.parent.parseDatabase()
            self.close()

windowList = []
def main():
    ThermochimicaOptima()
    while len(windowList) > 0:
        for window in windowList:
            window.read()

if __name__ == "__main__":
    main()
