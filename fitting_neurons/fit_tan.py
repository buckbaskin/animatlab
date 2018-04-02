import numpy as np

def actual(X):
    return np.arctan(X * 4) / np.arctan(4)

X = np.linspace(0, 1, 10)
Y1 = actual(X)

def neuron(X, g=0.55, E=134):
    X = 20 * X
    R = 20
    top = (g / R) * X * E
    bottom = 1 + (g / R) * X
    return np.divide(top, bottom) / 20

from matplotlib import pyplot as plt

plt.plot(X, Y1)

E = 40
for g in [0.125, 0.25, 0.5]:
    Y2 = neuron(X, g=g, E=E)
    plt.plot(X, Y2)

plt.show()
