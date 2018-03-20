'''
Build a single joint dynamic model, 2 different Festos, negative feedback based 
on  pressure/position curves. This is a numerical model where everything happens 
nicely.

M(\theta) \ddot{\theta} + C(\theta, \dot{\theta}) \dot{\theta} + N(\theta) \theta
= Torque

Mass Model:
Joint is hung vertically for now
M: A point mass at a distance from the joint (rotational inertia)
C: A small damping factor is assumed
N: gravity on the point mass at a distance, weight of robot

Notes:
- Pushing static stiffness too high causes clipping for the primary actuator, so less 
    net torque is achieved and decreased line following is achieved
- Dynamic gains that are too high cause sawtooth oscillation and instability
- Dynamic gains that are too low cause lagging trajectory execution
'''
import sys
print('--- %s ---' % (sys.argv[0],))

import math
import numpy as np
import matplotlib.pyplot as plt

from math import pi
from numpy import arctan, sqrt, floor, ceil

class Simulator(object):
    def __init__(self, bang_bang=True, limit_pressure=True, **kwargs):
        '''
        Set defaults, and override extras with kwargs
        '''
        self.bang_bang = bang_bang
        self.limit_pressure = limit_pressure
        ### Simulation Parameters and Constants ###
        self.MAX_AMPLITUDE = math.pi / 16

        self.LINK_LENGTH = 0.25 # meters
        self.LINK_MASS = 0.25 # kg
        self.ROBOT_MASS = 0.6 # kg

        self.TORQUE_MAX = 5.0
        self.TORQUE_MIN = 0.0

        self.PRESSURE_MAX = 620
        self.PRESSURE_MIN = 0

        self.PRESSURE_RATE_MAX = 500 # 200 kPa per sec works

        self.PRESSURE_RESOLUTION = 17.0 # hysterisis gap, # 17 works

        self.TIME_RESOLUTION = 0.001
        self.TIME_START = 0
        self.TIME_END = 10

        self.CONTROL_RATE = 500

        ## Actuator Model Parameters ##

        self.a0 = 254.3 # kpa
        self.a1 = 192.0 # kpa
        self.a2 = 2.0625
        self.a3 = -0.461
        self.a4 = -0.331 # 1 / Nm
        self.a5 = 1.230
        self.a6 = 15.6 # kpa

        ## Mutual Actuator Parameters ##

        self.l_rest = .189 # m
        self.l_620 = round(-((.17 * self.l_rest) - self.l_rest), 3)
        self.k_max = 0.17
        self.l_max = self.l_rest
        self.l_min = self.l_620

        self.d = 0.005 # m
        self.offset = 0.015 # m
        self.l1 = round(sqrt(self.d**2 + self.offset**2), 3)
        self.l0 = floor((self.l_max - self.l1) * 1000.0) / 1000.0

        ## Specific Actuator Parameters ##
        # Actuator L is the negative (flexion) actuator
        # Actuator R is the positive (extension) actuator
        # /////////////
        #    l  |   r
        #    l  |   r
        #     l |  r
        #     l(o) r
        #      x>\<x
        #       . \
        #       .  \
        #       .   \

        self.alpha_l = arctan(self.offset / self.d) # radians
        self.beta_l = -pi / 2 # radians, TODO(buckbaskin): assumes that muscle mounted d meters off mount
        self.beta_l = 0 # for now

        self.alpha_r = -arctan(self.offset / self.d) # radians
        self.beta_r = pi / 2 # radians, TODO(buckbaskin): assumes that muscle mounted d meters off mount
        self.beta_r = 0 # for now

        self.last_control = (0.0, 0.0, 0.0,)

        for arg, val in kwargs.items():
            if hasattr(self, arg):
                setattr(self, arg, val)
            else:
                raise ValueError('%s does not have attribute %s' % (self, arg,))

    def flx_torque_to_pressure(self, torque, state):
        T = torque
        A = state[0]
        F = T / (self.d * np.cos(self.beta_l + A))
        L_angle = self.l0 + self.l1 * np.cos(self.alpha_l + A)
        K = (self.l_rest - L_angle) / self.l_rest
        assert np.all(0 <= K) and np.all(K <= 1)
        P = (self.a0 + self.a1 *
            np.tan(self.a2 * (K / (self.a4 * F + self.k_max)+ self.a3))
            + self.a5 * F) # kpa
        return np.clip(P, self.PRESSURE_MIN, self.PRESSURE_MAX)

    def ext_torque_to_pressure(self, torque, state):
        T = torque
        A = state[0]
        F = T / (self.d * np.cos(self.beta_r + A))
        L_angle = self.l0 + self.l1 * np.cos(self.alpha_r + A)
        K = (self.l_rest - L_angle) / self.l_rest
        assert np.all(0 <= K) and np.all(K <= 1)
        P = (self.a0 + self.a1 *
            np.tan(self.a2 * (K / (self.a4 * F + self.k_max)+ self.a3))
            + self.a5 * F) # kpa
        return np.clip(P, self.PRESSURE_MIN, self.PRESSURE_MAX)

    def pressures_to_torque(self, extp, flxp, state, stiffness, actual_torque=None):
        '''
        Inverse model: given the pressures of the left and right actuator, estimate
        the torque on the joint
        Complications:
            - [x] Linear search through torque
            - [ ] Search through torque for speedup
        '''
        
        ### Calculate errors from guessing torque ###

        # TODO(buckbaskin): this is slow
        maximum_torque = np.max([np.abs(self.TORQUE_MAX), np.abs(self.TORQUE_MIN)])
        torque_guesses = np.arange(-maximum_torque, maximum_torque, 0.05)
        ext_guess = torque_guesses / 2 + stiffness
        flx_guess = -torque_guesses / 2 + stiffness

        extp_guesses = self.ext_torque_to_pressure(ext_guess, state)
        extp_guesses = np.clip(extp_guesses, self.PRESSURE_MIN, self.PRESSURE_MAX)
        flxp_guesses = self.flx_torque_to_pressure(flx_guess, state)
        flxp_guesses = np.clip(flxp_guesses, self.PRESSURE_MIN, self.PRESSURE_MAX)

        extp_err = np.abs(extp_guesses - extp)
        flxp_err = np.abs(flxp_guesses - flxp)

        total_err = extp_err + flxp_err
        best_guess = torque_guesses[np.argmin(total_err)]

        if actual_torque is not None:
            print('attempted', actual_torque, 'actual', best_guess)
        return best_guess

    def mass_model(self, theta):
        '''
        Mass Model
        ma -> I theta_ddot

        Implements: mass at a rigid point half of link length
        Complications:
            - [ ] Uniform mass distribution on the link
        '''
        M = self.LINK_MASS
        R = self.LINK_LENGTH / 2
        return M * (R**2)

    def vel_effects(self, theta, theta_dot):
        '''
        Damping/Velocity based effects on the system
        Complications:
            - [ ] Small damping from flexing of actuators based on change in length
            - [ ] Estimated Hysterisis effect of filling or empty actuators applying
                    a torque opposite the motion
        '''
        return 0.1 * theta_dot

    def conservative_effects(self, theta):
        '''
        Conservative Forces on the system, converted to torques (for now)
        Complications:
            - [x] Gravity from link mass
                    /////////////
                        (o)
                         .\
                         . \
                         .  m
                         .  :\
                         .  : \
                         .  v
            - [x] Gravity from robot/Suppoting Normal force from ground at end
                    /////////////
                        (o)
                         .\
                         . \  ^
                         .  \ :
                         .   \:
                         .    0
                         .   
        '''
        g = 9.81
        M_l = self.LINK_MASS
        F_g = M_l * g
        R_g = self.LINK_LENGTH / 2

        # this assumes that the robot mass is solely balanced on top of the joint
        M_r = self.ROBOT_MASS
        F_r = M_r * g
        R_n = self.LINK_LENGTH

        try:
            link_gravity = F_g * R_g * math.sin(theta)
        except ValueError:
            print(type(theta))
            print(theta)
            raise
        normal_force = - F_r * R_n * math.sin(theta)

        return link_gravity + normal_force

    def pressure_model(self, des_pressure, current_pressure, time_step):
        '''
        For now, set the pressure to the desired pressure
        In the future, use airflow model to restrict maximum pressure change
        Complications:
        - [x] Set pressure to desired pressure
        - [x] Bang-bang control
        - [x] Set maximum pressure change per time step
        - [ ] Develop airflow model to more accurately limit pressure changes 
              (pressure differential, airflow limits)
        '''
        # As implemented, controller either doesn't change if close or moves to the
        #   near side of the bang-bang window (close enough). This ignores details 
        #   of filling rate and pressure differential from the air supply to the
        #   actuator.
        if not self.bang_bang and not self.limit_pressure:
            return des_pressure
        if not self.bang_bang:
            return np.clip(des_pressure,
                current_pressure - self.PRESSURE_RATE_MAX,
                current_pressure + self.PRESSURE_RATE_MAX)
        if (float(abs(des_pressure - current_pressure)) < 
            float(self.PRESSURE_RESOLUTION)):
            return current_pressure
        elif des_pressure > current_pressure:
            if not self.limit_pressure:
                return des_pressure - self.PRESSURE_RESOLUTION
            return np.min([des_pressure - self.PRESSURE_RESOLUTION,
                current_pressure + self.PRESSURE_RATE_MAX * time_step])
        else: # des_pressure < current_pressure
            if not self.limit_pressure:
                return des_pressure + self.PRESSURE_RESOLUTION
            return np.max([des_pressure + self.PRESSURE_RESOLUTION,
                current_pressure - self.PRESSURE_RATE_MAX * time_step])

    def motion_evolution(self, state, time_step, control, control_stiffness):
        '''
        M * ddot theta + C * dot theta + N * theta = torque
        ddot theta = 1 / M * (torque - C * dot theta - N) 
        '''
        ext_pres = state[3]
        flx_pres = state[4]

        des_ext_pres, des_flx_pres, intended_torque = control

        ext_pres = self.pressure_model(des_ext_pres, ext_pres, time_step)
        flx_pres = self.pressure_model(des_flx_pres, flx_pres, time_step)

        Torque_net = self.pressures_to_torque(ext_pres, flx_pres, state, control_stiffness)

        M = self.mass_model(state[0])
        C = self.vel_effects(state[0], state[1])
        N = self.conservative_effects(state[0])

        accel = (Torque_net - C - N) / M
        
        # accelration happens over the time step
        start_vel = state[1]
        end_vel = state[1] + accel * time_step
        avg_vel = state[1] + accel * time_step / 2

        start_theta = state[0]
        end_theta = state[0] + avg_vel * time_step

        state = np.array([end_theta, end_vel, accel, ext_pres, flx_pres]).flatten()

        return state

    def timeline(self):
        return np.arange(self.TIME_START, self.TIME_END, self.TIME_RESOLUTION)

    def simulate(self, controller, state_start, desired_state):
        time = self.timeline()
        control_resolution = 1.0 / self.CONTROL_RATE
        steps_to_next_ctrl = int(np.ceil(control_resolution / self.TIME_RESOLUTION))
        last_control_time = -9001

        full_state = np.ones((time.shape[0], state_start.shape[0]))
        full_state[0,:] = state_start
        for i in range(full_state.shape[0] - 1):
            if i % 1000 == 0:
                print('...calculating step % 6d / %d' % (i, full_state.shape[0] - 1,))
            this_time = time[i]
            control_should_update = (this_time - last_control_time) > control_resolution
            if control_should_update:
                last_control_time = this_time
                self.last_control = controller.control(
                    state=full_state[i,:],
                    desired_states=desired_state[i:i+steps_to_next_ctrl,:],
                    times=time[i:i+steps_to_next_ctrl])
            new_state = self.motion_evolution(
                state=full_state[i,:],
                time_step=self.TIME_RESOLUTION,
                control=self.last_control,
                control_stiffness=controller.antagonistic_stiffness)
            full_state[i+1,:] = new_state

        return full_state

