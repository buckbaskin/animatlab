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

## Expectations

The expected controller rate is about 30 hz. This corresponds to a time step of about 33 milliseconds. 
Assuming the maximum acceleration occurs for that entire time step, the maximum change in velocity is just under 1 m/s.
Over the velocity mapping range, this means that a fully positive or negative acceleration neuron, transfered through a synapse, should shift the neuron by 4 mV (0.2x/reduction).

For a maximum velocity of 5 rad/sec, the expectation is that the position will change at most 0.165 rad in one time step. This corresponds to 4.2 mV in the split estimators of position/theta. As a current approximation, both can use the same reduction edge that takes full activation and shifts by 4 mV.

## Notes

In thinking about this, the mutual activations of neurons representing the same value where both are near zero may lead to bad values? Unless they remain generally mirrored around -60 mV for small variations, at which point it should be ok.
