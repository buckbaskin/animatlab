import numpy as np
from matplotlib import pyplot as plt
plt.rc('font', **{'size': 12})

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

linewidth = 2

for name, datasets in setup:
    fig = plt.figure(figsize=(3,3,), dpi=300)
    ax = fig.add_subplot('111')
    for datas in datasets:
        ax.plot(mvIn[200:], datas[200:], -60, -40, linewidth=linewidth)
    ax.set_xlim(-60, -40)
    ax.set_ylim(-60, -40)
    # ax.set_xticks([-60, -50, -40])
    # ax.set_yticks([-60, -50, -40])
    ax.set_xticks([-60, -40])
    ax.set_yticks([-60, -40])
    ax.set_xlabel('U0 (mV)')
    ax.set_ylabel('U1 (mV)')
    ax.spines['right'].set_color('none')
    ax.spines['left'].set_linewidth(linewidth)
    ax.spines['top'].set_color('none')
    ax.spines['bottom'].set_linewidth(linewidth)

    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_xlim()
    ax.set_aspect((x1 - x0)/(y1 - y0))

    plt.tight_layout()
    plt.savefig('Fig%s.png' % (name,))
    plt.show()