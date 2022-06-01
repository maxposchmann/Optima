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

def getPointValidationValues(updateInputFunction, validation, tags, beta, thermochimica_path):
    # Call update function
    updateInputFunction(tags, beta)

    # Run input files and store data
    f = []
    for n_val in range(len(validation)):
        subprocess.run([thermochimica_path + '/bin/RunCalculationList',f'validationPoints-{n_val}.ti'])

        jsonFile = open(thermochimica_path + '/thermoout.json',)
        try:
            data = json.load(jsonFile)
            jsonFile.close()
        except:
            jsonFile.close()
            print('Data load failed')
            raise optima.OptimaException

        validationKeys = list(validation[n_val].keys())
        for i in range(len(validationKeys)):
            if len(data[str(i+1)].keys()) == 0:
                print('Thermochimica calculation failed to converge')
                raise optima.OptimaException
            # Get all comparison values per calculation
            calcValues = []
            dictTools.getParallelDictValues(validation[n_val][validationKeys[i]]['values'],data[str(i+1)],calcValues)
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
        self.thermochimica_path = 'thermochimica'
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
        elif event == 'Clear Validation Data':
            self.validationPoints = dict([])
            print('Validation data cleared')
        elif event == 'Edit Validation Data':
            editDataWindow = EditDataWindow(self.validationPoints,self.elements)
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
            return getPointValidationValues(updateDat, self.validationPoints, tags, beta, self.thermochimica_path)
        # Get validation value/weight pairs
        validationPairs = []
        for points in self.validationPoints:
            validationKeys = list(points.keys())
            for i in range(len(points)):
                calcValues = []
                dictTools.getParallelDictValues(points[validationKeys[i]]['values'],
                                                points[validationKeys[i]]['values'],
                                                calcValues)
                validationPairs.extend(calcValues)
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
        self.method(y,
                    intertags,
                    getValues,
                    self.maxIts,
                    self.tol,
                    weight = weight,
                    scale = scale,
                    **self.extraParams)
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
                    rekeyedPoints[startIndex + i] = newPoints.pop(point)
                    i += 1
                self.validationPoints.append(rekeyedPoints)
                print(f'{len(rekeyedPoints)} validation points loaded')
            else:
                print('No entries in validation JSON')
    def writeFile(self):
        for n_val in range(len(self.validationPoints)):
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

        # Automatically open a window for initial conditions
        try:
            # Close old tagWindow if exists
            self.tagWindow.close()
        except AttributeError:
            pass
        self.tagWindow = optimaData.TagWindow(self.datafile,windowList)
        self.children.append(self.tagWindow)

class EditDataWindow:
    def __init__(self,points,elements):
        self.points = points
        self.elements = elements
        windowList.append(self)
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
            [sg.Text('Pressure'), sg.Input(key='-pres-',size=(inputSize,1))]]
        outputColumn.extend([[sg.Text(f'{self.elements[i]} concentration'),sg.Input(key=f'-{self.elements[i]}-',size=(inputSize,1))] for i in range(len(self.elements))])
        outputColumn.extend([
            [sg.Text('Gibbs Energy'), sg.Input(key='-gibbs-',size=(inputSize,1))],
            [sg.Button('Edit Point', disabled = True), sg.Button('Delete Point', disabled = True)],
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
    def read(self):
        event, values = self.sgw.read(timeout=timeout)
        if event == sg.WIN_CLOSED or event == 'Exit':
            self.close()
        elif event == '-dataList-':
            self.point = values['-dataList-'][0][0]
            elementDetails = ''.join([f'{self.elements[i]} concentration: {self.points[self.point]["state"][i+2]:6.2f}\n' for i in range(len(self.elements))])
            valValues = []
            dictTools.getParallelDictValues(self.points[self.point]['values'],self.points[self.point]['values'],valValues)
            actStr = ''
            valKeys = []
            dictTools.getDictKeyString(self.points[self.point]['values'],actStr,valKeys)
            validationDetails = '\n'.join([f'{valKeys[i]}: {str(valValues[i])}' for i in range(len(valValues))])
            details = (
                        'Calculated State:\n'
                      +f'Temperature: {self.points[self.point]["state"][0]:6.2f} K\n'
                      +f'Pressure: {self.points[self.point]["state"][1]:6.2f} atm\n'
                      +elementDetails
                      +'\nValidation Data:\n'
                      +validationDetails
                     )
            self.sgw['-details-'].update(details)
            self.sgw.Element('Edit Point').Update(disabled = False)
            self.sgw.Element('Delete Point').Update(disabled = False)
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
            del self.points[self.point]
            self.getData()
        elif event == 'Edit Point':
            try:
                self.points[self.point]['state'][0] = float(values['-temp-'])
            except ValueError:
                pass
            try:
                self.points[self.point]['state'][1] = float(values['-pres-'])
            except ValueError:
                pass
            for i in range(len(self.elements)):
                try:
                    self.points[self.point]['state'][i+2] = float(values[f'-{self.elements[i]}-'])
                except ValueError:
                    pass
            try:
                self.points[self.point]["values"]['integral Gibbs energy'] = float(values['-gibbs-'])
            except ValueError:
                pass
            self.getData()
    def getData(self):
        self.data = []
        for point in self.points.keys():
            if self.tlo <= self.points[point]["state"][0] and self.thi >= self.points[point]["state"][0]:
                self.data.append([point, f'{self.points[point]["state"][0]:6.2f} K'
                                        +f'{self.points[point]["state"][1]:6.2f} atm'
                                 ])
        self.sgw['-dataList-'].update(self.data)

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
