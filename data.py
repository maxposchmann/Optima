import os
import re
import PySimpleGUI as sg
import shutil
import subprocess

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

class TagWindow:
    def __init__(self,datafile):
        windowList.append(self)
        self.datafile = datafile
        self.tags = []
        self.initialValues = []

        with open(datafile) as f:
            data = f.readlines()
            for line in data:
                self.tags.extend(re.findall('<([^>]*)>', line))

        if self.tags == []:
            print('No tags found')
            self.close()

        self.tags = list(dict.fromkeys(self.tags))

        tagMaxLength = 3
        for tag in self.tags:
            tagMaxLength = max(tagMaxLength,len(tag))
        headingLayout = [[
                          sg.Text('Tag',   size = [tagMaxLength,1],justification='left'),
                          sg.Text('Initial Value 1',size = [inputSize,1],justification='center'),
                          sg.Text('Initial Value 2',size = [inputSize,1],justification='center')
                        ]]
        tagsLayout = []
        for tag in self.tags:
            tagsLayout.append([[
                                sg.Text(tag,size = [tagMaxLength,1],justification='left'),
                                sg.Input(key = f'{tag}-in1',size = [inputSize,1]),
                                sg.Input(key = f'{tag}-in2',size = [inputSize,1])
                             ]])
        buttonLayout = [[sg.Button('Make datafile')]]
        self.sgw = sg.Window('Coefficients', [headingLayout,tagsLayout,buttonLayout], location = [400,0], finalize=True)
        self.children = []
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
        if event == 'Accept':
            self.initialValues = []
            for tag in self.tags:
                key = f'{tag}-in1'
                self.initialValues.append(values[key])
            self.close()
