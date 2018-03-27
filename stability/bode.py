from simple_mass_model import ActualSimulator, OptimizingController, SimpleSimulator

if __name__ == '__main__':
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

    # Try following a sin curve of varying period
    # TODO(buckbaskin): adjust the plotting to first show the different iterations
    # TODO(buckbaskin): then plot something like a Bode Plot
    for period in [100, 50, 20, 10, 5, 2, 1, 0.5, 0.2, 0.1, 0.05, 0.02, 0.01,]:
        adjust = (pi * 2) / period 
        desired_state[:, 0] = MAX_AMPLITUDE * np.sin(time * adjust)
        desired_state[:, 1] = (MAX_AMPLITUDE * adjust) * np.cos(time * adjust)
        desired_state[:, 2] = -(MAX_AMPLITUDE * adjust * adjust) * np.sin(time * adjust)

        plt_index = 0

        fig = plt.figure()
        ax_pos = fig.add_subplot(4, 1, 1)
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
            ax_pos.plot(time[1000:], desired_state[1000:,plt_index] + ERROR_STANDARD,
                color='tab:purple', label='MAXIMUM')
            ax_pos.plot(time[1000:], desired_state[1000:,plt_index] - ERROR_STANDARD,
                color='tab:purple', label='MINIMUM')
        
    print('calculating...')
    stiffness = 1.0
    for index, _ in enumerate([0.0]):
        estimated_S = SimpleSimulator(M=0.0004, C=0.010, N=-1.7000)
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
        ax_inertia = fig.add_subplot(4, 1, 2)
        ax_inertia.plot(time, np.array(C.inertias))
        ax_inertia.set_ylabel('Inertia')
        ax_inertia.set_xlabel('Time (sec)')
        ax_damping = fig.add_subplot(4, 1, 3)
        ax_damping.plot(time, np.array(C.dampings))
        ax_damping.set_ylabel('Damping Factor')
        ax_damping.set_xlabel('Time (sec)')
        ax_cons = fig.add_subplot(4, 1, 4)
        ax_cons.plot(time, np.array(C.cons))
        ax_cons.set_ylabel('Load Factor')
        ax_cons.set_xlabel('Time (sec)')
        ax_pos.legend()
        print('show for the dough')
        plt.savefig('Simple_State_Model_Updating.png')
        plt.show()
        print('all done')