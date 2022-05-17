import matplotlib.pyplot as plt
import json
import numpy as np

broyden  = [ 8.99, 16.50, 63.98, 117.68, 292.35, 237.29, 276.51, 543.88, 678.14, 1038.67]
bayes    = [43.37, 54.92, 70.60,  95.09, 139.22, 146.31, 189.23, 210.46, 446.84,  401.88]
combined = [25.20, 28.31, 28.15,  27.49,  31.65,  34.23,  29.03,  37.53,  37.01,   39.98]

x = [i+1 for i in range(10)]
fig = plt.figure()
ax = fig.add_axes([0.125, 0.1, 0.85, 0.85])
lns  = ax.plot(x, broyden, 'o-', label = 'Broyden')
lns += ax.plot(x, bayes, 's--', label = 'UCB')
lns += ax.plot(x, combined, '^-.', label = 'Combined search')
ax.set_xlabel(r'$e_{max}$')
ax.set_ylabel('Mean number of iterations')
ax.set_xlim([0.9,10.1])
ax.set_ylim([0,1100])
ax.set_xticks([i for i in range(1,11)])

labs = [l.get_label() for l in lns]
ax.legend(lns, labs, loc=0)
plt.show()
