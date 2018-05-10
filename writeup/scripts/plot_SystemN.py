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
C_ref = np.zeros(neg_N.shape)
C_ref[ 5000:10000] = 0.0
C_ref[10000:15000] = 0.0
C_ref[15000:20000] = 0.0
C_ref[20000:25000] = 0.0
C_ref[25000:30000] = 3.8
C_ref[30000:35000] = -3.8
C_ref[35000:40000] = 0.0
C_ref[40000:45000] = -3.8
C_ref[45000:50000] = 3.8
C_ref[50000:55000] = 0.0
C_ref[55000:60000] = 1.9
C_ref[60000:65000] = -1.9

pos_ref = np.zeros(pos_N.shape)
pos_ref[ 5000:10000] = 0.0
pos_ref[10000:15000] = 0.0
pos_ref[15000:20000] = 0.0
pos_ref[20000:25000] = 19.6
pos_ref[25000:30000] = 0.8
pos_ref[30000:35000] = 0.8
pos_ref[35000:40000] = -19.6
pos_ref[40000:45000] = -0.8
pos_ref[45000:50000] = -0.8
pos_ref[50000:55000] = 9.8
pos_ref[55000:60000] = 0.4
pos_ref[60000:65000] = 0.4

neg_ref = - pos_ref.copy()

pos_ref += -60
pos_ref = np.clip(pos_ref, -60, -40)

neg_ref += -60
neg_ref = np.clip(neg_ref, -60, -40)

setup = [
('Pos', [pos_N, pos_ref]),
('Neg', [neg_N, neg_ref]),
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
    # print(len(time))
    ax.plot(time[5000:], vel[5000:], linewidth=linewidth, label='Est. Adjustment')
    ax.plot(time[5000:], ref[5000:], linewidth=linewidth, label='Reference')
    
    if count == 1:
        ax.set_ylabel('+ Load Shift')
    else:
        ax.set_ylabel('- Load Shift')
    ax.set_xlabel('Time (sec)')

    ax.set_ylim(-60, -40)
    ax.set_yticks([-60, -40])

    ax.spines['right'].set_color('none')
    ax.spines['left'].set_linewidth(linewidth)
    ax.spines['top'].set_color('none')
    ax.spines['bottom'].set_linewidth(linewidth)

    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_xlim()

    plt.legend()
    plt.tight_layout()
    plt.savefig('images/results/TestSystemN%sWide.png' % (name,))
    plt.show()