in_ = '''This research develops a new synthetic nervous system controller for control of joints
using pneumatic actuators in order to create a more efficient and adaptable walking
robot system. This design implements new features not previously seen in a control
oriented nervous system. The design develops 3 major components not previously
used for control of antagonistic pneumatic actuators. The controller uses an internal
model of the actuators to estimate the state of the joint. The controller also uses
internal estimates of the dynamics of the joint to continually optimize the control
output. Additionally, the controller updates its own internal system model with a
memory-like loop to allow the controller to adapt to any joint and trajectory. The
controller allows for the replacement of proportional or other control designs with
a learning system that decreases wasted antagonistic muscle activation and wasted
energy, decreases phase lag and increases trajectory tracking accuracy'''

tokens = in_.split(' ')
num_tokens = len(tokens)
num_chars = len(in_)
print('The given input has %d tokens' % (num_tokens,))
print('There are %d characters, %d if spaces are not included' %
    (num_chars, num_chars - num_tokens))