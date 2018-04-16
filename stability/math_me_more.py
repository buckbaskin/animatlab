from simple_mass_model import BaseSimulator
from bode import ActualSimulator, SimpleSimulator, FrozenOptimizingController

import numpy as np
from math import pi
from numpy import arctan, sqrt, floor, ceil

from matplotlib import pyplot as plt
plt.rc('font', **{'size': 28})

a0 = 254.3 # kpa
a1 = 192.0 # kpa
a2 = 2.0625
a3 = -0.461
a4 = -0.331 # 1 / Nm
a5 = 1.230
a6 = 15.6 # kpa

l_rest = .189 # m
l_620 = round(-((.17 * l_rest) - l_rest), 3)
k_max = 0.17
l_max = l_rest
l_min = l_620

d = 0.005 # m
offset = 0.015 # m
l1 = round(sqrt(d**2 + offset**2), 3)
l0 = floor((l_max - l1) * 1000.0) / 1000.0

alpha_l = arctan(offset / d) # radians
beta_l = -pi / 2 # radians, TODO(buckbaskin): assumes that muscle mounted d meters off mount
beta_l = 0 # for now

alpha_r = -arctan(offset / d) # radians
beta_r = pi / 2 # radians, TODO(buckbaskin): assumes that muscle mounted d meters off mount
beta_r = 0 # for now

PRESSURE_MAX = 620
PRESSURE_MIN = 0

hi = BaseSimulator()

ja = [
(620, 0, 0),
(0, 620, 0),
(310, 0, 0),
(0, 310, 0),
(620, 0, 10),
(0, 620, 10),
(310, 0, 10),
(0, 310, 10),
(620, 0, -10),
(0, 620, -10),
(310, 0, -10),
(0, 310, -10),
]

print('### Acceleration Fusion Network')

for extp, flxp, theta_mV in ja:
    extp_mV = extp / 620 * 20
    flxp_mV = flxp / 620 * 20
    theta = theta_mV / 20 * (pi / 4)
    state = np.array([theta, 0, 0, extp, flxp,])
    eT1, fT1 = hi.pressures_to_torque(extp, flxp, state)
    torque = eT1 - fT1
    torque_mV = torque / 2.5 * 20
    # TODO(buckbaskin): split out net torque to positive/negative guess
    print('(% 3d mV, % 3d mV, % 3d mV) -> (% 3d, % 3d, % 4.2f) --> % 2d Nm -> % 5.1f mV' % (
        extp_mV, flxp_mV, theta_mV,
        extp, flxp, theta,
        torque,
        torque_mV,))

ja2 = [
(0, 0),
(0, 20),
(0, -20),
(8, 0),
(8, 20),
(8, -20),
(-8, 0),
(-8, 20),
(-8, -20),
(4, 0),
(4, 20),
(4, -20),
]

print('\n### Parameter Adjustment/System Model')

for index, values in enumerate(ja2):
    pos_err_mV, velocity_mV = values
    pos_err = pos_err_mV / 20 * pi/4 # radians
    velocity = velocity_mV / 20 * 5 # rad/sec
    lambda_ = pos_err / (1 + velocity**2)
    C_err = lambda_ * velocity
    N_err = lambda_
    lambda_mV = lambda_ / 0.32 * 20
    C_err_mV = lambda_mV * velocity
    N_err_mV = lambda_mV
    print('(% 3d mV, % 3d mV) -> (% 4.2f, % 3.1f) --> (% 3.1f, % 3.1f) -> (% .1f mV, %5.1f mV)' % (
        pos_err_mV, velocity_mV,
        pos_err, velocity,
        C_err, N_err,
        C_err_mV, N_err_mV,))

print('\n### Accleration From Torque')

# inertia, damping and load in mV
ja3 = [
(  0,   0,   0,   0,   0),
( 20,   0,   0,   0,   0),
(-10,   0,   0,   0,   0),
( 10,  20,   0,  10,   0),
( 10, -10,   0,  10,   0),
(-10,  10,   0,  10,   0),
( 10,   0,  20,   0,   0),
(-10,   0,  10,   0,   0),
( 10,   0,   0,   0,  20),
(-10,   0,   0,   0,  10),
]

