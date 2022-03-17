import os
import re
import PySimpleGUI as sg
import shutil
import subprocess

timeout = 50
inputSize = 16

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

class TagWindow:
    def __init__(self,datafile,windowList):
        self.windowList = windowList
        self.datafile = datafile
        tags = []
        with open(datafile) as f:
            data = f.readlines()
            for line in data:
                tags.extend(re.findall('<([^>]*)>', line))
        if tags == []:
            print('No tags found')
            self.close()
        tags = list(dict.fromkeys(tags))
        self.tags = dict([(tags[i], dict([('initial',[0,0]),('optimize',True),('scale',1.0)])) for i in range(len(tags))])
        self.open()
        self.children = []
    def close(self):
        for child in self.children:
            child.close()
        self.sgw.close()
        if self in self.windowList:
            self.windowList.remove(self)
    def open(self):
        self.windowList.append(self)
        dataColumn = [
            [sg.Text('Tags')],
            [sg.Listbox(values=list(self.tags.keys()), enable_events=True, size=(30, 20), key='-tagList-')]
        ]
        outputColumn = [
            [sg.Text('Tag Details')],
            [sg.Multiline(key='-details-', size=(60,5))],
            [sg.Text('Edit Values', font='underline')],
            [sg.Text('Values 1 and 2 are initial guesses for Broyden, and low/high bounds for Bayesian')],
            [sg.Text('Value 1:'), sg.Input(key=f'-in1-',size=(inputSize,1))],
            [sg.Text('Value 2:'), sg.Input(key=f'-in2-',size=(inputSize,1))],
            [sg.Text('Should this tag be optimized or set to constant Value 1?')],
            [sg.Radio('Optimize', f'-set-', key = f'-opt-', default = True,  pad = (20,0), enable_events = True),
             sg.Radio('Constant', f'-set-', key = f'-con-', default = False, pad = (20,0), enable_events = True)],
            [sg.Text('Optional scaling factor for tag, enter approximate order of magnitude if known')],
            [sg.Text('Scale:'), sg.Input(key='-scale-',size=(inputSize,1))],
            [sg.Button('Update'), sg.Button('Reset to Defaults')]
            ]
        self.sgw = sg.Window('Tag inspection',
            [[sg.Pane([
                sg.Column(dataColumn, element_justification='l', expand_x=True, expand_y=True),
                sg.Column(outputColumn, element_justification='c', expand_x=True, expand_y=True)
            ], orientation='h', k='-PANE-')]],
            location = [400,0], finalize=True)
    def read(self):
        event, values = self.sgw.read(timeout=timeout)
        if event == sg.WIN_CLOSED or event == 'Cancel':
            self.close()
        elif event in ['Update',f'-opt-',f'-con-']:
            try:
                if not values[f'-in1-'] == '':
                    self.tags[self.tag]['initial'][0] = float(values[f'-in1-'])
                if not values[f'-in2-'] == '':
                    self.tags[self.tag]['initial'][1] = float(values[f'-in2-'])
                self.tags[self.tag]['optimize'] = values[f'-opt-']
                if not values[f'-scale-'] == '':
                    self.tags[self.tag]['scale'] = float(values[f'-scale-'])
                self.updateDetails()
            except ValueError:
                print(f'Invalid initial value or scale')
                return
        elif event == '-tagList-':
            self.tag = values['-tagList-'][0]
            self.updateDetails()
        elif event =='Reset to Defaults':
            self.tags[self.tag]['initial'] = [0,0]
            self.tags[self.tag]['optimize'] = True
            self.tags[self.tag]['scale'] = 1.0
            self.updateDetails()
    def updateDetails(self):
        details = (
                   f'Value 1: {self.tags[self.tag]["initial"][0]:6.2f}\n'
                  +f'Value 2: {self.tags[self.tag]["initial"][1]:6.2f}\n'
                  +f'Scale: {self.tags[self.tag]["scale"]}'
                 )
        self.sgw['-details-'].update(details)
        self.sgw['-opt-'].update(self.tags[self.tag]['optimize'])
        self.sgw['-con-'].update(not self.tags[self.tag]['optimize'])

