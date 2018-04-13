import numpy as np

from math import pi
from matplotlib import pyplot as plt

time_res = 0.01
time = np.arange(0, 10, time_res)

period = 1
adjust = (2*pi) / period

pos = (pi/4) * np.sin(time * adjust)
vel = np.gradient(pos) / time_res
accel = np.gradient(vel) / time_res

M = 1
C = 0.1
def M(P):
    return 1

def C(P, V):
    return 0.1

def N(P):
    link_mass = 0.25
    link_length = 0.25
    return (link_mass * 9.81 * link_length) * np.sin(P)

T = M(pos) * accel + C(pos, vel) * vel + N(pos)

print('Maximum and Minimum Torques Required for Trajectory:')
print('%.2f Nm' % np.max(T))
print('%.2f Nm' % np.min(T))

plt.plot(time, pos, label='Position (rad)')
plt.plot(time, vel, label='Velocity (rad/sec)')
plt.plot(time, accel,  label='Accleration (rad/sec^2)')
plt.plot(time, T,  label='Torque (Nm)')
plt.title('M acc + C vel + N = T')
plt.legend()
plt.show()
