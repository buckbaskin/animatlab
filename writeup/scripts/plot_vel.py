import numpy as np
from matplotlib import pyplot as plt
plt.rc('font', **{'size': 12})

data = np.genfromtxt('data/TestVel.csv', delimiter=',', skip_header=1)
index = data[:, 0]
time = data[:, 1]

data[:, 1:] *= 1000

theta_in = data[:, 2]
theta_fast = data[:, 3]
theta_slow = data[:, 4]
neg_ref = data[:, 5]
neg_vel = data[:, 6]
pos_ref = data[:, 7]
pos_vel = data[:, 8]

setup = [
('Pos', [add_inc, add_inc2]),
('Neg', [sub_inc, sub_inc2]),
]

linewidth = 2

for name, datasets in setup:
    fig = plt.figure(figsize=(6,6,), dpi=300)
    ax = fig.add_subplot('111')
    for datas in datasets:
        ax.plot(time[200:], datas[200:], -60, -40, linewidth=linewidth)
    ax.set_xlim(-60, -40)
    ax.set_ylim(-60, -40)
    # ax.set_xticks([-60, -50, -40])
    # ax.set_yticks([-60, -50, -40])
    ax.set_xticks([-60, -40])
    ax.set_yticks([-60, -40])
    ax.set_xlabel('time (sec)')
    ax.set_ylabel('Vel (mV)')

    ax.spines['right'].set_color('none')
    ax.spines['left'].set_linewidth(linewidth)
    ax.spines['top'].set_color('none')
    ax.spines['bottom'].set_linewidth(linewidth)

    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_xlim()
    # ax.set_aspect((x1 - x0)/(y1 - y0))

    plt.tight_layout()
    plt.savefig('Fig%s.png' % (name,))
    plt.show()