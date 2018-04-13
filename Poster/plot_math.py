import numpy as np
from matplotlib import pyplot as plt

data = np.genfromtxt('MathOperationsTable.csv', delimiter=',', skip_header=1)
index = data[:, 0]
time = data[:, 1]
mvIn = np.linspace(-60, -40, len(time))

data[:, 2:] *= 1000

add_inc2 = data[:, 2]
add_inc = data[:, 3]
sub_inc2 = data[:, 4]
sub_inc = data[:, 5]
mult_high = data[:, 6]
mult_mid = data[:, 7]
mult_low = data[:, 8]
div_high = data[:, 9]
div_low = data[:, 10]

setup = [
('Add', [add_inc, add_inc2]),
('Sub', [sub_inc, sub_inc2]),
('Mul', [mult_high, mult_mid, mult_low]),
('Div', [div_high, div_low]),
]
for name, datasets in setup:
    fig = plt.figure()
    ax = fig.add_subplot('111')
    for datas in datasets:
        ax.plot(mvIn[200:], np.clip(datas[200:], -60, -40))
    ax.set_xlim(-60, -40)
    ax.set_ylim(-60, -40)
    ax.set_xticks([-60, -50, -40])
    ax.set_yticks([-60, -50, -40])
    ax.spines['right'].set_color('none')
    ax.spines['top'].set_color('none')

    plt.savefig('Fig%s.png' % (name,))
    plt.show()