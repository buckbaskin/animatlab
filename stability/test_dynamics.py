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
print('--- test_dynamics.py ---')
import math
import numpy as np
import matplotlib.pyplot as plt

from math import pi

LINK_LENGTH = 0.25 # meters
LINK_MASS = 0.25 # kg
ROBOT_MASS = 0.6 # kg

MAX_AMPLITUDE = math.pi / 16

# Static Stiffness
stiffness = 0

# Together K_p, K_v constitute "dynamic stiffness"
# Not quite sure how to align static holding mode with dyanmic mode right now.
K_p = 8
K_v = 1
control_matrix = np.matrix([[-K_p, -K_v, 0]])


start_state = np.array([-MAX_AMPLITUDE / 2, 0, 0])

MAX_TORQUE = 10.0
MIN_TORQUE = -10.0

time_resolution = 0.001
time_start = 0
time_end = 60

# control_rate = 0.0
control_resolution = 0.022
controlled_torque = 0.0

def control(state, desired_state, stiffness):
    theta = state[0]
    des_theta = desired_state[0]

    theta_err = des_theta - theta
    theta_torque = K_p * theta_err

    theta_dot = state[1]
    des_theta_dot = desired_state[1]

    vel_err = des_theta_dot - theta_dot
    vel_torque = K_v * vel_err

    des_torque = theta_torque + vel_torque

    req_torque = np.clip(des_torque, MIN_TORQUE, MAX_TORQUE)

    return req_torque

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

def motion_evolution(state, desired_state, stiffness, time_step,
    last_control, control_active):
    '''
    M * ddot theta + C * dot theta + N * theta = torque
    ddot theta = 1 / M * (torque - C * dot theta - N) 
    '''
    if control_active:
        net_Torque = control(state, desired_state, stiffness)
    else:
        net_Torque = last_control

    M = mass_model(state[0])
    C = vel_effects(state[0], state[1])
    N = conservative_effects(state[0])

    accel = (net_Torque - C - N) / M
    
    # accelration happens over the time step
    start_vel = state[1]
    end_vel = state[1] + accel * time_step
    avg_vel = state[1] + accel * time_step / 2

    start_theta = state[0]
    end_theta = state[0] + avg_vel * time_step

    return np.array([end_theta, end_vel, accel]).flatten(), net_Torque


if __name__ == '__main__':
    time = np.arange(time_start, time_end, time_resolution)

    # the desired state velocity and acceleration are positive here
    desired_state = np.ones((time.shape[0], start_state.shape[0],)) * MAX_AMPLITUDE
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

    fig = plt.figure()
    ax_pos = fig.add_subplot(1, 1, 1)
    ax_pos.set_title('Position')
    ax_pos.plot(time,  desired_state[:,0] / math.pi)

    print('calculating...')
    for stiffness in [0.0,]:
        state = np.ones((time.shape[0], start_state.shape[0]))
        state[0,:] = start_state
        for i in range(state.shape[0] - 1):
            new_state, controlled_torque = motion_evolution(
                state[i,:],
                desired_state[i+1,:],
                stiffness,
                time_resolution,
                controlled_torque,
                control_active=True)
            # while new_state[0] > math.pi:
            #     new_state[0] -= 2 * math.pi
            # while new_state[0] < math.pi:
            #     new_state += 2 * math.pi
            state[i+1,:] = new_state
        ax_pos.plot(time, state[:,0] / math.pi)

        # delta = state - desired_state

        # ax_tor = fig.add_subplot(2, 1, 2)
        # ax_tor.set_title('Torque Components')
        # ax_tor.plot(time, T)
        # ax_tor.plot(time, - K_p * (delta[:,0]))
        # ax_tor.plot(time, - K_v * (delta[:,1]))
        
        print('show for the dough')
        plt.show()
        print('all done')