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
import math
import numpy as np
import matplotlib.pyplot as plt

K_p = 0.5
K_v = 2
control_matrix = np.matrix([[-K_p, -K_v, 0]])

MAX_TORQUE = 2
MIN_TORQUE = -0.5

def control(state, desired_state, stiffness):
    # TODO(buckbaskin): make a more complex control model with pressure
    # Use numerical derivative of Torque and Theta for computed pressure to adjust 
    #   torque
    Torque_des = control_matrix * np.matrix(state - desired_state).T
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
    return 1

def vel_effects(theta, theta_dot):
    return 0

def conservative_effects(theta):
    return 0

def motion_evolution(state, desired_state, stiffness, time_step):
    '''
    M * ddot theta + C * dot theta + N * theta = torque
    ddot theta = 1 / M * (torque - C * dot theta - N * theta) 
    '''
    net_Torque = control(state, desired_state, stiffness)
    
    M = mass_model(state[0])
    C = vel_effects(state[0], state[1])
    N = conservative_effects(state[0])
    
    accel = (net_Torque - C * state[1] - N * state[0]) / M

    # accelration happens over the time step
    start_vel = state[1]
    end_vel = state[1] + accel * time_step
    avg_vel = state[1] + accel * time_step / 2

    start_theta = state[0]
    end_theta = state[0] + avg_vel * time_step

    return np.array([end_theta, end_vel, accel]).flatten()


if __name__ == '__main__':
    start_state = np.array([0, 0, 0])
    
    time_resolution = 0.01
    time_start = 0
    time_end = 10
    time = np.arange(time_start, time_end, time_resolution)
    desired_state = np.zeros((time.shape[0],3))
    desired_state[:,0] = math.pi/4 * np.sin(time)
    desired_state[:,1] = math.pi/4 * np.cos(time)
    desired_state[:,2] = -math.pi/4 * np.sin(time)
    plt.plot(time,  desired_state[:,0])

    for stiffness in [0, 1.0, 2.0,]:
        state = np.ones((time.shape[0], start_state.shape[0]))
        state[0,:] = start_state
        for i in range(state.shape[0] - 1):
            val = motion_evolution(
                state[i,:],
                desired_state[i+1,:],
                stiffness,
                time_resolution)
            state[i+1,:] = val
        plt.plot(time, state[:,0])
    plt.title('Position(time)')
    plt.show()