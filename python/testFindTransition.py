import findTransition

kaye = findTransition.transitionFinder('Kaye_NobleMetals.dat')
kaye.transitionSolutionPhases = ['FCCN','BCCN','HCPN']
kaye.targetTemperature = 1600
kaye.targetComposition = dict([('Pd',0.3),('Mo',0.7)])
kaye.thermochimica_path = '../thermochimica'
kaye.tempRange = 50
kaye.findTransition()
print(f'Temperature: {kaye.bestBeta[0]}')
i = 0
for element in kaye.targetComposition.keys():
    i += 1
    print(f'{element}: {kaye.bestBeta[i]*kaye.totalMass}')
