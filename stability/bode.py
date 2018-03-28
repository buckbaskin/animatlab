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
    S = ActualSimulator(bang_bang=True, limit_pressure=True, TIME_END = 2.0)
    time = S.timeline()

    if False:
        fake1 = np.sin(time*10)
        fake2 = np.sin((time - 0.5)*10)

        delts = []
        # estimate difference in phase
        for i in range(750, len(time)-1):
            if (fake1[i-1] <= fake1[i] and
                fake1[i+1] <= fake1[i]):
                print('found a desired local max %d' % (i,))
                for j in range(i, len(time)-1):
                    if (fake2[j-1] <= fake2[j] and
                        fake2[j+1] <= fake2[j]):
                        print('found an actual local max %d' % (j,))
                        # difference in time between two maximums
                        delta_t = time[j] - time[i]
                        delts.append(delta_t)
                        break
        print(delts)
        plt.plot(time, fake1)
        plt.plot(time, fake2)
        plt.show()
        # assuming a similar frequency, avg time delta is an ok estimate of phase
        if len(delts) > 0:
            phase_est = np.mean(delts)
        else:
            phase_est = 0.0

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

    periods = np.array([500, 200, 100, 50, 20, 10, 5, 2, 1, 0.5,])
    periods = np.flip(periods, 0)
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

        # fig = plt.figure()
        # ax_pos = fig.add_subplot(2, 1, 1)
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
        # ax_pos.set_title(titlte)
        # ax_pos.set_ylabel(ylabel)
        # ax_pos.set_xlabel('Time (sec)')
        # ax_pos.plot(time,  desired_state[:,plt_index], 
        #     color='tab:blue', label='Desired')
        if plt_index == 0:
            # ax_pos.plot(time[SCORING_DELAY:], desired_state[SCORING_DELAY:,plt_index] + ERROR_STANDARD,
            #     color='tab:purple', label='MAXIMUM')
            # ax_pos.plot(time[SCORING_DELAY:], desired_state[SCORING_DELAY:,plt_index] - ERROR_STANDARD,
            #     color='tab:purple', label='MINIMUM')
            pass
        
        estimated_S = SimpleSimulator(M=0.0004, C=0.10, N=-1.7000)
    
        C = FrozenOptimizingController(state_start, time[0],
            sim = estimated_S, control_rate=S.CONTROL_RATE,
            time_horizon=1.5/S.CONTROL_RATE, stiffness=stiffness,
            optimization_steps=15, iteration_steps=45)

        full_state, est_state = S.simulate(controller=C, state_start=state_start, desired_state=desired_state)

        # evaluation(self, states, desired_states, times,
        #   amplitude=None, frequency=None, phase=None, delay=None)
        result = S.evaluation(full_state, desired_state, S.timeline(),
            amplitude=MAX_AMPLITUDE, frequency=1.0/period, phase=0.0,
            delay=SCORING_DELAY)
        print('Simulation Evaluation:')
        print('Controller: %s' % (str(C),))
        print('Maximum Positional Error: %.3f (rad)' % (result['max_pos_error']))
        tracking_err = abs(result['max_pos_error'])
        score = (ERROR_STANDARD - tracking_err) / ERROR_STANDARD
        # score = np.clip(score, 0, 1)
        print('Error Score: %.1f' % (score * 100.0,))
        print('Phase offset: %.3f' % (result['phase_offset']))
        tracking_score[index] = score

        # ax_pos.plot(time, full_state[:,plt_index],
        #     color='tab:orange', label='Actual State')
        # ax_pos.plot(time, est_state[:,plt_index],
        #     color='tab:green', label='Internal Est. State')
        # ax_pos.legend()
        # print('show for the dough')
        # plt.show()

    fig = plt.figure()
    ax_mag = fig.add_subplot(2, 1, 1)
    ax_mag.set_title('Bode, Magnitude')
    ax_mag.set_ylabel('Magnitude (%)')
    ax_mag.set_xlabel('Frequency (hz)')
    ax_mag.set_xscale('log')
    ax_mag.plot(frequencies,  tracking_score, color='tab:blue', label=str(C))
    ax_mag.legend()
    plt.savefig('Bode_Plot.png')
    print('showing again')
    plt.show()
    print('all done for real now')
