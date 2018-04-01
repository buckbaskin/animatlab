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

class NeuronLikeController(FrozenOptimizingController):
    accel_gain = 1.5899
    vel_gain = 0.0477
    def __str__(self):
        return 'NeuronLikeController()'

    def internal_model(self, state, desired_torque, end_time):
        '''
        Velocity Gain:
        Gain of velocity's effect on position. 

        Acceleration Gain:
        Gain of accel effect on position. Incorporates mass and time step into a
        single number, corresponding to the gain of the edge in the neuron 
        network
        '''
        times = np.linspace(0, end_time, 2)
        full_state = np.zeros((times.shape[0], state.shape[0],))
        full_state[0,:] = state

        vel_mod = state[1] + desired_torque * self.accel_gain
        full_state[1,0] = state[0] + vel_mod * self.vel_gain
        return full_state

if __name__ == '__main__':
    ### Set up time ###
    S = ActualSimulator(bang_bang=True, limit_pressure=True)
    time = S.timeline()

    MAX_AMPLITUDE = S.MAX_AMPLITUDE

    state_start = np.array([
        -MAX_AMPLITUDE / 2, # position
        # 0,
        0, # vel
        0, # accel
        0, # ext pressure
        0,]) # flx pressure

    ### Set up desired state ###
    # the desired state velocity and acceleration are positive here
    desired_state = np.zeros((time.shape[0], state_start.shape[0],))

    # Try following a sin curve
    period = 10
    adjust = (pi * 2) / period 
    desired_state[:, 0] = MAX_AMPLITUDE * np.sin(time * adjust)
    desired_state[:, 1] = (MAX_AMPLITUDE * adjust) * np.cos(time * adjust)
    desired_state[:, 2] = -(MAX_AMPLITUDE * adjust * adjust) * np.sin(time * adjust)

    plot_position = True
    plt_index = 0

    if plot_position:
        fig = plt.figure()
        ax_pos = fig.add_subplot(1, 1, 1)
        ax_pos.set_title('Estimated vs Actual Accel')
        ax_pos.set_ylabel('Accel')
        ax_pos.set_xlabel('Time (sec)')
        ax_pos.plot(time,  desired_state[:,plt_index], 
            color='tab:blue', label='Desired')
        if plt_index == 0:
            ax_pos.plot(time[1000:], desired_state[1000:,plt_index] + ERROR_STANDARD,
                color='tab:purple', label='MAXIMUM')
            ax_pos.plot(time[1000:], desired_state[1000:,plt_index] - ERROR_STANDARD,
                color='tab:purple', label='MINIMUM')
        
    print('calculating...')
    stiffness = 1.0
    for index, _ in enumerate([0.0]):
        estimated_S = SimpleSimulator(M=0.0004, C=0.10, N=-1.7000)
    
        C = FrozenOptimizingController(state_start, time[0],
            sim = estimated_S, control_rate=S.CONTROL_RATE,
            time_horizon=1.5/S.CONTROL_RATE, stiffness=stiffness,
            optimization_steps=8, iteration_steps=35)

        full_state, est_state = S.simulate(controller=C, state_start=state_start, desired_state=desired_state)

        result = S.evaluation(full_state, desired_state, S.timeline(), delay=SCORING_DELAY)
        print('Simulation Evaluation:')
        print('Controller: %s' % (str(C),))
        print('Maximum Positional Error: %.3f (rad)' % (result['max_pos_error']))
        tracking_err = abs(result['max_pos_error'])
        score = (ERROR_STANDARD - tracking_err) / ERROR_STANDARD
        # score = np.clip(score, 0, 1)
        print('Error Score: %.1f' % (score * 100.0,))
        print('Phase offset: %.3f' % (result['phase_offset']))
        
        if plot_position:
            ax_pos.plot(time, full_state[:,plt_index],
                color='tab:orange', label='Actual State')
            ax_pos.plot(time, est_state[:,plt_index],
                color='tab:green', label='Internal Est. State')
    if plot_position:
        ax_pos.legend()
        print('show for the dough')
        plt.savefig('State_Estimation.png')
        plt.show()
        print('all done')
