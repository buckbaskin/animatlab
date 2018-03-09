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

max_torque = 2.001
min_torque = -2
torque_resolution = 0.5
max_theta = pi / 4 + .001
min_theta = -pi / 4
angle_resolution = pi / 8.0

### Model Parameters ###

a0 = 254.3 # kpa
a1 = 192.0 # kpa
a2 = 2.0625
a3 = -0.461
a4 = -0.331 # 1 / Nm
a5 = 1.230
a6 = 15.6 # kpa

### Mutual Actuator Parameters ### 

l_rest = .189 # m
l_620 = round(-((.17 * l_rest) - l_rest), 3)
k_max = 0.17
l_max = l_rest
l_min = l_620

d = 0.005 # m
offset = 0.015 # m
l1 = round(sqrt(d**2 + offset**2), 3)
l0 = floor((l_max - l1) * 1000.0) / 1000.0

### Saftey Limits

MAX_STIFFNESS = 2
MIN_STIFFNESS = 0

FORCE_MAX = 15 * 9.81 # Newtons, about 15 kg
FORCE_MIN = -15 * 9.81 # N

PRESSURE_MAX = 620
PRESSURE_MIN = 0

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


def pressure(T, A):
    F = T / (d * np.cos(beta_l + A))
    L_angle = l0 + l1 * np.cos(alpha_l + A)
    K = (l_rest - L_angle) / l_rest
    assert np.all(0 <= K) and np.all(K <= 1)
    P = a0 + a1 * np.tan(a2 * (K / (a4 * F + k_max)+ a3)) + a5 * F # kpa
    return np.clip(P, PRESSURE_MIN, PRESSURE_MAX)

def pressure2(F, K, S=1):
    assert np.all(0 <= K) and np.all(K <= 1)
    P = a0 + a1 * np.tan(a2 * (K / (a4 * F + k_max)+ a3)) + a5 * F + a6 * S# kpa
    return np.clip(P, PRESSURE_MIN, PRESSURE_MAX)


delt = 0.01
state_a = np.arange(-pi/2, pi/2+.001, 0.05)
state_t = 0
# state_a = pi/8
dPdA = (pressure(state_t, state_a+delt) - pressure(state_t, state_a-delt)) / (delt - (-delt))
dPdT = (pressure(state_t+delt, state_a) - pressure(state_t-delt, state_a)) / (delt - (-delt))
# print('P(%.1f, %.1f)' % (state_t, state_a), pressure(T=state_t, A=state_a))
# print('dPdA', dPdA)
# print('dPdT', dPdT)

# plt.plot(state_a, pressure(state_t, state_a))
# plt.plot(state_a, dPdT)
# plt.plot(state_a, dPdA)

for F in [0.14, 0, 0.07,]: # What are these units? Supposedly Nm? 24 lb, 0 lb, 12 lb respectively 
    K = np.arange(0, 0.1701, 0.0001)
    print(a4 * F)
    # plt.plot(K, a2*(K / (a4 * F + k_max) + a3))
    plt.plot(K, pressure2(F, K))
    # plt.plot(K, pressure2(F, K))
plt.show()
import sys
sys.exit(0)


### Make data ###
stiffness = 1 # N-m (torque)
stiffness = np.clip(stiffness, 0, 2) # force boundary limits

T = np.arange(min_torque, max_torque, torque_resolution) # N-m, net torque
T_r = (0.5 * T) + stiffness
T_l = (0.5 * T) - stiffness

A = np.arange(min_theta, max_theta, angle_resolution) # radians, angle1
A2 = A.copy()
T_l, A = np.meshgrid(T_l, A)
T_r, A2 = np.meshgrid(T_r, A2)

### calculate the torque here
# Iterate through a grid of net torques and angles at a given stiffness
# for each actuator, based on torque and angle, calculate the pressure value for
# the mirroed actuators. Write down the two pressures in Xp, Yp, and two values
# Z_torque, Z_angle. Plot XYZ surface for both at different stiffness

L_angle_l = l0 + l1 * np.cos(alpha_l + A)
L_angle_r = l0 + l1 * np.cos(alpha_r + A)
F_l = T_l / (d * np.cos(beta_l + A))
F_r = T_r / (d * np.cos(beta_r + A))
np.clip(F_l, FORCE_MIN, FORCE_MAX, out=F_l)
np.clip(F_r, FORCE_MIN, FORCE_MAX, out=F_r)

K_l = (l_rest - L_angle_l) / l_rest
K_r = (l_rest - L_angle_l) / l_rest

P_l = a0 + a1 * np.tan(a2 * (K_l / (a4 * F_l + k_max)) + a3) + a5 * F_l # kpa
P_r = a0 + a1 * np.tan(a2 * (K_r / (a4 * F_r + k_max)) + a3) + a5 * F_r # kpa
np.clip(P_l, PRESSURE_MIN, PRESSURE_MAX, out=P_l)
np.clip(P_r, PRESSURE_MIN, PRESSURE_MAX, out=P_r)

print(P_r)
1/0

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
