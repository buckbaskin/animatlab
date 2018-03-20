'''
Build a single joint dynamic model, 2 different Festos, negative feedback based 
on  pressure/position curves. This is a numerical model where everything happens 
nicely.

M(\theta) \ddot{\theta} + C(\theta, \dot{\theta}) \dot{\theta} + N(\theta) \theta
= Torque

Control:
PD
Torque_{des} = -K_v \dot{\theta} + -K_p \theta
Convert to T_r, T_l
~~Calculate Pressures~~

For now, assume that the pressures just work, eventually clipping pressure,
so just torque works

Mass Model:
Joint is hung vertically for now
M: A point mass at a distance from the joint
C: ? Might come in when multiple joints come together
N: gravity on the point mass at a distance

Calculate forces on joint (mass accerleration, gravity) and torque from outside 
forces
Tracking forces on joint is just nice, torque is the N term

Notes:
- Pushing Stiffness too high causes clipping for the primary actuator, so less 
    net torque is achieved and decreased line following is achieved
'''
import sys
print('--- %s ---' % (sys.argv[0],))

import math
import numpy as np
import matplotlib.pyplot as plt

from math import pi
from numpy import arctan, sqrt, floor, ceil

LINK_LENGTH = 0.25 # meters
LINK_MASS = 0.25 # kg
ROBOT_MASS = 0.6 # kg

MAX_AMPLITUDE = math.pi / 16

# "Static" Stiffness
# So, increasing the stiffness increases the range around 0 where the complete
#   desired torque works. On the other hand, decreasing the stiffness increases
#   the range of total torques that are output before the desired torque
#   saturates.
antagonistic_stiffness = 0.1

# Together K_p, K_v constitute "Dynamic" Stiffness
# Not quite sure how to align static holding mode with dyanmic mode right now.
K_p = 8
K_v = 1
control_matrix = np.matrix([[-K_p, -K_v, 0]])

hidden_state_start = np.array([0, 0]) # pressures of actuators
state_start = np.array([-MAX_AMPLITUDE / 2, 0, 0]) # position, vel, accel

TORQUE_MAX = 5.0
TORQUE_MIN = 0.0

PRESSURE_MAX = 620
PRESSURE_MIN = 0

PRESSURE_RATE_MAX = 200 # kPa per sec

# Simplified Proxy for bang-bang control of pressure 
PRESSURE_RESOLUTION = 17.0 # hysterisis gap

time_resolution = 0.001
time_start = 0
time_end = 10

control_resolution = 0.022
last_control = (0.0, 0.0)

### Model Parameters ###

a0 = 254.3 # kpa
a1 = 192.0 # kpa
a2 = 2.0625
a3 = -0.461
a4 = -0.331 # 1 / Nm
a5 = 1.230
a6 = 15.6 # kpa

### Mutual Actuator Parameters ### 

l_rest = .189 # m
l_620 = round(-((.17 * l_rest) - l_rest), 3)
k_max = 0.17
l_max = l_rest
l_min = l_620

d = 0.005 # m
offset = 0.015 # m
l1 = round(sqrt(d**2 + offset**2), 3)
l0 = floor((l_max - l1) * 1000.0) / 1000.0

### Specific Actuator Parameters ###
# Actuator L is the negative actuator, Actuator R is the positive actuator
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


def flx_torque_to_pressure(torque, state):
    T = torque
    A = state[0]
    F = T / (d * np.cos(beta_l + A))
    # print('pressurel:T', T)
    # print('pressurel:A', A)
    # print('pressurel:F', F)
    L_angle = l0 + l1 * np.cos(alpha_l + A)
    K = (l_rest - L_angle) / l_rest
    assert np.all(0 <= K) and np.all(K <= 1)
    P = a0 + a1 * np.tan(a2 * (K / (a4 * F + k_max)+ a3)) + a5 * F # kpa
    return np.clip(P, PRESSURE_MIN, PRESSURE_MAX)

def ext_torque_to_pressure(torque, state):
    T = torque
    A = state[0]
    F = T / (d * np.cos(beta_r + A))
    # print('pressurer:T', T)
    # print('pressurer:A', A)
    # print('pressurer:F', F)
    L_angle = l0 + l1 * np.cos(alpha_r + A)
    K = (l_rest - L_angle) / l_rest
    assert np.all(0 <= K) and np.all(K <= 1)
    P = a0 + a1 * np.tan(a2 * (K / (a4 * F + k_max)+ a3)) + a5 * F # kpa
    return np.clip(P, PRESSURE_MIN, PRESSURE_MAX)

