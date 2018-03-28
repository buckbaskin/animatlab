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
SCORING_DELAY = 1250

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
    S = ActualSimulator(bang_bang=True, limit_pressure=True, TIME_END = 3.0)
    time = S.timeline()

    MAX_AMPLITUDE = S.MAX_AMPLITUDE

    state_start = np.array([
        -0.01, # position
        # 0,
        0, # vel
        0, # accel
        0, # ext pressure
        0,]) # flx pressure

    ### Set up desired state ###
    # the desired state velocity and acceleration are positive here
    desired_state = np.zeros((time.shape[0], state_start.shape[0],))

    # TODO(buckbaskin): remove stiffness?
    stiffness = 0.5

    periods = np.array([100, 50, 20, 10, 5, 2, 1])
    frequencies = 1.0 / periods
    tracking_score = np.zeros(periods.shape)

    # Try following a sin curve of varying period
    # TODO(buckbaskin): adjust the plotting to first show the different iterations
    # TODO(buckbaskin): then plot something like a Bode Plot
    for index, period in enumerate(periods):
        print('period: %.2f' % (period,))
        adjust = (pi * 2) / period 
        desired_state[:, 0] = MAX_AMPLITUDE * np.sin(time * adjust)
        desired_state[:, 1] = (MAX_AMPLITUDE * adjust) * np.cos(time * adjust)
        desired_state[:, 2] = -(MAX_AMPLITUDE * adjust * adjust) * np.sin(time * adjust)

        plt_index = 0

        fig = plt.figure()
        ax_pos = fig.add_subplot(2, 1, 1)
        titlte = 'Estimated vs Actual %s, Period %.2f'
        if plt_index == 0:
            titlte = titlte % ('Position', period,)
            ylabel = 'Position (rad)'
        if plt_index == 1:
            titlte = titlte % ('Velocity', period,)
            ylabel = 'Velocity (rad/sec)'
        if plt_index == 2:
            titlte = titlte % ('Acceleration', period,)
            ylabel = 'Acceleration (rad/sec**2)'
        ax_pos.set_title(titlte)
        ax_pos.set_ylabel(ylabel)
        ax_pos.set_xlabel('Time (sec)')
        ax_pos.plot(time,  desired_state[:,plt_index], 
            color='tab:blue', label='Desired')
        if plt_index == 0:
            ax_pos.plot(time[SCORING_DELAY:], desired_state[SCORING_DELAY:,plt_index] + ERROR_STANDARD,
                color='tab:purple', label='MAXIMUM')
            ax_pos.plot(time[SCORING_DELAY:], desired_state[SCORING_DELAY:,plt_index] - ERROR_STANDARD,
                color='tab:purple', label='MINIMUM')
        
        estimated_S = SimpleSimulator(M=0.0004, C=0.10, N=-1.7000)
    
        C = FrozenOptimizingController(state_start, time[0],
            sim = estimated_S, control_rate=S.CONTROL_RATE,
            time_horizon=1.5/S.CONTROL_RATE, stiffness=stiffness,
            optimization_steps=15, iteration_steps=45)

        full_state, est_state = S.simulate(controller=C, state_start=state_start, desired_state=desired_state)

        result = S.evaluation(full_state, desired_state, S.timeline())
        print('Simulation Evaluation:')
        print('Controller: %s' % (str(C),))
        print('Maximum Positional Error: %.3f (rad)' % (result['max_pos_error']))
        tracking_err = abs(result['max_pos_error'])
        score = np.clip((ERROR_STANDARD - tracking_err) / ERROR_STANDARD, 0, 1)
        print('Error Score: %.1f' % (score * 100.0,))
        tracking_score[index] = score

        ax_pos.plot(time, full_state[:,plt_index],
            color='tab:orange', label='Actual State')
        ax_pos.plot(time, est_state[:,plt_index],
            color='tab:green', label='Internal Est. State')
        ax_pos.legend()
        print('show for the dough')
        plt.show()
        print('all done')

    ax_mag = fig.add_subplot(2, 1, 1)
    ax_mag.set_title('Bode, Magnitude')
    ax_mag.set_ylabel('Magnitude (%)')
    ax_mag.set_xlabel('Frequency (hz)')
    ax_mag.plot(frequencies,  tracking_score, color='tab:blue', label=str(C))
    ax_mag.legend()
    plt.show()
    # plt.savefig('Bode_Plot.png')