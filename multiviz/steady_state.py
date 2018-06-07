'''
Some Maths

C dV/dt = G_m (Ev - V) + G_syn (E_syn - V) + I
'''
from copy import deepcopy
from itertools import product

import numpy as np

from mpl_toolkits.mplot3d import Axes3D
from matplotlib import pyplot as plt

from pprint import pprint

# mapping from neuron name to voltage
og_neurons = {
    'high': {
        'voltage': -40,
        'lock': True,
    },
    'test in': {},
    'test out': {},
    'fusion accel +': {},
    'inertia (test)': {},
    'neg load effect (test)': {},
    'pos load effect (test)': {},
    'neg damp effect (test)': {},
    'pos damp effect (test)': {},
    'tcn+': {},
    'tc+': {
        'applied_current': 20,
    },
    'inv pos net torque': {
        'applied_current': 20,
    },
    'pos net torque': {},
    'ext torque guess': {
        'voltage': -50,
        'visited': 1,
        'conductance': 0,
    },
    'ext torque': {},
    'ext torque also': {},
    'ext pres (guess)': {},
    'ext pres (test)': {},
    'ext +p err': {},
    'ext -p err': {},
    'theta mult 1': {
        'applied_current': 20,
    },
    'abs theta': {},
    'pos theta': {},
    'neg theta': {
        'applied_current': 20,
    },
    'theta (test)': {},
}

# mapping from synapse name to properties
synapse_types = {
    'signal transfer': {
        'potential': 134, # mV
        'conductance': 0.115, # micro siemens
        'lo': -60,
        'hi': -40,
        'id': '74912d0e-6d4c-48f7-99a6-a2c0c541976e',
    },
    'conv forward neg': {
        'potential': -100,
        'conductance': 0.5,
        'lo': -60,
        'hi': -50,
        'id': '788aa18b-93f5-4fba-bda7-82152b501a1f',
    },
    'conv forward pos': {
        'potential': 134,
        'conductance': 0.115,
        'lo': -50,
        'hi': -40,
        'id': '11b3d9fa-3a52-4643-bbd2-a40eb07eb1be',
    },
    'signal amp 2x': {
        'potential': 134,
        'conductance': 0.23,
        'id': '3056ff98-05c0-486c-a10d-e651df31f875',
    },
    'signal amp 4x': {
        'potential': 134,
        'conductance': 0.46,
        'id': '85578db7-e355-434e-9891-9b64689ed69b'
    },
    'signal inv amp 2x': {
        'potential': -100,
        'conductance': 1.11,
        'id': '34ea07c1-cbbe-4250-951a-67e8d1da21a1',
    },
    'signal inv amp 4x': {
        'potential': -100,
        'conductance': 2.3,
        'id': '3696ce27-55b2-456c-b829-0cd0fb446ee8',
    },
    'torque pres converter': {
        'potential': 134,
        'conductance': 0.048,
        'id': '368e485a-679b-4564-ac8c-c63b05940926',
    },
    'integral inibitor': {
        'potential': -100,
        'conductance': 0.5,
        'id': '39a453be-9294-4306-a057-7f69d53a47c9',
    },
    'signal inverter': {
        'potential': -100,
        'conductance': 0.55,
        'id': '5975749f-f8e6-46b0-bb4d-7d06da043ca2',
    },
    'signal multiplier': {
        'potential': -61,
        'conductance': 19.75,
        'id': '61156786-e99e-4b95-bbb0-4f672b607a2b',
    },
    'signal inv red 0.2x': {
        'potential': -100,
        'conductance': 0.093,
        'id': '8664f6ec-686a-4aa8-96d1-8b1ca8114ec7',
    },
    'signal inv red 0.5x': {
        'potential': -100,
        'conductance': 0.22,
        'id': 'a0a658aa-f090-4014-9a73-30c46c1fb55c',
    },
    'signal inv stim': {
        'potential': -100,
        'conductance': 0.5,
        'id': 'a1a55801-a811-41f2-8700-1ed269834c93',
    },
    'signal divider': {
        'potential': -60,
        'conductance': 20,
        'id': 'cd07ff49-d279-4cdc-900a-70d4062baf2d',
    },
    'signal red 0.2x': {
        'potential': 134,
        'conductance': 0.021,
        'id': 'd43aabad-74c5-479e-a5b7-d837f7b17ea3',
    },
    'signal red 0.5x': {
        'potential': 134,
        'conductance': 0.054,
        'id': 'e3f40f4e-72fc-42e4-89e8-86210bbe817e',
    },
}

