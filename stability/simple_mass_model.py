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
import datetime
import math
import matplotlib.pyplot as plt
import numpy as np

from functools import partial
from math import pi
from numpy import arctan, sqrt, floor, ceil
from scipy.signal import argrelmax
from scipy.optimize import curve_fit

ERROR_STANDARD = 1 # degree
ERROR_STANDARD = ERROR_STANDARD / 180 * pi # radians
SCORING_DELAY = 750

class BaseSimulator(object):
    MAX_AMPLITUDE = math.pi / 16
    ### Simulation Parameters and Constants ###
    LINK_LENGTH = 0.25 # meters
    LINK_MASS = 0.25 # kg
    ROBOT_MASS = 0.3 # kg

    INTERNAL_DAMPING = 0.1

    JOINT_LIMIT_MAX = pi / 4
    JOINT_LIMIT_MIN = -pi / 4

    TORQUE_MAX = 2.5
    TORQUE_MIN = 0.25

    PRESSURE_MAX = 620
    PRESSURE_MIN = 0

    PRESSURE_RATE_MAX = 1000 # 200 kPa per sec works

    TIME_RESOLUTION = 0.001
    TIME_START = 0
    TIME_END = 10.0

    CONTROL_RATE = 30

    ## Actuator Model Parameters ##

    a0 = 254.3 # kpa
    a1 = 192.0 # kpa
    a2 = 2.0625
    a3 = -0.461
    a4 = -0.331 # 1 / Nm
    a5 = 1.230
    a6 = 15.6 # kpa

    ## Mutual Actuator Parameters ##

    l_rest = .189 # m
    l_620 = round(-((.17 * l_rest) - l_rest), 3)
    k_max = 0.17
    l_max = l_rest
    l_min = l_620

    d = 0.005 # m
    offset = 0.015 # m
    l1 = round(sqrt(d**2 + offset**2), 3)
    l0 = floor((l_max - l1) * 1000.0) / 1000.0

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

    alpha_l = arctan(offset / d) # radians
    beta_l = -pi / 2 # radians, TODO(buckbaskin): assumes that muscle mounted d meters off mount
    beta_l = 0 # for now

    alpha_r = -arctan(offset / d) # radians
    beta_r = pi / 2 # radians, TODO(buckbaskin): assumes that muscle mounted d meters off mount
    beta_r = 0 # for now

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

    def pressures_to_torque(self, extp, flxp, state, actual_torque=None):
        '''
        Inverse model: given the pressures of the left and right actuator, estimate
        the torque on the joint
        '''

        extp = np.clip(extp, self.PRESSURE_MIN, self.PRESSURE_MAX)
        flxp = np.clip(flxp, self.PRESSURE_MIN, self.PRESSURE_MAX)

        ### Calculate errors from guessing torque ###

        base = 0.5
        step = 0.1

        ext_p_0 = self.ext_torque_to_pressure(base - step, state)
        ext_p_1 = self.ext_torque_to_pressure(base, state)
        condition = (ext_p_1 == ext_p_0 or
            (not 0.5 <= ext_p_1 <= 619.5) or
            (not 0.5 <= ext_p_0 <= 619.5))
        for i in range(10): 
            if not condition:
                break
            if ext_p_1 >= 619.5:
                base /= 2
                step /= 2
                if step < 0.01:
                    step = 0.01
            elif ext_p_1 < 0.5:
                base += 0.1
                if step < 0.01:
                    step = 0.01
            else:
                raise ValueError()
            ext_p_0 = self.ext_torque_to_pressure(base - step, state)
            ext_p_1 = self.ext_torque_to_pressure(base, state)

            condition = (ext_p_1 == ext_p_0 or
                (not 0.5 <= ext_p_1 <= 619.5) or
                (not 0.5 <= ext_p_0 <= 619.5))
        
            if condition and i == 9:
                print('Ps_2_T(', extp, flxp, state, ')')
                print('failed to fix the problem.')
                input(('not fixed', base, step, 'got', ext_p_1, ext_p_0))
            if not condition:
                print(('fixed', base, step, 'got', ext_p_1, ext_p_0))

        if ext_p_1 == 0 and ext_p_0 == 0:
            dTdeP = 0
        else:
            dTdeP = (step) / (ext_p_1 - ext_p_0)
        flx_p_0 = self.ext_torque_to_pressure(base - step, state)
        flx_p_1 = self.ext_torque_to_pressure(base, state)
        if flx_p_1 == 0 and flx_p_0 == 0:
            dTdfP = 0
        else:
            dTdfP = (step) / (flx_p_1 - flx_p_0)

        deP = extp - ext_p_1
        deT = dTdeP * deP
        dfP = flxp - flx_p_1
        dfT = dTdfP * dfP
        
        eT0 = 0.5
        eT1 = eT0 + deT
        fT0 = 0.5
        fT1 = fT0 + dfT

        return eT1, fT1

    def mass_model(self, theta):
        '''
        Mass
        '''
        raise NotImplementedError()

    def vel_effects(self, theta, theta_dot):
        '''
        Damping
        '''
        raise NotImplementedError()

    def conservative_effects(self, theta):
        '''
        Gravity
        '''
        raise NotImplementedError()

    def pressure_model(self, des_pressure, current_pressure, time_step):
        '''
        Time Dependent Pressure updates
        '''
        raise NotImplementedError()

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

        ext_torque, flx_torque = self.pressures_to_torque(extp=ext_pres, flxp=flx_pres,
            state=state, actual_torque=None) # intended_torque)

        Torque_net = ext_torque - flx_torque

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

        if end_theta > self.JOINT_LIMIT_MAX:
            end_theta = self.JOINT_LIMIT_MAX
            end_vel = 0
            accel = 0
        if end_theta < self.JOINT_LIMIT_MIN:
            end_theta = self.JOINT_LIMIT_MIN
            end_vel = 0
            accel = 0

        state = np.array([end_theta, end_vel, accel, ext_pres, flx_pres]).flatten()

        return state

    def timeline(self):
        return np.arange(self.TIME_START, self.TIME_END, self.TIME_RESOLUTION)

    def simulate(self, controller, state_start, desired_state):
        time = self.timeline()
        control_resolution = 1.0 / self.CONTROL_RATE
        steps_to_next_ctrl = int(np.ceil(control_resolution / self.TIME_RESOLUTION))
        last_control_time = -9001

        full_state = np.zeros((time.shape[0], state_start.shape[0]))
        c_est_state = np.zeros((time.shape[0], state_start.shape[0]))
        full_state[0,:] = state_start
        c_est_state[0,:] = state_start
        # runs every control
        # sensor_fusion(est_state, last_est_time, current_state, current_time)
        # can run every time step
        # internal_model(state, desired_torque, run_time)

        start_time = datetime.datetime.now()
        controller.inertias.append(controller.sim.inertia)
        controller.dampings.append(controller.sim.damping)
        controller.cons.append(controller.sim.conservative)

        for i in range(full_state.shape[0] - 1):
            if i % 1000 == 1 or i == (full_state.shape[0] - 2):
                print('...calculating step % 6d / %d' % (i, full_state.shape[0],))
                print('estimated', controller.sim)
            this_time = time[i]
            control_should_update = (this_time - last_control_time) > control_resolution
            if control_should_update:
                self.last_control = controller.control(
                    state=full_state[i,:],
                    desired_states=desired_state[i:i+2*steps_to_next_ctrl,:],
                    times=time[i:i+2*steps_to_next_ctrl])

            controller.inertias.append(controller.sim.inertia)
            controller.dampings.append(controller.sim.damping)
            controller.cons.append(controller.sim.conservative)

            new_state = self.motion_evolution(
                state=full_state[i,:],
                time_step=self.TIME_RESOLUTION,
                control=self.last_control,
                control_stiffness=controller.antagonistic_stiffness)
            full_state[i+1,:] = new_state
            c_est_state[i+1,:] = c_est_state[i,:]
            if control_should_update:
                new_est_state = controller.sensor_fusion(
                    c_est_state[i,:],
                    last_control_time,
                    c_est_state[i-1,0],
                    full_state[i,:],
                    this_time)
                c_est_state[i+1,:] = new_est_state
                last_control_time = this_time

        end_time = datetime.datetime.now()
        sim_time = (end_time - start_time).total_seconds()
        simulated_time = time[-1] - time[0]

        realtime = min(1.0, simulated_time / sim_time)
        print('runtime is: %.2f seconds for %.2f of real time (%.2f percent of rt)' % (sim_time, simulated_time, realtime,))

        return full_state, c_est_state

    def evaluation(self, states, desired_states, times,
        amplitude=None, frequency=None, phase=None, delay=None):
        '''
        Evaluate position error and antagonistic torque (wasted effort)

        Tracking performance has a strict bound (staying within a certain error)
        and a score to minimize (pos_error_rate). Antagonistic torques focus is
        minimizing the antag_torque_rate. A momentarily high antagonistic torque
        maybe useful and allowed, but continued unnecessarily high antagonism is
        wasteful.
        '''
        if delay is None:
            delay = SCORING_DELAY

        pos_error = np.abs(desired_states[:,0] - states[:,0])
        pos_error_rate = np.sum(pos_error) / (times[-1] - times[0])
        max_pos_error = np.max(pos_error[SCORING_DELAY:]) # ignore the first bit of time

        extp = states[:,3]
        flxp = states[:,4]
        ext_torques = np.zeros(extp.shape)
        flx_torques = np.zeros(flxp.shape)
        for i in range(len(extp)):
            ext_torque, flx_torque = self.pressures_to_torque(extp[i], flxp[i], states[i,:])
            ext_torques[i] = ext_torque
            flx_torques[i] = flx_torque
        antag_torque = np.abs(ext_torques) + np.abs(flx_torques)
        antag_torque_rate = np.sum(antag_torque) / (times[-1] - times[0])
        max_antag_torque = np.max(antag_torque)

        delts = []
        # estimate difference in phase
        for i in range(delay, len(times)-1):
            if (desired_states[i-1,0] <= desired_states[i,0] and
                desired_states[i+1,0] <= desired_states[i,0]):
                print('found des local max %d' % (i,))
                for j in range(i, len(times)-1):
                    if (desired_states[j-1,0] <= desired_states[j,0] and
                        desired_states[j+1,0] <= desired_states[j,0]):
                        if j > i:
                            print('found a new des max first %d' % (j,))
                            break
                    if ((states[j-1,0] <= states[j,0] and states[j+1,0] < states[j,0]) or 
                        (states[j-1,0] < states[j,0] and states[j+1,0] <= states[j,0])):
                        print('found est max %d' % (j,))
                        # difference in time between two maximums
                        delta_t = times[j] - times[i]
                        delts.append(delta_t)
                        break

        # assuming a similar frequency, avg time delta is an ok estimate of phase
        if len(delts) > 0:
            phase_est = np.mean(delts)
        else:
            phase_est = 0.0

        return {
            'max_pos_error': max_pos_error,
            'pos_error_rate': pos_error_rate,
            'max_antag_torque': max_antag_torque,
            'antag_torque_rate': antag_torque_rate,
            'phase_offset': phase_est,
        }


