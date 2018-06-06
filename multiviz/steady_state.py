'''
Some Maths

C dV/dt = G_m (Ev - V) + G_syn (E_syn - V) + I
'''
from copy import deepcopy
from itertools import product

import numpy as np

from mpl_toolkits.mplot3d import Axes3D
from matplotlib import pyplot as plt

# mapping from neuron name to voltage
og_neurons = {
    'output': {
        'voltage': -60, # mV
        'resting': -60,
        'visited': 0,
        'size': 1,
        'applied_current': 0
    },
}

# mapping from synapse name to properties
synapse_types = {
    'signal transfer': {
        'potential': 134, # mV
        'conductance': 0.115, # micro siemens
        'lo': -60,
        'hi': -40,
    }
}

# mapping from ending neuron to starting neuron, synapse type
edges = {
    'output': {
        'different name': 'signal transfer',
        'other': 'signal transfer',
    }
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

            V_pre = neurons[input_name]['voltage']
            G_s = synapse_types[synapse_type]['conductance']
            if V_pre < E_lo:
                G_s = 0
            elif V_pre > E_hi:
                G_s = G_s
            else:
                G_s = G_s * (V_pre - E_lo) / (E_hi - E_lo)
            E_s = synapse_types[synapse_type]['potential']
            top += G_s * E_s
            bottom += G_s
        
    V = top / bottom
    return V

def iterate_recursively(neuron_name, neurons):
    neurons[neuron_name]['visited'] += 1
    if neuron_name in edges:
        for input_name in edges[neuron_name]:
            iterate_recursively(input_name, neurons
                )

    neurons[neuron_name]['voltage'] = steady_state(neuron_name, neurons)

def try_1_inputs(inputs, output):
    neurons = deepcopy(og_neurons)

    output = 'output'

    for input_name, voltage, applied_current in inputs:
        neurons[input_name] = {
            'voltage': voltage, # mV
            'visited': 0,
            'size': 0,
            'applied_current': applied_current,
        }
    iterate_recursively(output, neurons)
    return neurons[output]['voltage']

def reference_sum(inputs, output):
    accum = 0
    for input_ in inputs:
        accum += input_[1] - (-60)

    return accum - 60

if __name__ == '__main__':
    output_neuron = 'output'

    # All these variables get producted together so all combinations are tested

    different_name = np.zeros((11, 2,))
    different_name[:,0] = np.linspace(-60, -40, 11)

    other = np.zeros((11, 2))
    other[:, 0] = np.linspace(-60, -40, 11)

    inputs = {
        'different name': list(different_name),
        'other': list(other),
    }

    # Step 1: Select two variables to have visualized against output

    input_length0 = len(inputs['different name'])
    input_length1 = len(inputs['other'])

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
            data[iteration, index] = value[1] # mV
            data_ref[iteration, index] = value[1]
        output = try_1_inputs(input_combo, output_neuron)
        data[iteration, -1] = output
        data_ref[iteration, -1] = reference_sum(input_combo, output_neuron)

    fig = plt.figure()
    ax = fig.gca(projection='3d')
    X = data[:,0]
    X = X.reshape((input_length0, input_length1))
    Y = data[:,1]
    Y = Y.reshape((input_length0, input_length1))
    Z = data[:,-1]
    Z = Z.reshape((input_length0, input_length1))

    Z_ref = data_ref[:,-1]
    Z_ref = Z_ref.reshape((input_length0, input_length1))

    surf = ax.plot_surface(X, Y, Z, linewidth=0, antialiased=False, label='Neuron')
    surf2 = ax.plot_surface(X, Y, Z_ref, linewidth=0, antialiased=False)
    ax.set_xticks([-60, -50, -40])
    ax.set_yticks([-60, -50, -40])
    ax.set_zticks([-60, -50, -40])

    mean_error = np.mean(np.abs(Z - Z_ref))
    print('Mean Error from Reference')
    print('%.1f mV' % (mean_error,))
    # plt.legend()
    plt.tight_layout()
    plt.show()