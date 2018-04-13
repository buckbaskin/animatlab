import sys
print('--- %s ---' % (sys.argv[0],))

import datetime
import math
import matplotlib.pyplot as plt
import numpy as np

from functools import partial
from math import pi
from numpy import arctan, sqrt, floor, ceil
from simple_mass_model import ActualSimulator, SimpleSimulator
from simple_mass_model import OptimizingController

ERROR_STANDARD = 1 # degree
ERROR_STANDARD = ERROR_STANDARD / 180 * pi # radians
SCORING_DELAY = 750

class FrozenOptimizingController(OptimizingController):
    def control(self, state, desired_states, times):
        self.est_state = self.sensor_fusion(self.est_state, self.last_est_time,
            self.lag_pos, state, times[0])

        self.last_est_time = times[0]
        self.lag_pos = self.est_state[0]

        des_torque = self._pick_torque(self.est_state, desired_states, times)
        des_ext_pres, des_flx_pres = self._convert_to_pressure(des_torque, state)

        self.last_control = des_torque

        return des_ext_pres, des_flx_pres, des_torque

if __name__ == '__main__':
    plt.rc('font', **{'size': 28})
    S = ActualSimulator(bang_bang=True, limit_pressure=True, TIME_END = 2.0)
    
    linewidth = 4

    # plt.title('Pressure Torque Relation (Flx)')
    fig = plt.figure(figsize=(11.5, 4.5,), dpi=300)
    ax = fig.add_subplot(111)
    ax.set_xlabel('Torque (Nm)')
    ax.set_ylabel('Pressure (kPa)')
    ax.set_xlim(0, 3)
    ax.set_ylim(0, 620)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines['right'].set_color('none')
    ax.spines['left'].set_linewidth(linewidth)
    ax.spines['top'].set_color('none')
    ax.spines['bottom'].set_linewidth(linewidth)

    angles = np.linspace(0, math.pi * 1 / 4, 3)
    for angle in angles:
        state = np.zeros((5,))
        state[0] = angle
        torques = np.linspace(0.01, 3, 400)
        pressures = S.flx_torque_to_pressure(torques, state) # * np.cos(angle)
        # this shows that the entire thing can be calculated by a normalized 
        # linear thing, then divided by cosine(theta)
        #   Input range: 0 -> 2.5 Nm <> 0 to 20 mV
        #   Output range: 0 -> 620 Nm <> 0 to 20 mV
        # But then divide by cos(angle) -> increasing torque requirements for
        #   increasing angle
        # This doesn't quite correspond with how the neurons do
        ax.plot(torques, pressures*1.015, label='%.2f (rad)' % (angle), linewidth=linewidth)
    plt.legend()
    print('go find the plot and close it please')
    plt.savefig('FigPressureTorque.png')
    plt.show()
    print('all done for real now')
