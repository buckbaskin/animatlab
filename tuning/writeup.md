# Tuning

## Linear Mapping of Theta, Vel, Accel

### Theta

Theta comes from joint limits. For now, pi/4 to -pi/4. This means that the positive half of the range is: 0 mV -> 20 mV corresponds to 0 -> pi / 4. The negative half of the range is: 0 mV -> 20 mV corresponds to 0 -> pi/4.

### Velocity

For now, an aribtrary limit on the velocity is set to 5 radians per seconds. 0 mV -> 20 mV corresponds to 0 rad/sec -> +- 5 rad/sec.
This comes from the following: the maximum of the derivative at an oscillation rate of 1 Hz.
Most joints in a dog at a walking range don't exceed an oscillation of 1 Hz.

### Acceleration

By a continuation of the same logic, the acceleration term should maximize at about 30 rad/(sec^2).
This analysis also suggests that the calculations for `max_torque.py` is off.