# inertia correspondence 20 mV -> 1

for torque_mV, velocity_mV, inertia_mV, damping_mV, load_mV in ja3:
    torque = torque_mV / 20 * 2.5
    velocity = velocity_mV / 20 * 5
    inertia = inertia_mV / 20 * 1
    damping = damping_mV / 20 * 1
    load = load_mV / 20 * 2

    M = inertia + 0.1
    C = velocity * damping
    N = load
    accel = (torque - C - N) / M

    accel_mV = accel / 30 * 20

    print('(% 3d mV, % 3d mV, % 3d mV, % 3d mV, % 3d mV) -> (...) --> (% 6.2f) -> (% 6.2f mV)' % (
        torque_mV, velocity_mV, inertia_mV, damping_mV, load_mV,
        accel,
        accel_mV,
        ))

print('\n### Torque Guessing/Forward Projection')

# inputs: Position, Vel, Acceleration
# output: Torque

ja4 = [
(0, 0, 0),
(0, 5, 0),
(0, -5, 0),

(5, 0, 0),
(-5, 0, 0),

(0, 2, 0),
(0, -2, 0),

(0, 0, 20),
(0, 0, -20),
(0, 1, 10),
(1, 0, -10),
(2, -2, 0), 
]

state_start = np.array([
    -0.01, # position
    # 0,
    0, # vel
    0, # accel
    0, # ext pressure
    0,]) # flx pressure

S = ActualSimulator(bang_bang=True, limit_pressure=True, TIME_END = 2.0)
estimated_S = SimpleSimulator(M=0.0004, C=0.10, N=-1.7000)

controller = FrozenOptimizingController(state_start, 0.0,
            sim = estimated_S, control_rate=S.CONTROL_RATE,
            time_horizon=1.5/S.CONTROL_RATE, stiffness=1.0,
            optimization_steps=15, iteration_steps=45)

for theta_mV, desired_theta_mV, velocity_mV in ja4:
    theta = theta_mV * (pi / 4) / 20
    desired_theta = desired_theta_mV * (pi / 4) / 20
    velocity = velocity_mV * 5 / 20

    state = np.array([theta, velocity, 0, 0, 0])
    desired_states = np.array([[desired_theta, 0, 0, 0, 0]])
    times = np.array([1.5/hi.CONTROL_RATE])
    _, _, des_torque = controller.control(state, desired_states, times)

    torque_mV = des_torque / 2.5 * 20

    print('(% 2d mV, % 2d mV, % 3d mV) -> (% .2f, % 5.2f, % 5.2f) --> (% 5.2f) -> (% 5.1f mV)' % (
        theta_mV, desired_theta_mV, velocity_mV,
        theta, desired_theta, velocity,
        des_torque,
        torque_mV,))

print('\n### Desired Torque -> Pressures')

# Inputs: Theta, Torque. Outputs -> Ext Pressure, Flx Pressure

ja5 = [
(0, 0),
(0, 2.5),
(0, -2.5),
(20, 0),
(20, 2.5),
(20, -2.5),
(-20, 0),
(-20, 2.5),
(-20, -2.5),
(10, 0),
(10, 2.5),
(10, -2.5),
]

for theta_mV, torque in ja5:
    theta = theta_mV / 20 * (pi / 4)
    torque_mV = torque / 2.5 * 20

    ext_pres, flx_pres = controller._convert_to_pressure(torque, state)

    extp_mV = ext_pres / 620 * 20
    flxp_mV = flx_pres / 620 * 20

    print('(% 3d mV, % 3d mV) -> (% 5.2f, % 5.2f) --> (% 3d, % 3d) -> (% .1f mV, % .1f mV)' % (
        theta_mV, torque_mV,
        theta, torque,
        ext_pres, flx_pres,
        extp_mV, flxp_mV,))