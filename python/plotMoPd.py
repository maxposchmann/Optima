import matplotlib.pyplot as plt
import json
import numpy as np

itmed = dict([])
itstd = dict([])
nomed = dict([])
nostd = dict([])
for method in ['broyden','ucb']:
    itmed[method] = []
    itstd[method] = []
    nomed[method] = []
    nostd[method] = []
    for n in range(1,17):
        # Load result
        resultFile = f'testResults/{method}-{str(n)}vars-100tests.json'
        jsonFile = open(resultFile,)
        result = json.load(jsonFile)
        jsonFile.close()

        iterations = [result[run]['iterations'] for run in result]
        norms = [result[run]['norm'] for run in result]
        itmed[method].append(np.median(iterations))
        itstd[method].append(np.std(iterations))
        nomed[method].append(np.median(norms))
        nostd[method].append(np.std(norms))

x = [i+1 for i in range(16)]
fig = plt.figure()
ax = fig.add_axes([0.1, 0.1, 0.775, 0.85])
lns  = ax.plot(x, itmed['broyden'], 'k.-', label = 'Broyden # iterations')
lns += ax.plot(x, itmed['ucb'], 'ks--', label = 'UCB # iterations')
ax.set_xlabel('Number of reoptimized parameters')
ax.set_ylabel('Mean number of iterations')

ax2 = ax.twinx()
lns += ax2.plot(x, nomed['broyden'], 'b.-', label = 'Broyden residual norm')
lns += ax2.plot(x, nomed['ucb'], 'bs--', label = 'UCB residual norm')
ax2.set_yscale('log')
ax2.set_ylabel('Mean residual norm')
ax2.spines['right'].set_color('b')
ax2.yaxis.label.set_color('b')
ax2.tick_params(axis='y', colors='b')

labs = [l.get_label() for l in lns]
ax.legend(lns, labs, loc=(0.5,0.5))
plt.show()
