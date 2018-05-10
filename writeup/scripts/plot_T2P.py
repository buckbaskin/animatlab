import numpy as np
from matplotlib import pyplot as plt
plt.rc('font', **{'size': 8})
linewidth = 1

data = np.genfromtxt('data/TestT2P.csv', delimiter=',', skip_header=1)
index = data[:, 0]
time = data[:, 1]

data[:, 2:] *= 1000

neg_tor = data[:, 2]
pos_tor = data[:, 3]
theta = data[:, 4]
ext_p = data[:, 5]
flx_p = data[:, 6]

# TODO(buckbaskin): define reference accelerations for positive, negative
# 5000 steps per second
ext_ref = np.zeros(ext_p.shape)
ext_ref[ 5000:10000] = 7.5
ext_ref[10000:15000] = 17.4
ext_ref[15000:20000] = 0
ext_ref[20000:25000] = 7.5
ext_ref[25000:30000] = 17.4
ext_ref[30000:35000] = 0
ext_ref[35000:40000] = 7.5
ext_ref[40000:45000] = 17.4
ext_ref[45000:50000] = 0
ext_ref[50000:55000] = 7.5
ext_ref[55000:60000] = 17.4
ext_ref[60000:65000] = 0.0

flx_ref = np.zeros(flx_p.shape)
flx_ref[ 5000:10000] = 7.5
flx_ref[10000:15000] = 0.0
flx_ref[15000:20000] = 17.4
flx_ref[20000:25000] = 7.5
flx_ref[25000:30000] = 0.0
flx_ref[30000:35000] = 17.4
flx_ref[35000:40000] = 7.5
flx_ref[40000:45000] = 0
flx_ref[45000:50000] = 17.4
flx_ref[50000:55000] = 7.5
flx_ref[55000:60000] = 0.0
flx_ref[60000:65000] = 17.4

ext_ref += -60
ext_ref = np.clip(ext_ref, -60, -40)

flx_ref += -60
flx_ref = np.clip(flx_ref, -60, -40)

setup = [
('Ext', [ext_p, ext_ref]),
('Flx', [flx_p, flx_ref]),
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
    ax.plot(time[5000:], vel[5000:], linewidth=linewidth, label='Est. Pres.')
    print('plot ref')
    ax.plot(time[5000:], ref[5000:], linewidth=linewidth, label='Reference')

    if count == 1:
        ax.set_ylabel('Ext. Pres. (mV)')
    else:
        ax.set_ylabel('Flx. Pres. (mV)')
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
    plt.savefig('images/results/TestT2P%sWide.png' % (name,))
    plt.show()