print('Wow, you made %d synapse types.' % (len(synapse_types),))

# mapping from ending neuron to starting neuron, synapse type
edges = {
    'pos theta': {
        'theta (test)': 'conv forward pos',
    },
    'neg theta': {
        'theta (test)': 'conv forward neg',
    },
    'abs theta': {
        'pos theta': 'signal transfer',
        'neg theta': 'signal transfer',
    },
    'theta mult 1': {
        'abs theta': 'signal multiplier',
    },
    'ext torque also': {
        'theta mult 1': 'signal multiplier',
        'ext torque': 'signal transfer',
    },
    'ext pres (guess)': {
        'ext torque also': 'torque pres converter',
        'ext torque': 'signal transfer',
    },
    'ext +p err': {
        'ext pres (test)': 'signal transfer',
        'ext pres (guess)': 'signal inverter',
    },
    'ext -p err': {
        'ext pres (test)': 'signal inverter',
        'ext pres (guess)': 'signal transfer',
    },
    'ext torque guess': {
        'ext +p err': 'signal amp 2x',
        'ext -p err': 'signal inv amp 2x',
    },
    'ext torque': {
        'ext torque guess': 'signal transfer',
    },
    'pos net torque': {
        'ext torque guess': 'signal transfer',
    },
    'inv pos net torque': {
        'pos net torque': 'signal inv stim',
    },
    'tc+': {
        'inv pos net torque': 'signal inv stim',
        'pos damp effect (test)': 'signal transfer',
        'neg damp effect (test)': 'signal inverter',
    },
    'tcn+': {
        'tc+': 'signal transfer',
        'pos load effect (test)': 'signal transfer',
        'neg load effect (test)': 'signal inverter',
    },
    'fusion accel +': {
        'tcn+': 'signal transfer',
        'inertia (test)': 'signal divider',
    },
}

neurons = deepcopy(og_neurons)

def steady_state(neuron_name, neurons):
    neuron_props = neurons[neuron_name]
    I_app = 0
    if 'applied_current' in neuron_props:
        I_app = neuron_props['applied_current']
    G_m = 1
    if 'size' in neuron_props:
        G_m = neuron_props['size']
    E_r = -60
    if 'resting' in neuron_props:
        E_r = neuron_props['resting']

    if G_m <= 0:
        return neuron_props['voltage']

    top = G_m * E_r + I_app
    bottom = G_m
    
    if neuron_name in edges:
        for input_name in edges[neuron_name]:
            synapse_type = edges[neuron_name][input_name]

            E_lo = -60
            if 'lo' in synapse_types[synapse_type]:
                E_lo = synapse_types[synapse_type]['lo']
            E_hi = -40
            if 'hi' in synapse_types[synapse_type]:
                E_hi = synapse_types[synapse_type]['hi']


            V_pre = -60
            if 'voltage' in neurons[input_name]:
                V_pre = neurons[input_name]['voltage']

            G_s = synapse_types[synapse_type]['conductance']
            if V_pre <= E_lo:
                G_s = 0
            elif V_pre >= E_hi:
                G_s = G_s
            else:
                G_s = G_s * (V_pre - E_lo) / (E_hi - E_lo)

            if synapse_type == 'conv forward neg':
                # print(synapse_types[synapse_type])
                # print(E_hi, '>= >=', E_lo)
                # print(V_pre)
                # print(G_s, 'vs', synapse_types[synapse_type]['conductance'])
                # input('Hi')
                pass

            E_s = synapse_types[synapse_type]['potential']
            top += G_s * E_s
            bottom += G_s

    V = top / bottom
    return V

def iterate_recursively(neuron_name, neurons):
    if neurons[neuron_name]['visited'] >= 1:
        '''
        Cycle detection!

        If I've already been here once, don't update "steady state" again
        '''
        # TODO(buckbaskin): need to reset visited count for multiple iterations
        return None
    neurons[neuron_name]['visited'] += 1
    if neuron_name in edges:
        # input('following edges to %s' % (edges[neuron_name],))

        for input_name in edges[neuron_name]:
            if neurons[input_name]['visited'] >= 1:
                '''
                Cycle detection!

                If I've already been there once, don't update "steady state" again
                '''
                continue

            iterate_recursively(input_name, neurons)

    if 'lock' not in neurons[neuron_name] or not neurons[neuron_name]['lock']:
        neurons[neuron_name]['voltage'] = steady_state(neuron_name, neurons)