def control(state, desired_state, stiffness):
    '''
    Control Model
    Implements: PD Control
    Complications:
        - [x] Torque Limits
        - [x] Force Limts -> Torque Limits based on geometry
        - [x] Pressure Limits -> Force Limits -> Torque Limits
        - [x] Control does bang-bang pressure control
        - [ ] Control only updates at X Hz

    # Use numerical derivative of Torque and Theta for computed pressure to adjust 
    #   torque
    '''

    ### Current State ###
    theta = state[0]
    des_theta = desired_state[0]

    ### PD Control ###
    theta_err = des_theta - theta
    theta_torque = K_p * theta_err

    theta_dot = state[1]
    des_theta_dot = desired_state[1]

    vel_err = des_theta_dot - theta_dot
    vel_torque = K_v * vel_err

    des_torque = theta_torque + vel_torque

    ### Convert Torque to Left and Right Torques ###
    # extension is positive rotation
    ext_torque = des_torque / 2 + antagonistic_stiffness
    
    # flexion is negative rotation
    flx_torque = -des_torque / 2 + antagonistic_stiffness
    
    '''
    # Torque correction that doesn't work (as implemented) in the pressure-torque world

    current_net = ext_torque - flx_torque
    err = des_torque - current_net
    pos_err = np.clip(err, 0, None)
    neg_err = np.clip(err, None, 0)

    ext_torque += pos_err
    ext_torque = np.clip(ext_torque, TORQUE_MIN, TORQUE_MAX)
    flx_torque += -neg_err
    flx_torque = np.clip(flx_torque, TORQUE_MIN, TORQUE_MAX)
    '''

    # TODO(buckbaskin): I did the math here so clipping had less effect, but I
    #   deleted it
    des_ext_pres = ext_torque_to_pressure(ext_torque, state)
    des_ext_pres = np.clip(des_ext_pres, PRESSURE_MIN, PRESSURE_MAX)

    des_flx_pres = flx_torque_to_pressure(flx_torque, state)
    des_flx_pres = np.clip(des_flx_pres, PRESSURE_MIN, PRESSURE_MAX)

    return des_ext_pres, des_flx_pres, des_torque

def pressures_to_torque(extp, flxp, state, stiffness, actual_torque=None):
    '''
    Inverse model: given the pressures of the left and right actuator, estimate
    the torque on the joint
    Complications:
        - [x] Linear search through torque
        - [ ] Search through torque for speedup
    '''
    
    ### Calculate errors from guessing torque ###

    # TODO(buckbaskin): this is slow
    maximum_torque = np.max([np.abs(TORQUE_MAX), np.abs(TORQUE_MIN)])    
    torque_guesses = np.arange(-maximum_torque, maximum_torque, 0.05)
    ext_guess = torque_guesses / 2 + stiffness
    flx_guess = -torque_guesses / 2 + stiffness

    extp_guesses = ext_torque_to_pressure(ext_guess, state)
    extp_guesses = np.clip(extp_guesses, PRESSURE_MIN, PRESSURE_MAX)
    flxp_guesses = flx_torque_to_pressure(flx_guess, state)
    flxp_guesses = np.clip(flxp_guesses, PRESSURE_MIN, PRESSURE_MAX)

    extp_err = np.abs(extp_guesses - extp)
    flxp_err = np.abs(flxp_guesses - flxp)

    total_err = extp_err + flxp_err
    best_guess = torque_guesses[np.argmin(total_err)]

    if actual_torque is not None:
        print('attempted', actual_torque, 'actual', best_guess)
    return best_guess

def mass_model(theta):
    '''
    Mass Model
    ma -> I theta_ddot

    Implements: mass at a rigid point half of link length
    Complications:
        - [ ] Uniform mass distribution on the link
    '''
    M = LINK_MASS
    R = LINK_LENGTH / 2
    return M * (R**2)

def vel_effects(theta, theta_dot):
    '''
    Damping/Velocity based effects on the system
    Complications:
        - [ ] Small damping from flexing of actuators based on change in length
        - [ ] Estimated Hysterisis effect of filling or empty actuators applying
                a torque opposite the motion
    '''
    return 0.1 * theta_dot

