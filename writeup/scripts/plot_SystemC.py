import numpy as np
from matplotlib import pyplot as plt
plt.rc('font', **{'size': 8})
linewidth = 1

data = np.genfromtxt('data/TestSystemModel.csv', delimiter=',', skip_header=1)
index = data[:, 0]
time = data[:, 1]

data[:, 2:] *= 1000

pos_err = data[:, 2]
pos_vel = data[:, 3]
neg_vel = data[:, 4]
_neg_vel2 = data[:, 5]
neg_err = data[:, 6]
neg_C = data[:, 7]
neg_N = data[:, 8]
pos_N = data[:, 9]
pos_C = data[:, 10]
neg_lam = data[:, 11]
pos_lam = data[:, 12]

# TODO(buckbaskin): define reference accelerations for positive, negative
# 5000 steps per second
pos_ref = np.zeros(pos_C.shape)
pos_ref[ 5000:10000] = 0.0
pos_ref[10000:15000] = 0.0
pos_ref[15000:20000] = 0.0
pos_ref[20000:25000] = 0.0
pos_ref[25000:30000] = 3.8
pos_ref[30000:35000] = -3.8
pos_ref[35000:40000] = 0.0
pos_ref[40000:45000] = -3.8
pos_ref[45000:50000] = 3.8
pos_ref[50000:55000] = 0.0
pos_ref[55000:60000] = 1.9
pos_ref[60000:65000] = -1.9

N_ref = np.zeros(pos_N.shape)
N_ref[ 5000:10000] = 0.0
N_ref[10000:15000] = 0.0
N_ref[15000:20000] = 0.0
N_ref[20000:25000] = 19.6
N_ref[25000:30000] = 0.8
N_ref[30000:35000] = 0.8
N_ref[35000:40000] = -19.6
N_ref[40000:45000] = -0.8
N_ref[45000:50000] = -0.8
N_ref[50000:55000] = 9.8
N_ref[55000:60000] = 0.4
N_ref[60000:65000] = 0.4

neg_ref = - pos_ref.copy()

pos_ref += -60
pos_ref = np.clip(pos_ref, -60, -40)

neg_ref += -60
neg_ref = np.clip(neg_ref, -60, -40)

setup = [
('Pos', [pos_C, pos_ref]),
('Neg', [neg_C, neg_ref]),
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
        ax.set_ylabel('+ Damp Shift')
        ax.set_xticks([])
    else:
        ax.set_xlabel('Time (sec)')
        ax.set_ylabel('- Damp Shift')

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
plt.savefig('images/results/TestSystemC.png')
plt.show()