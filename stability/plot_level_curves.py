'''
======================
Plot Level curve (Desired Torque)
======================
Based on matplotlib 3D surface (color map) demo
https://matplotlib.org/mpl_toolkits/mplot3d/tutorial.html

And level curve plotting
https://matplotlib.org/gallery/mplot3d/contour3d.html
'''
from math import atan, floor, pi, sqrt

from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter
import numpy as np


### Search Parameters ###

max_torque = 2
min_torque = -2
max_theta = pi / 4
min_theta = -pi / 4
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
l_max = l_rest
l_min = l_620

d = 0.005 # m
offset = 0.015 # m
l1 = round(sqrt(d**2 + offset**2), 3)
l0 = floor((l_max - l1) * 1000.0) / 1000.0

### Specific Actuator Parameters ###
# Actuator L is the negative actuator, Actuator R is the positive actuator
# /////////////
#    l  |   r
#    l  |   r
#     l |  r
#     l(o) r
#      x>\<x
#       . \
#       .  \
#       .   \

alpha_l = atan(offset / d) # radians
beta_l = -pi / 2 # radians, TODO(buckbaskin): assumes that muscle mounted d meters off mount

alpha_r = -atan(offset / d) # radians
beta_r = pi / 2 # radians, TODO(buckbaskin): assumes that muscle mounted d meters off mount

# Make data
stiffness = 1 # N-m (torque)

T = np.arange(min_torque, max_torque, resolution) # N-m, net torque
T_l = (0.5 * T) + stiffness
T_r = (0.5 * T) - stiffness
A = np.arange(min_theta, max_theta, resolution) # radians, angle1
A2 = A.copy()
T_l, A = np.meshgrid(T_l, A)
T_r, A2 = np.meshgrid(T_r, A2)

fail = 1/0

### calculate the torque here
# Iterate through a grid of net torques and angles at a given stiffness
# for each actuator, based on torque and angle, calculate the pressure value for
# the mirroed actuators. Write down the two pressures in Xp, Yp, and two values
# Z_torque, Z_angle. Plot XYZ surface for both at different stiffness

L_angle_l = l0_l + l1_l * np.cos(alpha_l + A)
L_angle_r = l0_r + l1_r * np.cos(alpha_r + A)
F_l = T_l / (d_l * np.cos(beta_l + A))
F_r = T_r / (d_r * np.cos(beta_r + A))
K_l = (l_rest - L_angle_l) / l_rest
K_r = (l_rest - L_angle_l) / l_rest

P_l = a0 + a1 * np.tan(a2 * (K_l / (a4 * F_l + k_max)) + a3) + a5 * F_l # kpa
P_r = a0 + a1 * np.tan(a2 * (K_r / (a4 * F_r + k_max)) + a3) + a5 * F_r # kpa

# Plot the surface.
fig = plt.figure()
ax = fig.gca(projection='3d')

tsurf = ax.plot_surface(P_l, P_r, T, cmap=cm.coolwarm,
                        linewidth=0, antialiased=False)
# asurf = ax.plot_surface(P_l, P_r, A, cmap=cm.coolwarm,
#                         linewidth=0, antialiased=False)

# # Add a color bar which maps values to colors.
# fig.colorbar(surf, shrink=0.5, aspect=6)

plt.show()
