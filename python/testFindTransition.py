import findTransition

kaye = findTransition.transitionFinder('Kaye_NobleMetals.dat')
kaye.transitionSolutionPhases = ['FCCN','BCCN','HCPN']
kaye.targetTemperature = 1600
kaye.targetComposition = dict([('Pd',0.3),('Mo',0.7)])
kaye.thermochimica_path = '../thermochimica'
kaye.findTransition()
print(f'Temperature: {bestBeta[0]}')
i = 0
for element in self.targetComposition.keys():
    i += 1
    print(f'{element}: {bestBeta[i]*totalMass}')
