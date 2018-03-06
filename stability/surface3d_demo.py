'''
======================
Plot Level curve (Desired Torque)
======================
Based on matplotlib 3D surface (color map) demo
'''
from math import pi

from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter
import numpy as np


fig = plt.figure()
ax = fig.gca(projection='3d')

max_pressure = 5
min_pressure = -5
resolution = 0.1

# Make data.
X = np.arange(min_pressure, max_pressure, resolution)
Y = np.arange(min_pressure, max_pressure, resolution)
X, Y = np.meshgrid(X, Y)

### calculate the torque here
# for any two pressures w/in reason
# Start at angle 0, calculate numerical derivative of angle/torque
# Look at sum of positive, negative actuator
# If the positive actuator has a greater K value, increment angle smaller
# If the negative actuator has a greater K value, increment angle larger
# This should iterate the actuators to a balanced position
# Ex. positive actuator K = 2
# Ex. negative actuator < 2

# that's the hard way to do it, and might get lots of bad pressure values
# Instead, iterate through a grid of net torques and angles at a given stiffness
# for each actuator, based on torque and angle, calculate the pressure value for
# the mirroed actuators. Write down the two pressures in Xp, Yp, and two values
# Z_torque, Z_angle. Plot XYZ surface for both at different stiffness

R = np.sqrt(X**2 + Y**2)
Z = np.sin(R)

# Plot the surface.
surf = ax.plot_surface(X, Y, Z, cmap=cm.coolwarm,
                       linewidth=0, antialiased=False)

# Add a color bar which maps values to colors.
fig.colorbar(surf, shrink=0.5, aspect=6)

plt.show()
