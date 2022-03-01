import os
import re
import PySimpleGUI as sg
import shutil
import subprocess

timeout = 50
inputSize = 16

class TagWindow:
    def __init__(self,datafile,windowList):
        self.windowList = windowList
        self.windowList.append(self)
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
        buttonLayout = [[sg.Button('Accept'),sg.Button('Cancel')]]
        self.sgw = sg.Window('Coefficients', [headingLayout,tagsLayout,buttonLayout], location = [400,0], finalize=True)
        self.children = []
    def close(self):
        for child in self.children:
            child.close()
        self.sgw.close()
        if self in self.windowList:
            self.windowList.remove(self)
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