class Controller(object):
    def __init__(self, control_rate, stiffness, **kwargs):
        # TODO(buckbaskin): this assumes perfect matching parameters for motion model
        self.control_rate = control_rate
        self.sim = Simulator()
        ## "Static" Stiffness ##
        # Increasing the stiffness increases the range around 0 where the complete
        #   desired torque works. On the other hand, decreasing the stiffness increases
        #   the range of total torques that are output before the desired torque
        #   saturates.
        self.antagonistic_stiffness = stiffness

        ## "Dynamic" Stiffness ##
        # Together K_p, K_v constitute "Dynamic" Stiffness
        # Not quite sure how to align static holding mode with dyanmic mode right now.
        self.K_p = 8
        self.K_v = 1

        for arg, val in kwargs.items():
            if hasattr(self, arg):
                setattr(self, arg, val)

    def internal_model(self, state, desired_torque, times):
        '''
        Implement something like motion_evolution for short forward time periods
        based on an internal model. The output from this will be used to pick a
        desired torque to set as the desired control for the next time steps until a
        new control update.
        Complications:
            - [.] Create a parameters object, one for simulation and one internal
            - [ ] Spend some time reducing code duplication. Prep for multi-joint model
            - [ ] Make the motion_evolution function operate from object, collect 
                    parameter arguments
            - [ ] Call the motion evolution repeatedly and build up the states here
            - [ ] Return the states array
        '''
        internal_rotational_inertia = 1

    def control(self, state, desired_states, times):
        '''
        Control Model
        Implements: 
            Formerly: PD Control
            WIP: Chooses a torque/acceleration that best matches desired states at 
                the given times
        Complications:
            - [x] Torque Limits
            - [x] Force Limts -> Torque Limits based on geometry
            - [x] Pressure Limits -> Force Limits -> Torque Limits
            - [x] Control does bang-bang pressure control
            - [x] Control only updates at X Hz
            - [x] Control uses linear time scaling of control rate
            - [ ] Control uses a model to project forward to choose accel/torque
        '''
        desired_state=None

        ### Current State ###
        theta = state[0]
        des_theta = desired_state[-1,0]

        vel = state[1]

        accel = state[2]

        ### PD Control ###
        theta_err = des_theta - theta
        magic_number1 = 115
        theta_torque = (self.K_p * np.min([1, (1 + self.control_rate) / magic_number1])) * theta_err

        theta_dot = state[1]
        des_theta_dot = desired_state[-1,1]

        vel_err = des_theta_dot - theta_dot
        vel_torque = (self.K_v * np.min([1, (1 + self.control_rate) / magic_number1])) * vel_err

        des_torque = theta_torque + vel_torque

        ### Convert Torque to Left and Right Torques ###
        # extension is positive rotation
        ext_torque = des_torque / 2 + self.antagonistic_stiffness
        
        # flexion is negative rotation
        flx_torque = -des_torque / 2 + self.antagonistic_stiffness
        
        # TODO(buckbaskin): I did the math here so clipping had less effect, but I
        #   deleted it
        des_ext_pres = self.sim.ext_torque_to_pressure(ext_torque, state)
        des_ext_pres = np.clip(des_ext_pres, self.sim.PRESSURE_MIN, self.sim.PRESSURE_MAX)

        des_flx_pres = self.sim.flx_torque_to_pressure(flx_torque, state)
        des_flx_pres = np.clip(des_flx_pres, self.sim.PRESSURE_MIN, self.sim.PRESSURE_MAX)

        return des_ext_pres, des_flx_pres, des_torque

if __name__ == '__main__':
    ### Set up time ###
    S = Simulator(bang_bang=False, limit_pressure=False)
    time = S.timeline()

    MAX_AMPLITUDE = S.MAX_AMPLITUDE

    state_start = np.array([
        -MAX_AMPLITUDE / 2, # position
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

    plot_position = True

    if plot_position:
        fig = plt.figure()
        ax_pos = fig.add_subplot(1, 1, 1)
        ax_pos.set_title('Position')
        ax_pos.set_ylabel('Position (% of circle)')
        ax_pos.set_xlabel('Time (sec)')
        ax_pos.plot(time,  desired_state[:,0] / (pi))

    print('calculating...')
    for stiffness in [0.1,]:
        print('stiffness: %.2f' % (stiffness,))
        C = Controller(control_rate=S.CONTROL_RATE, stiffness=stiffness)
        
        full_state = S.simulate(controller=C, state_start=state_start, desired_state=desired_state)

        if plot_position:
            ax_pos.plot(time, full_state[:,0] / (pi))
    if plot_position:
        print('show for the dough')
        plt.show()
        print('all done')
