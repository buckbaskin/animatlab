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
print('--- dynamic_model.py ---')
import math
import numpy as np
import matplotlib.pyplot as plt

LINK_LENGTH = 0.5 # meters
LINK_MASS = 0.25 # kg
ROBOT_MASS = 0.3 # kg

MAX_AMPLITUDE = math.pi / 16

K_p = 1.6
K_v = 2.4
control_matrix = np.matrix([[-K_p, -K_v, 0]])

MAX_TORQUE = 3
MIN_TORQUE = -1.0

def control(state, desired_state, stiffness):
    '''
    Control Model
    Implements: PD Control
    Complications:
        - [x] Torque Limits
        - [.] Force Limts -> Torque Limits based on geometry
        - [ ] Pressure Limits -> Force Limits -> Torque Limits
        - [ ] Max Pressure Fill Rate -> dynamic pressure change
        - [ ] Control only updates at X Hz
        - [ ] Control does bang-bang pressure control
        - [ ] Simulate Pressure Fill from regulated supply, venting to atmos.
    '''
    # TODO(buckbaskin): make a more complex control model with pressure
    # Use numerical derivative of Torque and Theta for computed pressure to adjust 
    #   torque
    delta = state - desired_state
    Torque_des = -K_p * delta[0] - K_v * delta[1]
    
    T_r = 0.5 * Torque_des + stiffness
    T_l = -0.5 * Torque_des + stiffness
    T_r = np.clip(T_r, MIN_TORQUE, MAX_TORQUE)
    T_l = np.clip(T_l, MIN_TORQUE, MAX_TORQUE)
    net_Torque = T_r - T_l

    return net_Torque

def force(state):
    x = 0
    y = 0
    return x, y

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
        - [ ] Estimated Hysterisis effect of filling or empty actuators applying
                a torque opposite the motion
    '''
    return 0

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

    M_r = ROBOT_MASS
    F_r = M_r * g
    R_n = LINK_LENGTH
    link_gravity = F_g * R_g * math.sin(theta)
    normal_force = - F_r * R_n * math.sin(theta)

    return link_gravity + normal_force

def motion_evolution(state, desired_state, stiffness, time_step):
    '''
    M * ddot theta + C * dot theta + N * theta = torque
    ddot theta = 1 / M * (torque - C * dot theta - N) 
    '''
    net_Torque = control(state, desired_state, stiffness)

    M = mass_model(state[0])
    C = vel_effects(state[0], state[1])
    N = conservative_effects(state[0])
    
    accel = (net_Torque - C * state[1] - N) / M
    
    # accelration happens over the time step
    start_vel = state[1]
    end_vel = state[1] + accel * time_step
    avg_vel = state[1] + accel * time_step / 2

    start_theta = state[0]
    end_theta = state[0] + avg_vel * time_step

    return np.array([end_theta, end_vel, accel]).flatten()


if __name__ == '__main__':
    start_state = np.array([0.02, 0, 0])
    
    time_resolution = 0.01
    time_start = 0
    time_end = 60
    time = np.arange(time_start, time_end, time_resolution)
    desired_state = np.zeros((time.shape[0],3))
    desired_state[:,0] = MAX_AMPLITUDE * np.sin(time)
    desired_state[:,1] = MAX_AMPLITUDE * np.cos(time)
    desired_state[:,2] = -MAX_AMPLITUDE * np.sin(time)
    fig = plt.figure()
    ax_pos = fig.add_subplot(2, 1, 1)
    ax_pos.set_title('Position')
    ax_pos.plot(time,  desired_state[:,0] / MAX_AMPLITUDE)

    print('calculating...')
    for stiffness in [1.0,]:
        state = np.ones((time.shape[0], start_state.shape[0]))
        state[0,:] = start_state
        for i in range(state.shape[0] - 1):
            val = motion_evolution(
                state[i,:],
                desired_state[i+1,:],
                stiffness,
                time_resolution)
            state[i+1,:] = val
        ax_pos.plot(time, state[:,0] / MAX_AMPLITUDE)
        delta = state - desired_state

        accum_pos_error = sum(delta[:,0])
        accum_vel_error = sum(delta[:,1])
        print('pos_error', accum_pos_error)
        print('vel_error', accum_vel_error)

        T = -K_p * (delta[:,0])
        T += -K_v * (delta[:,1])

        ax_tor = fig.add_subplot(2, 1, 2)
        ax_tor.set_title('Torque Components')
        ax_tor.plot(time, T)
        ax_tor.plot(time, - K_p * (delta[:,0]))
        ax_tor.plot(time, - K_v * (delta[:,1]))
    
    print('show for the dough')
    plt.show()