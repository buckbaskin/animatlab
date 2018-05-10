import numpy as np
from matplotlib import pyplot as plt
plt.rc('font', **{'size': 8})
linewidth = 1

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
# 5000 steps per second
pos_ref = np.zeros(pos_net.shape)
pos_ref[5000:10000] = 19.7
pos_ref[15000:20000] = 9.9
pos_ref[25000:30000] = 18.5
pos_ref[35000:40000] = 9.2
pos_ref[45000:50000] = 18.1
pos_ref[55000:60000] = 9.1

pos_ref += -60

neg_ref = np.zeros(neg_net.shape)
neg_ref[10000:15000] = 19.7
neg_ref[20000:25000] = 9.9
neg_ref[30000:35000] = 18.5
neg_ref[40000:45000] = 9.2
neg_ref[50000:55000] = 18.1
neg_ref[60000:65000] = 9.1

neg_ref += -60

setup = [
('Pos', [pos_net, pos_ref]),
('Neg', [neg_net, neg_ref]),
]

# fig = plt.figure(figsize=(3,2.25,), dpi=300)
# ax1 = fig.add_subplot('211')
# ax2 = fig.add_subplot('212')
count = 0
for name, datasets in setup:
    # if count == 0:
    #     ax = ax1
    # else:
    #     ax = ax2
    count += 1
    fig = plt.figure(figsize=(6.5,2.25,), dpi=300)
    ax = fig.add_subplot('111')

    vel, ref = datasets
    ax.plot(time[5000:], vel[5000:], linewidth=linewidth, label='Est. Acc.')
    ax.plot(time[5000:], ref[5000:], linewidth=linewidth, label='Reference')
    
    if count == 1:
        ax.set_ylabel('+ Accel (mV)')
    else:
        ax.set_ylabel('- Accel (mV)')
    ax.set_xlabel('Time (sec)')

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
    plt.savefig('images/results/TestAccel%sWide.png' % (name,))
    plt.show()