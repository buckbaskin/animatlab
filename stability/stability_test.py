import numpy as np

from numpy import linalg as LA

K_p = 2
K_v = .01
A = np.matrix([[0, 1], [-K_p, -K_v]])
print(A)

w, v = LA.eig(A)

print('eigen values')
print(w)

print('eigen vectors')
print(v)

system = np.matrix([3.0,2.0]).T
states = []

steps = 100
ax_title = 'Linear System, '
if np.any(np.real(w) >= 0):
    ax_title += 'Unstable'
else:
    ax_title += 'Stable'

if np.any(np.imag(w) != 0):
    ax_title += ', Oscillating (Underdamped)'
else:
    ax_title += ', Damped'

for i in range(steps):
    system_delta = 0.1 * A * system
    system += system_delta
    print(i, system)
    states.append(system.copy())

import matplotlib
matplotlib.use('TKAgg')
from matplotlib import pyplot as plt

states = np.array(states).reshape((steps,2))
X = states[:,0]
y = states[:,1]

fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)
ax.set_title(ax_title)
ax.spines['left'].set_position('zero')
ax.spines['left'].set_smart_bounds(True)
ax.spines['bottom'].set_position('zero')
ax.spines['bottom'].set_smart_bounds(True)
ax.spines['right'].set_color('none')
ax.spines['top'].set_color('none')

plt.plot(X, y)
plt.plot(X[:1], y[:1], 'ro')
plt.show()