def conservative_effects(theta):
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
    M_l = LINK_MASS
    F_g = M_l * g
    R_g = LINK_LENGTH / 2

    # this assumes that the robot mass is solely balanced on top of the robot
    M_r = ROBOT_MASS
    F_r = M_r * g
    R_n = LINK_LENGTH

    try:
        link_gravity = F_g * R_g * math.sin(theta)
    except ValueError:
        print(type(theta))
        print(theta)
        raise
    normal_force = - F_r * R_n * math.sin(theta)

    return link_gravity + normal_force

def pressure_model(des_pressure, current_pressure, time_step):
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
    #   near side of the bang-bang window (close enough). This ignores filling
    #   rate and pressure differential from the air supply to the actuator.
    if np.abs(des_pressure - current_pressure) < PRESSURE_RESOLUTION:
        return current_pressure
    elif des_pressure > current_pressure:
        return np.min([des_pressure - PRESSURE_RESOLUTION,
            current_pressure + PRESSURE_RATE_MAX * time_step])
    else: # des_pressure < current_pressure
        return np.max([des_pressure + PRESSURE_RESOLUTION,
            current_pressure - PRESSURE_RATE_MAX * time_step])

def motion_evolution(state, desired_state, hidden_state,
    stiffness, time_step, last_control, control_active):
    '''
    M * ddot theta + C * dot theta + N * theta = torque
    ddot theta = 1 / M * (torque - C * dot theta - N) 
    '''
    ext_pres = hidden_state[0]
    flx_pres = hidden_state[1]

    if control_active:
        des_ext_pres, des_flx_pres, intended_torque = control(state, desired_state, stiffness)
    else:
        des_ext_pres, des_flx_pres, intended_torque = last_control

    ext_pres = pressure_model(des_ext_pres, ext_pres, time_step)
    flx_pres = pressure_model(des_flx_pres, flx_pres, time_step)

    Torque_net = pressures_to_torque(ext_pres, flx_pres, state, stiffness,
        actual_torque=None)

    M = mass_model(state[0])
    C = vel_effects(state[0], state[1])
    N = conservative_effects(state[0])

    accel = (Torque_net - C - N) / M
    
    # accelration happens over the time step
    start_vel = state[1]
    end_vel = state[1] + accel * time_step
    avg_vel = state[1] + accel * time_step / 2

    start_theta = state[0]
    end_theta = state[0] + avg_vel * time_step

    state = np.array([end_theta, end_vel, accel]).flatten()
    hidden_state = np.array([ext_pres, flx_pres]).flatten()
    last_control = (des_ext_pres, des_flx_pres, intended_torque,)

    return state, hidden_state, last_control


if __name__ == '__main__':
    ### Set up time ###
    time = np.arange(time_start, time_end, time_resolution)

    ### Set up desired state ###
    # the desired state velocity and acceleration are positive here
    desired_state = np.ones((time.shape[0], state_start.shape[0],)) * MAX_AMPLITUDE
    # so set desired velocity to 0
    desired_state[:,1] = 0
    desired_state[:,2] = 0

    # # add an in place step change to the other joint angle
    # desired_state[len(time)//4:len(time)//2,0] *= -0.5
    # desired_state[len(time)//2:3*len(time)//4,0] *= 0.5
    # desired_state[3*len(time)//4:,0] *= -1

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
        ### Set up Hidden State ###
        hidden_state = np.zeros((time.shape[0], hidden_state_start.shape[0]))
        hidden_state[0,:] = hidden_state_start

        ### Set up State ###
        state = np.ones((time.shape[0], state_start.shape[0]))
        state[0,:] = state_start
        for i in range(state.shape[0] - 1):
            if i % 1000 == 0:
                print('...calculating step % 6d / %d' % (i, state.shape[0] - 1,))
            new_state, new_hidden_state, last_control = motion_evolution(
                state=state[i,:],
                desired_state=desired_state[i+1,:],
                hidden_state=hidden_state[i,:],
                stiffness=stiffness,
                time_step=time_resolution,
                last_control=last_control,
                control_active=True)
            state[i+1,:] = new_state
            hidden_state[i+1,:] = new_hidden_state

        if plot_position:
            ax_pos.plot(time, state[:,0] / (pi))
            print('show for the dough')
            plt.show()
            print('all done')