class ActualSimulator(BaseSimulator):
    def __init__(self, bang_bang=True, limit_pressure=True, **kwargs):
        '''
        Set defaults, and override extras with kwargs
        '''
        self.bang_bang = bang_bang
        self.limit_pressure = limit_pressure
        self.last_control = (0.0, 0.0, 0.0,)
        self.PRESSURE_RESOLUTION = 17.0 # hysterisis gap, # 17 works

        for arg, val in kwargs.items():
            if hasattr(self, arg):
                setattr(self, arg, val)
            else:
                raise ValueError('%s does not have attribute %s' % (self, arg,))

    def __str__(self):
        R = self.LINK_LENGTH / 2
        M = self.LINK_MASS * (R**2)

        C = self.INTERNAL_DAMPING

        g = 9.81
        M_l = self.LINK_MASS
        F_g = M_l * g
        R_g = self.LINK_LENGTH / 2

        M_r = self.ROBOT_MASS
        F_r = M_r * g
        R_n = self.LINK_LENGTH
        N = (F_g * R_g - F_r * R_n) / (self.LINK_LENGTH)

        return 'ActualSimulator(M=%.4f, C=%.4f, N=%.4f)' % (M, C, N,)

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
        return self.INTERNAL_DAMPING * theta_dot

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

class SimpleSimulator(BaseSimulator):
    def __init__(self, M, C, N, **kwargs):
        self.inertia = M
        self.damping = C
        self.conservative = N

        self.bang_bang = True
        self.limit_pressure = True
        self.PRESSURE_RESOLUTION = 17.0

        self.DAMPING_MIN = 0.001
        self.DAMPING_MAX = 0.25

        self.CONSERVATIVE_MIN = -3
        self.CONSERVATIVE_MAX = 3

        self.INERTIA_MIN = 0.0001
        self.INERTIA_MAX = 0.0050

        for arg, val in kwargs.items():
            if hasattr(self, arg):
                setattr(self, arg, val)

    def __str__(self):
        return 'SimpleSimulator(M=%.4f, C=%.4f, N=%.4f)' % (self.inertia,
            self.damping, self.conservative,)

    def set(self, **kwargs):
        M = None
        C = None
        N = None
        for arg, val in kwargs.items():
            if arg == 'M':
                pass
                # self.inertia = np.clip(val, self.INERTIA_MIN, self.INERTIA_MAX)
            if arg == 'C':
                # pass
                self.damping = np.clip(val, self.DAMPING_MIN, self.DAMPING_MAX)
            if arg == 'N':
                self.conservative = np.clip(val, self.CONSERVATIVE_MIN, self.CONSERVATIVE_MAX)

    def mass_model(self, theta):
        '''
        Returns the rotational inertia of the link being controlled
        '''
        return self.inertia

    def vel_effects(self, theta, theta_dot):
        '''
        Damping/Velocity based effects on the system
        '''
        return self.damping * theta_dot

    def conservative_effects(self, theta):
        '''
        Simplified conservative force model. One net positive or negative force
        acting at the end of the link vertically
        '''
        R_g = self.LINK_LENGTH
        link_gravity = self.conservative * R_g * math.sin(theta)
        return link_gravity

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