class PointValidationWindow:
    def __init__(self,npoints,elements,points,windowList):
        self.windowList = windowList
        self.windowList.append(self)
        self.npoints = npoints
        self.elements = elements
        # Don't edit self.points along the way, just append to it at the end!
        # This array will have all the previously-accumulated points in it.
        # The plan is to allow multiple of these windows simultaneously.
        self.points = points

        self.open()
        self.children = []
    def close(self):
        for child in self.children:
            child.close()
        self.sgw.close()
        if self in self.windowList:
            self.windowList.remove(self)
    def open(self):
        elementHeader = [sg.Text(f'{element} Concentration',size=inputSize) for element in self.elements]
        headerLayout = [[sg.Text('Temperature',size=inputSize),sg.Text('Pressure',size=inputSize)] + elementHeader]
        rowLayout = [[sg.Input(key=f'-temp{i}-',size=inputSize),sg.Input(key=f'-pres{i}-',size=inputSize)] + [sg.Input(key = f'-{element}{i}-',size=inputSize) for element in self.elements] for i in range(self.npoints)]
        buttonLayout = [[sg.Button('Accept'),sg.Button('Cancel')]]
        self.sgw = sg.Window('Validation Data', [headerLayout,rowLayout,buttonLayout], location = [800,0], finalize=True)
    def read(self):
        event, values = self.sgw.read(timeout=timeout)
        if event == sg.WIN_CLOSED or event == 'Cancel':
            self.close()
        if event == 'Accept':
            if len(self.points) == 0:
                startIndex = 0
            else:
                startIndex = int(list(self.points.keys())[-1]) + 1
            # use newpoints to accumulate points entered here
            newpoints = dict([])
            temp, status = self.validEntry(values[f'-temp{0}-'])
            if not (status == 0 and temp >= 300):
                print('Invalid temperature in line 0')
                return
            pres, status = self.validEntry(values[f'-pres{0}-'])
            if not (status == 0 and pres > 0):
                print('Invalid pressure in line 0')
                return
            concentrations = []
            for element in self.elements:
                conc, status = self.validEntry(values[f'-{element}{0}-'])
                concentrations.append(conc)
            if not max(concentrations) > 0:
                print('Need at least one element present')
                return
            newpoints[startIndex] = dict([('state',[temp,pres]+concentrations)])
            for i in range(1,self.npoints):
                lastTemp = temp
                lastPres = pres
                lastConcentrations = concentrations
                temp, status = self.validEntry(values[f'-temp{i}-'])
                if status == 1:
                    temp = lastTemp
                elif not (status >= 0 and temp >= 300):
                    print(f'Invalid temperature in line {i+1}')
                    return
                pres, status = self.validEntry(values[f'-pres{i}-'])
                if status == 1:
                    pres = lastPres
                elif not (status >= 0 and pres > 0):
                    print(f'Invalid pressure in line {i+1}')
                    return
                concentrations = []
                for element in self.elements:
                    conc, status = self.validEntry(values[f'-{element}{i}-'])
                    if status == -1:
                        return
                    elif status == 1:
                        conc = lastConcentrations[self.elements.index(element)]
                    concentrations.append(conc)
                if not max(concentrations) > 0:
                    print('Need at least one element present')
                    return
                newpoints[startIndex + i] = dict([('state',[temp,pres]+concentrations)])
            # Make window to enter reference data
            headerLayout = [[sg.Text('Gibbs Energy')]]
            rowLayout = [[sg.Input(key=f'-gibbs{i}-',size=inputSize)] for i in range(self.npoints)]
            buttonLayout = [[sg.Button('Accept'),sg.Button('Cancel')]]
            referenceWindow = sg.Window('Reference Data', [headerLayout,rowLayout,buttonLayout], location = [800,0], finalize=True)
            while True:
                event, values = referenceWindow.read(timeout=timeout)
                if event == sg.WIN_CLOSED or event == 'Cancel':
                    break
                if event == 'Accept':
                    valid = True
                    for i in range(self.npoints):
                        try:
                            gibbs = float(values[f'-gibbs{i}-'])
                            newpoints[startIndex + i]['values'] = dict([('integral Gibbs energy',gibbs)])
                        except ValueError:
                            print(f'Invalid entry {values[f"-gibbs{i}-"]}')
                            valid = False
                    if valid:
                        referenceWindow.close()
                        self.points.update(newpoints)
                        self.close()
    def validEntry(self,value):
        if value == '':
            outValue = 0
            status = 1
        else:
            try:
                outValue = float(value)
                if outValue >= 0:
                    status = 0
                else:
                    raise ValueError
            except ValueError:
                print(f'Invalid entry {value}')
                outValue = 0
                status = -1
        return outValue, status
