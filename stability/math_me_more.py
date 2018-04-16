from simple_mass_model import BaseSimulator

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
    print('(%d mV, %d mV, %d mV) -> (%d, %d, %.2f) -> %f Nm -> %.1f mV' % (
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

for index, values in enumerate(ja2):
    pos_err_mV, velocity_mV = values
    pos_err = pos_err_mV / 20 * pi/4 # radians
    velocity = velocity_mV / 20 * 5 # rad/sec
    lambda_ = pos_err / (1 + velocity**2)
    lambda_mV = lambda_ / 0.32 * 20
    C_err = lambda_mV * velocity
    N_err = lambda_mV
    print('%s -> (%.2f, %.2f)' % (values, C_err, N_err,))