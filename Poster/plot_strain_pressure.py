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

def pressure(strain, F=0.0533):
    K = strain
    P = (a0 + a1 *
        np.tan(a2 * (K / (a4 * F + k_max)+ a3))
        + a5 * F) # kpa
    return np.clip(P, PRESSURE_MIN, PRESSURE_MAX)

max_strain = 0.16
strain = np.linspace(0, max_strain, 100)
p = pressure(strain)

linewidth = 4

fig = plt.figure(figsize=(5.5, 6,), dpi=300)
ax = fig.add_subplot(111)
ax.set_xlim(0, max_strain)
ax.set_ylim(0, 615)
ax.set_xticks([])
ax.set_yticks([])
ax.set_xlabel('Strain')
ax.set_ylabel('Pressure (kPa)')
ax.spines['right'].set_color('none')
ax.spines['left'].set_linewidth(linewidth)
ax.spines['top'].set_color('none')
ax.spines['bottom'].set_linewidth(linewidth)

ax.plot(strain, pressure(strain, F=0.0), linewidth=linewidth, label='0 lb')
ax.plot(strain, pressure(strain, F=0.05), linewidth=linewidth, label='12 lb')
ax.plot(strain, pressure(strain, F=0.10), linewidth=linewidth, label='24 lb')
ax.legend()
plt.savefig('FigStrainPressure.png')
plt.show()