class BaselineController(object):
    def __init__(self, control_rate, stiffness, **kwargs):
        # TODO(buckbaskin): this assumes perfect matching parameters for motion model
        self.control_rate = control_rate
        self.sim = ActualSimulator()
        ## "Static" Stiffness ##
        # Increasing the stiffness increases the range around 0 where the complete
        #   desired torque works. On the other hand, decreasing the stiffness increases
        #   the range of total torques that are output before the desired torque
        #   saturates.
        self.antagonistic_stiffness = stiffness

        ## "Dynamic" Stiffness ##
        # Together K_p, K_v constitute "Dynamic" Stiffness
        # Not quite sure how to align static holding mode with dyanmic mode right now.
        self.K_p = 20
        self.K_v = 2

        for arg, val in kwargs.items():
            if hasattr(self, arg):
                setattr(self, arg, val)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return 'BaselineController(K_p=%.2f, K_v=%.2f)' % (self.K_p, self.K_v)

    def _pick_proportional_torque(self, state, desired_states, times):
        theta = state[0]
        des_theta = desired_states[0, 0]
        theta_dot = state[1]
        des_theta_dot = desired_states[0, 1]

        # vel = state[1]

        # accel = state[2]

        ### PD Control ###
        magic_number1 = 115

        theta_err = des_theta - theta
        theta_torque = (self.K_p * np.min([1, (1 + self.control_rate) / magic_number1])) * theta_err

        vel_err = des_theta_dot - theta_dot
        vel_torque = (self.K_v * np.min([1, (1 + self.control_rate) / magic_number1])) * vel_err

        des_torque = theta_torque + vel_torque
        return des_torque

    def _convert_to_pressure(self, des_torque, state):

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

        return des_ext_pres, des_flx_pres

    def control(self, state, desired_states, times):
        '''
        Control Model
        Implements: (see _pick_torque)
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

        des_torque = self._pick_proportional_torque(state, desired_states, times)
        des_ext_pres, des_flx_pres = self._convert_to_pressure(des_torque, state)

        return des_ext_pres, des_flx_pres, des_torque

class OptimizingController(object):
    def __init__(self, init_state, init_time, sim,
        control_rate, time_horizon, stiffness,
        optimization_steps=10, iteration_steps=10, **kwargs):
        # TODO(buckbaskin): this assumes perfect matching parameters for motion model
        self.control_rate = control_rate
        self.sim = sim
        self.antagonistic_stiffness = stiffness

        self.time_horizon = time_horizon
        self.iterations = iteration_steps
        self.optimization_steps = optimization_steps
        self.last_control = 0.0
        self.est_state = init_state.copy()
        self.last_est_time = init_time
        self.lag_pos = 0

        self.inertias = []
        self.dampings = []
        self.cons = []
        for arg, val in kwargs.items():
            if hasattr(self, arg):
                setattr(self, arg, val)

        self.counter = 0
        self.accel_gains = []
        self.vel_gains = []

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return 'OptimizingController()'

    def internal_model(self, state, desired_torque, end_time):
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
        times = np.linspace(0, end_time, self.iterations)
        des_ext_pres, des_flx_pres = self._convert_to_pressure(desired_torque, state)
        # print('des_ext_pres', des_ext_pres, 'des_flx_pres', des_flx_pres)
        full_state = np.zeros((times.shape[0], state.shape[0],))
        full_state[0,:] = state
        for i in range(len(times) - 1):
            new_state = self.sim.motion_evolution(
                state=full_state[i,:],
                time_step=self.sim.TIME_RESOLUTION,
                control=(des_ext_pres, des_flx_pres, desired_torque,),
                control_stiffness=self.antagonistic_stiffness)
            full_state[i+1,:] = new_state

        if False and (desired_torque > 0.1 or desired_torque < -0.1):
            delta_vel = full_state[-1, 1] - state[1]
            accel_gain = delta_vel / desired_torque
            self.accel_gains.append(accel_gain)
            delta_pos = full_state[-1, 0] - state[0]
            vel_mod = state[0] + desired_torque * accel_gain
            vel_gain = delta_pos / vel_mod
            self.vel_gains.append(vel_gain)
            self.counter += 1
            if self.counter > 3000:
                print('ag', np.mean(self.accel_gains))
                print('vg', np.mean(self.vel_gains))
                1/0

        return full_state

    def _pick_torque(self, state, desired_states, times):
        desired_state=None # clear polluting global scope

        ### Current State ###
        theta = state[0]
        vel = state[1]
        accel = state[2]

        ### Optimizing Control ###
        max_torque = 2.25
        mid_torque = 0.0
        min_torque = -2.25
        
        desired_end_pos = desired_states[-1,0]
        max_traj = self.internal_model(state, max_torque, self.time_horizon)
        min_traj = self.internal_model(state, min_torque, self.time_horizon)


        for i in range(self.optimization_steps):
            mid_traj = self.internal_model(state, mid_torque, self.time_horizon)
            max_pos = max_traj[-1,0]
            mid_pos = mid_traj[-1,0]
            min_pos = min_traj[-1,0]

            if desired_end_pos >= max_pos:
                return max_torque
            elif desired_end_pos <= min_pos:
                return min_torque
            elif desired_end_pos == mid_pos:
                return mid_torque
            
            if desired_end_pos > mid_traj[-1,0]:
                max_torque = max_torque
                min_torque = mid_torque
                min_traj = mid_traj.copy()
                mid_torque = (max_torque + min_torque) / 2.0

            else: # desired_end_pos < mid_traj[-1,0]:
                max_torque = mid_torque
                max_traj = mid_traj.copy()
                min_torque = min_torque
                mid_torque = (max_torque + min_torque) / 2.0

        return mid_torque

    def _convert_to_pressure(self, des_torque, state):

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

        return des_ext_pres, des_flx_pres

    def sensor_readings(self, state):
        '''
        The robot has rotation sensors on the joints (position) and pressure
        sensors for each actuator.
        '''
        new_state = state.copy()
        new_state[1] = 0 # zero out velocity
        new_state[2] = 0 # zero out acceleration
        return new_state

    def sensor_fusion(self, est_state, last_est_time, lag_pos, current_state, current_time):
        '''
        Based on the last estimated state and sensor readings of the current
        state, estimate the current state before picking torques
        '''
        delta_t = current_time - last_est_time
        start_pos = est_state[0]
        start_vel = est_state[1]
        start_acc = est_state[2]
        start_extp = est_state[3]
        start_flxp = est_state[4]

        sensed = self.sensor_readings(current_state)

        mes_pos = sensed[0]
        mes_extp = sensed[3]
        mes_flxp = sensed[4]

        if delta_t < 0.00001:
            avg_vel = start_vel
            end_vel = start_vel
            avg_acc = start_acc
        else:
            avg_vel = (mes_pos - lag_pos) / (2 * delta_t)
            avg_acc = (mes_pos - 2 * start_pos + lag_pos) / (delta_t * delta_t)
            end_vel = avg_vel + (avg_acc * delta_t / 2)

        est_state[0] = mes_pos
        est_state[1] = end_vel
        est_state[2] = avg_acc
        est_state[3] = mes_extp
        est_state[4] = mes_flxp

        return est_state

    def update_parameters(self, last_state, last_time, current_state,
        current_time, inertia, damping, conservative):
        '''
        TODO(buckbaskin):
            - [x] Damping Estimation
            - [x] Load Estimation
            - [ ] ~~Mass estimation~~
            - [.] Update all values as a combined gradient
            - [ ] Non-dimensionalize it to stay within the stable range. Estimate
                all values to fall in a 0-1 range, where 0 is the minimum stable
                value and 1 is the maximum stable value.
        '''

        delta_t = current_time - last_time
        if delta_t <= 0.0:
            return inertia, damping, conservative
        acc_actual = (current_state[1] - last_state[1]) / delta_t

        acc_est = self.internal_model(
            last_state,
            self.last_control,
            current_time - last_time)[-1, 2]
        acc_err = acc_actual - acc_est

        vel_avg = (current_state[1] + last_state[1]) / 2

        if vel_avg != 0:
            C_err = acc_err * (inertia / vel_avg)
        else:
            C_err = 0 # can't update if there wasn't a velocity

        theta_avg = (current_state[0] + current_state[1])/2.0
        base = self.sim.LINK_LENGTH * math.sin(theta_avg)
        if base != 0:
            N_err = acc_err * (inertia / base)
        else:
            N_err = 0

        ext_t, flx_t = self.sim.pressures_to_torque(last_state[3], last_state[4], last_state)
        torque = ext_t - flx_t
        M_err = acc_err * (torque
            - damping * vel_avg
            - conservative * (
                (self.sim.LINK_LENGTH * math.sin(theta_avg))) *
                (inertia**-2))

        # prefer underestimation
        update_rate = 1.004
        if C_err > 0:
            damping *= update_rate
        else:
            damping /= update_rate
        if N_err > 0:
            conservative *= update_rate
        else:
            conservative /= update_rate

        return inertia, damping, conservative

    def control(self, state, desired_states, times):
        '''
        Control Model
        Implements: (see _pick_torque)
            Chooses a torque/acceleration that best matches desired states at 
                the given times
        Complications:
            - [x] Torque Limits
            - [x] Force Limts -> Torque Limits based on geometry
            - [x] Pressure Limits -> Force Limits -> Torque Limits
            - [x] Control does bang-bang pressure control
            - [x] Control only updates at X Hz
            - [x] Control uses linear time scaling of control rate
            - [x] Control uses a model to project forward to choose accel/torque
            - [.] Estimate state because sensors only read pressure, position
        '''
        old_state = self.est_state.copy()
        self.est_state = self.sensor_fusion(self.est_state, self.last_est_time,
            self.lag_pos, state, times[0])
        new_state = self.est_state.copy()

        _M, _C, _N = self.update_parameters(
            old_state, self.last_est_time, 
            new_state, times[0],
            self.sim.inertia, self.sim.damping, self.sim.conservative)

        self.sim.set(M=_M, C=_C, N=_N)

        self.last_est_time = times[0]
        self.lag_pos = self.est_state[0]

        des_torque = self._pick_torque(self.est_state, desired_states, times)
        des_ext_pres, des_flx_pres = self._convert_to_pressure(des_torque, state)

        self.last_control = des_torque

        return des_ext_pres, des_flx_pres, des_torque

if __name__ == '__main__':
    import sys
    print('--- %s ---' % (sys.argv[0],))

    ### Set up time ###
    S = ActualSimulator(bang_bang=True, limit_pressure=True)
    print('actual', S)
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
        fig = plt.figure(figsize=(6.5,7.5,), dpi=300)
        ax_pos = fig.add_subplot(3, 1, 1)
        titlte = 'Estimated vs Actual %s'
        if plt_index == 0:
            titlte = titlte % 'Position'
        if plt_index == 1:
            titlte = titlte % 'Velocity'
        if plt_index == 2:
            titlte = titlte % 'Acceleration'
        ax_pos.set_title(titlte)
        ax_pos.set_ylabel('PVA')
        ax_pos.set_xlabel('Time (sec)')
        ax_pos.plot(time,  desired_state[:,plt_index], 
            color='tab:blue', label='Desired')
        if plt_index == 0:
            ax_pos.plot(time[SCORING_DELAY:], desired_state[SCORING_DELAY:,plt_index] + ERROR_STANDARD,
                color='tab:purple', label='MAXIMUM')
            ax_pos.plot(time[SCORING_DELAY:], desired_state[SCORING_DELAY:,plt_index] - ERROR_STANDARD,
                color='tab:purple', label='MINIMUM')
        
    print('calculating...')
    stiffness = 1.0
    for index, _ in enumerate([0.0]):
        # Actual is M=0.25, C=0.1, N=-1.7
        estimated_S = SimpleSimulator(M=0.0010, C=0.11, N=-1.8000)
        print('internal', estimated_S)
    
        C = OptimizingController(state_start, time[0],
            sim = estimated_S, control_rate=S.CONTROL_RATE,
            time_horizon=1.5/S.CONTROL_RATE, stiffness=stiffness,
            optimization_steps=15, iteration_steps=45)

        full_state, est_state = S.simulate(controller=C, state_start=state_start, desired_state=desired_state)

        result = S.evaluation(full_state, desired_state, S.timeline())
        print('Simulation Evaluation:')
        print('Controller: %s' % (str(C),))
        print('Maximum Positional Error: %.3f (rad)' % (result['max_pos_error']))
        if abs(result['max_pos_error']) > ERROR_STANDARD:
            print('Maximum Positional Error: Failed Standard')
        print('Torque Score: %.3f (total Nm/sec)' % (result['antag_torque_rate']))

        if plot_position:
            ax_pos.plot(time, full_state[:,plt_index],
                color='tab:orange', label='Actual State')
            ax_pos.plot(time, est_state[:,plt_index],
                color='tab:green', label='Internal Est. State')
    if plot_position:
        # ax_inertia = fig.add_subplot(4, 1, 2)
        # ax_inertia.plot(time, np.array(C.inertias))
        # ax_inertia.set_ylabel('Inertia')
        # ax_inertia.set_xlabel('Time (sec)')
        ax_damping = fig.add_subplot(3, 1, 2)
        ax_damping.plot(time, np.array(C.dampings))
        ax_damping.set_ylabel('Damping Factor')
        # ax_damping.set_xlabel('Time (sec)')
        ax_cons = fig.add_subplot(3, 1, 3)
        ax_cons.plot(time, np.array(C.cons))
        ax_cons.set_ylabel('Load Factor')
        # ax_cons.set_xlabel('Time (sec)')
        ax_pos.legend()
        print('show for the dough')
        plt.savefig('State_Model_SimpleUpdate.png')
        plt.show()
        print('all done')
