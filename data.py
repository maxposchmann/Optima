import os
import re
import PySimpleGUI as sg

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
    def __init__(self,tags):
        windowList.append(self)
        tagMaxLength = 3
        for tag in tags:
            tagMaxLength = max(tagMaxLength,len(tag))
        headingLayout = [[
                          sg.Text('Tag',   size = [tagMaxLength,1],justification='left'),
                          sg.Text('Initial Value 1',size = [inputSize,1],justification='center'),
                          sg.Text('Initial Value 2',size = [inputSize,1],justification='center')
                        ]]
        tagsLayout = []
        for tag in tags:
            tagsLayout.append([[
                                sg.Text(tag,size = [tagMaxLength,1],justification='left'),
                                sg.Input(key = f'{tag}-in1',size = [inputSize,1]),
                                sg.Input(key = f'{tag}-in2',size = [inputSize,1])
                             ]])
        self.sgw = sg.Window('Coefficients', [headingLayout,tagsLayout], location = [400,0], finalize=True)
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

tags = []
datafile = 'kayetest.dat'
with open(datafile) as f:
    data = f.readlines()
    for line in data:
        tags.extend(re.findall('<([^>]*)>', line))

if tags == []:
    sys.exit('No tags found')

windowList = []
TagWindow(tags)
while len(windowList) > 0:
    for window in windowList:
        window.read()
