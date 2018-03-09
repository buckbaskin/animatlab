'''
======================
Plot Level curve (Desired Torque)
======================
Based on matplotlib 3D surface (color map) demo
https://matplotlib.org/mpl_toolkits/mplot3d/tutorial.html

And level curve/contour plotting
https://matplotlib.org/gallery/mplot3d/contour3d.html

So, how does this help? I can figure out the torques that I want for a desired 
stiffness. 
The goal is an inversion question: At a current position, etc. I want to PD
drive the joint to the desired position by setting a joint torque. I can do this
with the antagonistic torque model calculated below. Stiffness here doesn't
change net torque on the joint (behavior might change later).

DesTorque = -K_p * p + -K_v * v

T_r =  0.5 * T_des + stiffness
T_l =  -(0.5 * T_des - stiffness) # positive from the point of view of the actuator
'''
print('---=== plot_level_curves.py ===---')
from math import atan, floor, pi, sqrt

from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter
import numpy as np


### Search Parameters ###

max_torque = 2.001
min_torque = -2
torque_resolution = 0.01
max_theta = pi / 4 + .001
min_theta = -pi / 4
angle_resolution = pi / 32

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
beta_l = 0 # for now

alpha_r = -atan(offset / d) # radians
beta_r = pi / 2 # radians, TODO(buckbaskin): assumes that muscle mounted d meters off mount
beta_r = 0 # for now


def pressurel(T, A):
    F = T / (d * np.cos(beta_l + A))
    # print('pressurel:T', T)
    # print('pressurel:A', A)
    # print('pressurel:F', F)
    L_angle = l0 + l1 * np.cos(alpha_l + A)
    K = (l_rest - L_angle) / l_rest
    assert np.all(0 <= K) and np.all(K <= 1)
    P = a0 + a1 * np.tan(a2 * (K / (a4 * F + k_max)+ a3)) + a5 * F # kpa
    return np.clip(P, PRESSURE_MIN, PRESSURE_MAX)

def pressurer(T, A):
    F = T / (d * np.cos(beta_r + A))
    # print('pressurer:T', T)
    # print('pressurer:A', A)
    # print('pressurer:F', F)
    L_angle = l0 + l1 * np.cos(alpha_r + A)
    K = (l_rest - L_angle) / l_rest
    assert np.all(0 <= K) and np.all(K <= 1)
    P = a0 + a1 * np.tan(a2 * (K / (a4 * F + k_max)+ a3)) + a5 * F # kpa
    return np.clip(P, PRESSURE_MIN, PRESSURE_MAX)

### Make data ###
stiffness = 1.0 # N-m (torque)
stiffness = np.clip(stiffness, 0, 2) # force boundary limits

T = np.arange(min_torque, max_torque, torque_resolution) # N-m, net torque
# T = np.array([0.00, 0.5])
T_r = (0.5 * T) + stiffness
# T_r[T_r == 0] += torque_resolution
T_l = -((0.5 * T) - stiffness)
# T_l[T_l == 0] -= torque_resolution

A = np.arange(min_theta, max_theta, angle_resolution) # radians, angle1
A2 = A.copy()
T_l, A = np.meshgrid(T_l, A)
T_r, A2 = np.meshgrid(T_r, A2)

### calculate the torque here
# Iterate through a grid of net torques and angles at a given stiffness
# for each actuator, based on torque and angle, calculate the pressure value for
# the mirroed actuators. Write down the two pressures in Xp, Yp, and two values
# Z_torque, Z_angle. Plot XYZ surface for both at different stiffness

P_l = pressurel(T_l, A) # kpa
P_r = pressurer(T_r, A2) # kpa

# Plot the surfaces
if False:
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    tarsurf = ax.plot_surface(A, T_r, P_r)
    plt.title('P(T, A) for the Right Actuator')

if False:
    fig = plt.figure()
    ax = plt.gca(projection='3d')
    talsurf = ax.plot_surface(A, T_l, P_l)
    plt.title('P(T, A) for the Left Actuator')

if False:
    # I really need/want that level curves thingy
    # also masked np arrays (if they work with this) would be great
    # I'd like to trim the parts of the plot out where the pressure is clipped
    netT = T_r - T_l

    fig = plt.figure()
    ax = plt.gca(projection='3d')
    nT = ax.plot_surface(P_r, P_l, netT)
    plt.title('Net Torque from Pressures')

# plt.show()
