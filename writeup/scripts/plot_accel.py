import numpy as np
from matplotlib import pyplot as plt
plt.rc('font', **{'size': 12})

data = np.genfromtxt('data/TestAccel.csv', delimiter=',', skip_header=1)
index = data[:, 0]
time = data[:, 1]

data[:, 2:] *= 1000

theta = data[:, 2]
ext_pres = data[:, 3]
flx_pres = data[:, 4]
pos_net = data[:, 5]
neg_net = data[:, 6]

# TODO(buckbaskin): define reference accelerations for positive, negative

setup = [
('Pos', [pos_net,]),
('Neg', [neg_net,]),
]

linewidth = 2

for name, datasets in setup:
    fig = plt.figure(figsize=(6,3,), dpi=300)
    ax = fig.add_subplot('111')

    vel, = datasets
    # print(len(time))
    ax.plot(time[200:], vel[200:], linewidth=linewidth, label='Est. Acc.')
    # ax.plot(time[20000:40000], ref[20000:40000], linewidth=linewidth, label='Reference')
    
    ax.set_xlabel('Time (sec)')
    ax.set_ylabel('Acceleration (mV)')

    ax.set_ylim(-60, -40)
    ax.set_yticks([-60, -40])

    ax.spines['right'].set_color('none')
    ax.spines['left'].set_linewidth(linewidth)
    ax.spines['top'].set_color('none')
    ax.spines['bottom'].set_linewidth(linewidth)

    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_xlim()
    # ax.set_aspect((x1 - x0)/(y1 - y0))

    plt.legend()
    plt.tight_layout()
    plt.savefig('images/results/TestAccel%s.png' % (name,))
    plt.show()