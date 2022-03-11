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
        self.valid = False
        tags = []
        with open(datafile) as f:
            data = f.readlines()
            for line in data:
                tags.extend(re.findall('<([^>]*)>', line))
        if tags == []:
            print('No tags found')
            self.close()
        tags = list(dict.fromkeys(tags))
        self.tags = dict([(tags[i], [[0,0],True]) for i in range(len(tags))])
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
        tagMaxLength = 3
        for tag in self.tags:
            tagMaxLength = max(tagMaxLength,len(tag))
        headingLayout = [[
                          sg.Text('Tag',   size = [tagMaxLength,1],justification='left'),
                          sg.Text('Initial Value 1',size = [inputSize,1],justification='center'),
                          sg.Text('Initial Value 2',size = [inputSize,1],justification='center'),
                          sg.Text('Optimize',justification='center'),
                          sg.Text('Constant',justification='center')
                        ]]
        tagsLayout = []
        for tag in self.tags:
            tagsLayout.append([[
                                sg.Text(tag,size = [tagMaxLength,1],justification='left'),
                                sg.Input(key = f'{tag}-in1',size = [inputSize,1]),
                                sg.Input(key = f'{tag}-in2',size = [inputSize,1]),
                                sg.Radio('', f'{tag}-set', key = f'{tag}-opt', default = True, pad = (20,0)),
                                sg.Radio('', f'{tag}-set', key = f'{tag}-con', default = False, pad = (20,0))
                             ]])
        buttonLayout = [[sg.Button('Accept'),sg.Button('Cancel')]]
        self.sgw = sg.Window('Coefficients', [headingLayout,tagsLayout,buttonLayout], location = [400,0], finalize=True)
    def read(self):
        event, values = self.sgw.read(timeout=timeout)
        if event == sg.WIN_CLOSED or event == 'Cancel':
            self.close()
        if event == 'Accept':
            for tag in self.tags.keys():
                try:
                    if values[f'{tag}-in1'] == '':
                        v1 = 0
                    else:
                        v1 = float(values[f'{tag}-in1'])
                    if values[f'{tag}-in2'] == '':
                        v2 = 0
                    else:
                        v2 = float(values[f'{tag}-in2'])
                    self.tags[tag] = [[v1,v2],values[f'{tag}-opt']]
                except ValueError:
                    print(f'Invalid initial value for {tag}')
                    return
            self.valid = True
            self.close()

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
                            newpoints[startIndex + i]['gibbs'] = gibbs
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
