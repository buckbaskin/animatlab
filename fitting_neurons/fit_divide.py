import numpy as np

def actual(X):
    return np.clip((1.0 / X) / 100.0, 0, 1)

X = np.linspace(0.01, 1.0, 100)
Y1 = actual(X)

def neuron(X, g=0.859, E=-40):
    '''
    All around good fit:
    g=0.216, E=-100
    '''
    X = 20 * X
    R = 20
    top = (g / R) * X * E
    bottom = 1 + (g / R) * X
    return 1 + np.divide(top, bottom) / 40

def error(X, g, E):
    return neuron(X, g, E) - actual(X)

from matplotlib import pyplot as plt

plt.plot(X, Y1)
Y2 = neuron(X)
plt.plot(X, Y2)

def seek_g_E(E_list=None):
    if E_list is None:
        E_list = [100, 50, 20]
    for E in E_list:
        max_G = 40
        min_G = 0.01
        for i in range(30):
            mid_G = (max_G + min_G) / 2.0
            y_goal = actual(1)
            y_max = neuron(1, g=max_G, E=E)
            y_min = neuron(1, g=min_G, E=E)
            y_mid = neuron(1, g=mid_G, E=E)
            if y_max < y_goal:
                yield max_G, E
                break
            elif y_min > y_goal:
                yield min_G, E
                break
            elif y_mid == y_goal:
                yield mid_G, E
                break
            elif y_mid < y_goal:
                max_G = max_G
                min_G = mid_G
            else: # y_mid > y_goal
                max_G = mid_G
                min_G = min_G
        else:
            yield mid_G, E

E_list = list(range(133, 136))
scores = []
for G, E in seek_g_E(E_list=E_list):
    score = abs(actual(0.5) - neuron(0.5, g=G, E=E))
    print('E %.1f G %.3f Score: %.3f' % (E, G, score,))
    scores.append(score)
    
import scipy
from scipy.optimize import curve_fit

popt, _ = curve_fit(neuron, X, actual(X), p0=[0.25])
print(popt)

# plt.plot(E_list, scores)
plt.show()
