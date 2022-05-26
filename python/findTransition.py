import optima
import thermoOptima
import math
import dictTools

class transitionFinder:
    def __init__(self, datafile,):
        self.datafile = datafile
        self.parseDatabase()

        # Default parameters
        self.tol = 1e-10
        self.maxIts = 30
        self.tunit = 'K'
        self.punit = 'atm'
        self.munit = 'moles'

        self.validationPoints = dict([('0', dict([('values', dict([('solution phases',dict([])),('pure condensed phases',dict([]))]))]))])

        # Phases involved in transition
        self.transitionSolutionPhases = []
        self.transitionStoichiometricPhases = []

        self.targetTemperature = []
        self.targetComposition = []

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
                index = thermoOptima.atomic_number_map.index(el)+1 # get element indices in PT (i.e. # of protons)
            except ValueError:
                if len(el) > 0:
                    if el[0] != 'e':
                        print(el+' not in list') # if the name is bogus (or e(phase)), discard
                self.elements = list(filter(lambda a: a != el, self.elements))
    def updateInputFile(self, tags, beta):
        with open('validationPoints.ti', 'w') as inputFile:
            inputFile.write('! Optima-generated input file for validation points\n')
            inputFile.write(f'data file         = {self.datafile}\n')
            inputFile.write(f'temperature unit  = {self.tunit}\n')
            inputFile.write(f'pressure unit     = {self.punit}\n')
            inputFile.write(f'mass unit         = {self.munit}\n')
            inputFile.write(f'nEl               = {len(self.elements)} \n')
            inputFile.write(f'iEl               = {" ".join([str(thermoOptima.atomic_number_map.index(element)+1) for element in self.elements])}\n')
            inputFile.write(f'nCalc             = {len(self.validationPoints)}\n')
            compositions = []
            for element in self.elements:
                if element in self.targetComposition.keys():
                    compositions.append(str(beta[1 + list(self.targetComposition.keys()).index(element)]))
                else:
                    compositions.append('0')
            for point in self.validationPoints.keys():
                inputFile.write(f'{beta[0]} 1 {" ".join(compositions)}\n')
    def findTransition(self):
        # Setup tags
        self.tagNames = ['temperature']
        self.tagNames.extend(self.targetComposition.keys())
        self.tags = dict([(self.tagNames[i], [0,0]) for i in range(len(self.tagNames))])
        self.tags['temperature'][0] = self.targetTemperature
        self.tags['temperature'][1] = self.targetTemperature
        for element in self.targetComposition.keys():
            self.tags[element][0] = self.targetComposition[element]
            self.tags[element][1] = self.targetComposition[element]

        # Setup validation
        for phase in self.transitionSolutionPhases:
            self.validationPoints['0']['values']['solution phases'][phase] = dict([('driving force', 0)])

        for phase in self.transitionStoichiometricPhases:
            self.validationPoints['0']['values']['pure condensed phases'][phase] = dict([('driving force', 0)])

        # Use currying to package validationPoints with getPointValidationValues
        def getValues(tags, beta):
            return thermoOptima.getPointValidationValues(self.updateInputFile, self.validationPoints, tags, beta)

        # Get validation value/weight pairs
        validationPairs = []
        for key in self.validationPoints.keys():
            calcValues = []
            dictTools.getParallelDictValues(self.validationPoints[key]['values'],
                                            self.validationPoints[key]['values'],
                                            calcValues)
            validationPairs.extend(calcValues)

        # Call Optima
        optima.LevenbergMarquardtBroyden(validationPairs,
                                         self.tags,
                                         getValues,
                                         self.maxIts,
                                         self.tol
                                        )

kaye = transitionFinder('Kaye_NobleMetals.dat')
kaye.transitionSolutionPhases = ['FCCN','BCCN','HCPN']
kaye.targetTemperature = 1600
kaye.targetComposition = dict([('Pd',0.3),('Mo',0.7)])
kaye.findTransition()
