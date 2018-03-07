'''
======================
Plot Level curve (Desired Torque)
======================
Based on matplotlib 3D surface (color map) demo
https://matplotlib.org/mpl_toolkits/mplot3d/tutorial.html

And level curve plotting
https://matplotlib.org/gallery/mplot3d/contour3d.html
'''
from math import pi

from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter
import numpy as np


fig = plt.figure()
ax = fig.gca(projection='3d')

### Search Parameters ###

max_torque = 2
min_torque = -2
max_theta = pi / 2
min_theta = -pi / 2
resolution = 0.1

### Model Parameters ###

a0 = 254.3 # kpa
a1 = 192.0 # kpa
a2 = 2.0625
a3 = -0.461
a4 = -0.331
a5 = 1.230
a6 = 15.6 # kpa

### Mutual Actuator Parameters ### 

l_rest = .189 # m
l_620 = round(-((.16 * l_rest) - l_rest), 3)
k_max = round((l_rest - l_620) / (l_rest), 3)

### Specific Actuator Parameters ###

d_l = 1
alpha_l = 0
beta_l = 0
l0_l = 1
l1_l = 1

d_r = 1
alpha_r = 0
beta_r = 0
l0_r = 1
l1_r = 1

# Make data.
T = np.arange(min_torque, max_torque, resolution)
A = np.arange(min_theta, max_theta, resolution)
T, A = np.meshgrid(T, A)

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

L_angle_l = l0_l + l1_l * np.cos(alpha_l + A)
F_l = T / (d_l * np.cos(beta_l + A))
K_l = (l_rest - L_angle_l) / l_rest

P_l = a0 + a1 * np.tan(a2 * (K_l / (a4 * F_l + k_max)) + a3) + a5 * F_l # kpa

# Plot the surface.
surf = ax.plot_surface(X, Y, Z, cmap=cm.coolwarm,
                       linewidth=0, antialiased=False)

# Add a color bar which maps values to colors.
fig.colorbar(surf, shrink=0.5, aspect=6)

plt.show()
