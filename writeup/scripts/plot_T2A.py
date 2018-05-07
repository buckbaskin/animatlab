import numpy as np
from matplotlib import pyplot as plt
plt.rc('font', **{'size': 8})
linewidth = 1

data = np.genfromtxt('data/TestT2A.csv', delimiter=',', skip_header=1)
index = data[:, 0]
time = data[:, 1]

data[:, 2:] *= 1000

inv_pos_tor = data[:, 2]
load = data[:, 3]
inertia = data[:, 4]
inv_pos_vel = data[:, 5]
inv_neg_tor = data[:, 6]
inv_neg_vel = data[:, 7]
damping = data[:, 8]
tc_plus = data[:, 9]
tc_minus = data[:, 10]
neg_load = data[:, 11]
tcn_minus = data[:, 12]
tcn_plus = data[:, 13]
pos_load = data[:, 14]
pos_acc = data[:, 15]
neg_acc = data[:, 16]

# TODO(buckbaskin): define reference accelerations for positive, negative
# 5000 steps per second
pos_ref = np.zeros(pos_acc.shape)
pos_ref[ 5000:10000] = 0
pos_ref[10000:15000] = 20
pos_ref[15000:20000] = -9
pos_ref[20000:25000] = 12.5
pos_ref[25000:30000] = -12.5
pos_ref[30000:35000] = 0.5
pos_ref[35000:40000] = -1
pos_ref[40000:45000] = 0
pos_ref[45000:50000] = 0
pos_ref[50000:55000] = -8
neg_ref = - pos_ref.copy()

pos_ref += -60
pos_ref = np.clip(pos_ref, -60, -40)
neg_ref += -60
neg_ref = np.clip(neg_ref, -60, -40)

setup = [
('Pos', [pos_acc, pos_ref]),
('Neg', [neg_acc, neg_ref]),
]


fig = plt.figure(figsize=(3,2.25,), dpi=300)
ax1 = fig.add_subplot('211')
ax2 = fig.add_subplot('212')
count = 0
for name, datasets in setup:
    if count == 0:
        ax = ax1
    else:
        ax = ax2
    count += 1

    vel, ref = datasets
    # print(len(time))
    ax.plot(time[5000:], vel[5000:], linewidth=linewidth, label='Est. Acc.')
    ax.plot(time[5000:], ref[5000:], linewidth=linewidth, label='Reference')
    
    if count == 1:
        ax.set_ylabel('+ Accel (mV)')
        ax.set_xticks([])
    else:
        ax.set_xlabel('Time (sec)')
        ax.set_ylabel('- Accel (mV)')

    ax.set_ylim(-60, -40)
    ax.set_yticks([-60, -40])

    ax.spines['right'].set_color('none')
    ax.spines['left'].set_linewidth(linewidth)
    ax.spines['top'].set_color('none')
    ax.spines['bottom'].set_linewidth(linewidth)

    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_xlim()
    # ax.set_aspect((x1 - x0)/(y1 - y0))

# plt.legend()
plt.tight_layout()
plt.savefig('images/results/TestT2A.png')
plt.show()