def try_1_inputs(inputs, output, iterations = 3):
    neurons = deepcopy(og_neurons)
    for _ in range(iterations):
        for neuron_name in neurons:
            neurons[neuron_name]['visited'] = 0

        for input_name, voltage, applied_current in inputs:
            neurons[input_name] = {
                'voltage': voltage, # mV
                'visited': 0,
                'size': 0,
                'applied_current': applied_current,
            }
        iterate_recursively(output, neurons)

    voltages = {}
    for neuron_name in neurons:
        if 'voltage' in neurons[neuron_name]:
            voltages[neuron_name] = neurons[neuron_name]['voltage']
        else:
            voltages[neuron_name] = None
    return voltages

def reference_sum(inputs, output):
    accum = 0
    for input_ in inputs:
        accum += input_[1] - (-60)

    return accum - 60

def reference_torque(inputs, output):
    return -60

if __name__ == '__main__':
    RESOLUTION = 11
    ITERATIONS = 1
    output_neuron = 'test out'

    # All these variables get producted together so all combinations are tested

    position = np.zeros((RESOLUTION, 2,))
    position[:,0] = np.linspace(-60, -40, RESOLUTION)
    # position[:, 0] = np.ones((RESOLUTION,)) * -50


    ext_pres = np.zeros((RESOLUTION, 2))
    ext_pres[:, 0] = np.linspace(-60, -40, RESOLUTION)

    inputs = {
        'test in': list(position),
        # 'null': list(ext_pres),
        'null': list(ext_pres),
        # 'theta (test)': [[-60, 0]], # mV
    }

    # Step 1: Select two variables to have visualized against output
    input0 = 'test in'
    input1 = 'null'

    input_length0 = len(inputs[input0])
    input_length1 = len(inputs[input1])

    combine_this = []
    for input_neuron in inputs:
        volt_amps = inputs[input_neuron]
        for idx in range(len(volt_amps)):
            volt_amps[idx] = list(volt_amps[idx])
            volt_amps[idx].insert(0, input_neuron)
        combine_this.append(inputs[input_neuron])

    input_combos = list(product(*combine_this))

    data = np.zeros((len(list(input_combos)), len(inputs) + 1,))
    data_ref = np.zeros((len(list(input_combos)), len(inputs) + 1,))

    for iteration, input_combo in enumerate(input_combos):
        for index, value in enumerate(input_combo):
            if value[0] == input0:
                data[iteration, 0] = value[1] # mV
            if value[0] == input1:
                data[iteration, 1] = value[1]
            if value[0] == input0:
                data_ref[iteration, 0] = value[1] # mV
            if value[0] == input1:
                data_ref[iteration, 1] = value[1]
        general_output = try_1_inputs(input_combo, output_neuron, iterations=ITERATIONS)
        pprint(general_output)
        specific_output = general_output[output_neuron]
        data[iteration, -1] = specific_output
        data_ref[iteration, -1] = reference_torque(input_combo, output_neuron)

    fig = plt.figure()
    ax = fig.gca(projection='3d')
    X = data[:,0]
    X = X.reshape((input_length0, input_length1)) + 60
    Y = data[:,1]
    Y = Y.reshape((input_length0, input_length1)) + 60
    Z = data[:,-1]
    Z = Z.reshape((input_length0, input_length1)) + 60

    Z_ref = data_ref[:,-1]
    Z_ref = Z_ref.reshape((input_length0, input_length1))

    surf = ax.plot_surface(X, Y, Z, linewidth=0, antialiased=False, label='Neuron')
    # surf2 = ax.plot_surface(X, Y, Z_ref, linewidth=0, antialiased=False)
    ax.set_xlabel(input0 + ' mV')
    ax.set_ylabel(input1 + ' mV')
    ax.set_zlabel(output_neuron + ' mV')
    ticks = np.linspace(0, 20, 5)
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)
    ax.set_zticks(ticks)

    mean_error = np.mean(np.abs(Z - Z_ref))
    print('Mean Error from Reference')
    print('%.1f mV' % (mean_error,))
    # plt.legend()
    plt.tight_layout()
    plt.show()