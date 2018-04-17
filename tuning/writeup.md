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

## Pressures

For now: 0 -> 20 mV corresponds to 0 -> 620 kPa.

## Notes

In thinking about this, the mutual activations of neurons representing the same value where both are near zero may lead to bad values? Unless they remain generally mirrored around -60 mV for small variations, at which point it should be ok.

## Things to Visualize/Tune

1. [x] Velocity estimation network. Max velocity show on a 1 Hz sin wave input of the correct sin, or approximately that. Phase should be consistent with approximately 1 Hz.
2. [x] Accel fusion network is harder. Pick 10 combos of ext, flx pressures and joint angles. 3 joint angles, +/-/0. Then two pressure pairs each? Goal is to show "symmetric" effects from joint angle and pressure differential, with highest torque at the 0 angle.
3. [x] Parameter network behaviors (especially in the compressed single step version)
4. [x] Torque Guessing Network. Based on known correspondences, can do the maths out.
5. [x] Torque -> Pressures network. This needs pressure correspondences.

### Parameter Networks/Torque -> Acceleration

1. [x] Write out correspondences
2. [x] Verify behaviors with correspondences (inertia, etc.) for assumed known values.
3. [x] Update networks. Sign needs to be correct for 5-10 test cases.

### Things left to do

1. [x] Write out correspondences for Torque -> Acceleration Factors and Parameter
update networks (maybe?)
1. [x] Do the math for all the question marks to convert mV or real inputs to real
outputs. Then convert again to mV outputs.
2. [.] Set up test stimuli to make all these combinations happen. For visual effect
when testing, sort all the outputs by expected increasing output level.

## Working Notes

### Acceleration Fusion Network

Choose 10-12 sets of values for Ext Pressure (kPa), Flx Pressure (kPa), Theta
(~~rad~~, -20 <= mV <= 20)

#### Values

1. 620, 0, 0 -> ?
2. 0, 620, 0 -> ?
3. 310, 0, 0 -> ?
4. 0, 310, 0 -> ?

5. 620, 0, 10 -> ?
6. 0, 620, 10 -> ?
7. 310, 0, 10 -> ?
8. 0, 310, 10 -> ?

9. 620, 0, -10 -> ?
10. 0, 620, -10 -> ?
11. 310, 0, -10 -> ?
12. 0, 310, -10 -> ?

#### Calculated

```
( 20 mV,   0 mV,   0 mV) -> ( 620,   0,  0.00) -->  2 Nm ->  19.7 mV
(  0 mV,  20 mV,   0 mV) -> (  0,  620,  0.00) --> -2 Nm -> -19.7 mV
( 10 mV,   0 mV,   0 mV) -> ( 310,   0,  0.00) -->  1 Nm ->   9.9 mV
(  0 mV,  10 mV,   0 mV) -> (  0,  310,  0.00) --> -1 Nm ->  -9.9 mV
( 20 mV,   0 mV,  10 mV) -> ( 620,   0,  0.39) -->  2 Nm ->  18.5 mV
(  0 mV,  20 mV,  10 mV) -> (  0,  620,  0.39) --> -2 Nm -> -18.5 mV
( 10 mV,   0 mV,  10 mV) -> ( 310,   0,  0.39) -->  1 Nm ->   9.2 mV
(  0 mV,  10 mV,  10 mV) -> (  0,  310,  0.39) --> -1 Nm ->  -9.2 mV
( 20 mV,   0 mV, -10 mV) -> ( 620,   0, -0.39) -->  2 Nm ->  18.1 mV
(  0 mV,  20 mV, -10 mV) -> (  0,  620, -0.39) --> -2 Nm -> -18.1 mV
( 10 mV,   0 mV, -10 mV) -> ( 310,   0, -0.39) -->  1 Nm ->   9.1 mV
(  0 mV,  10 mV, -10 mV) -> (  0,  310, -0.39) --> -1 Nm ->  -9.1 mV
```

### Parameter Adjustment/Parameter Estimation/System Model Network

Choose values for prediction error, velocity. Position ranges from pi/4 ->
-pi/4 (+- 20 mV). I'm going to assume position error will also fall in that
range. It will saturate if it's more than that, but I expect only a possible
error of +- 4 for the given time step (max 8 mV if min predicted and max
realized). Velocity ranges +- 5 rad/sec (+- 20 mV). This suggests interesting
ranges. The lambda gain can be set to allow full pass through for now.

Test max and min error, 0 error and small positive error to check values with
different velocities.

The lag from the theta should be tuned independently.

#### Values

1. 0, 0 -> 0
2. 0, 20 -> 0
3. 0, -20 -> 0

4. 8, 0, -> ?
5. 8, 20, -> ?
6. 8, -20, -> ?

7. -8, 0, -> ?
8. -8, 20, -> ?
9. -8, -20, -> ?

10. 4, 0, -> ?
11. 4, 20, -> ?
12. 4, -20, -> ?

#### Calculated

lambda = gain * inertia * theta_err * (1 / (1+vel^2))

C_err = lambda * vel
N_err = lambda

Set gain = 1, inertia = 1 (not being tested here)

lambda = theta_err / (1 + vel^2)

```
1. (  0 mV,   0 mV) -> ( 0.00,  0.0) --> ( 0.0,  0.0) -> ( 0.0 mV,   0.0 mV)
2. (  0 mV,  20 mV) -> ( 0.00,  5.0) --> ( 0.0,  0.0) -> ( 0.0 mV,   0.0 mV)
3. (  0 mV, -20 mV) -> ( 0.00, -5.0) --> (-0.0,  0.0) -> (-0.0 mV,   0.0 mV)
4. (  8 mV,   0 mV) -> ( 0.31,  0.0) --> ( 0.0,  0.3) -> ( 0.0 mV,  19.6 mV)
5. (  8 mV,  20 mV) -> ( 0.31,  5.0) --> ( 0.1,  0.0) -> ( 3.8 mV,   0.8 mV)
6. (  8 mV, -20 mV) -> ( 0.31, -5.0) --> (-0.1,  0.0) -> (-3.8 mV,   0.8 mV)
7. ( -8 mV,   0 mV) -> (-0.31,  0.0) --> (-0.0, -0.3) -> (-0.0 mV, -19.6 mV)
8. ( -8 mV,  20 mV) -> (-0.31,  5.0) --> (-0.1, -0.0) -> (-3.8 mV,  -0.8 mV)
9. ( -8 mV, -20 mV) -> (-0.31, -5.0) --> ( 0.1, -0.0) -> ( 3.8 mV,  -0.8 mV)
10. (  4 mV,   0 mV) -> ( 0.16,  0.0) --> ( 0.0,  0.2) -> ( 0.0 mV,   9.8 mV)
11. (  4 mV,  20 mV) -> ( 0.16,  5.0) --> ( 0.0,  0.0) -> ( 1.9 mV,   0.4 mV)
12. (  4 mV, -20 mV) -> ( 0.16, -5.0) --> (-0.0,  0.0) -> (-1.9 mV,   0.4 mV)
```

#### Testing Notes (Iteration 1)

Even with two 4x gains in the system, the actual range of the system appears
to be +- 15 mV. This should scale the rest of the values down by about 25%.
There is also a lack of sensitivity near 0 (less than 2 mV rated above) that
I'm ok with for now because I think that small adjustments shouldn't cause
major problems. In practice, the gain in the above math is 0.75.

lambda = 0.75 * theta_err / (1 + vel^2)

TODO(buckbaskin): In test cases 6 and 8, the current implementation doesn't 
flip the sign of the C_err. Is the sign flip the correct behavior? The 
magnitude of 3.8 mV -> 2 mV is adequately explained by a smaller gain (see below)
Proposed Solution: ???

6. (  8 mV, -20 mV) -> -3.8 mV actually 2 mV
8. ( -8 mV,  20 mV) -> -3.8 mV actually 2 mV

TODO(buckbaskin): In test cases 5, 6, 8, 9, the magnitude of N_err should be
much smaller.
Proposed solution: add a divider to N_err.

5. (  8 mV,  20 mV) ->  0.8 mV actually 2 mV
6. (  8 mV, -20 mV) ->  0.8 mV actually 2 mV
8. ( -8 mV,  20 mV) -> -0.8 mV actually -2 mV
9. ( -8 mV, -20 mV) -> -0.8 mV actually -2 mV

TODO(buckbaskin): In test case 10, the magnitude of N_err should be larger.
Proposed Action: Investigate the value of Lambda. Lambda should be large here.
Even with adjustment, expect a value in the 7-8 mV range. After checking, the
lambda calculation is way off.

10. (  4 mV,   0 mV) -> 9.8 mV actually < 1 mV.

### Parameter Adjustment Timing

Need to tune the lagging theta prediction. It should just be 33 ms, but the
network might perform better with a less precise value. This will likely combine
with the gain term.

### Acceration from Torque

Need to check inertia, damping and load factors. Correspondences? Inertia 0.001 -> 2
kg... for 0 -> 20 mV. Damping factor: Nm / (m/s), 0 -> 1 seems reasonable (0 -> 5 
Nm with velocity range), likely on the lower side though for 0 -> 20 mV. 
Load shoud maybe be recalculated to take angle into account, so it'll get a 
little more complicated.

Measure these in mV, but consider their expected effect in kg, etc.

Torque correspondence is +-2.5 Nm -> +-20 mV
Accel correspondence is +- 30 rad/sec^2 -> +- 20 mV

Need to check input torque, input velocity as well

Values are:

Torque, velocity, inertia, damping, load

#### Values/Calculated

```
(  0 mV,   0 mV,   0 mV,   0 mV,   0 mV) -> (...) --> (  0.00) -> (  0.00 mV)
( 20 mV,   0 mV,   0 mV,   0 mV,   0 mV) -> (...) --> ( 25.00) -> ( 16.67 mV)
(-10 mV,   0 mV,   0 mV,   0 mV,   0 mV) -> (...) --> (-12.50) -> ( -8.33 mV)
( 10 mV,  20 mV,   0 mV,  10 mV,   0 mV) -> (...) --> (-12.50) -> ( -8.33 mV)
( 10 mV, -10 mV,   0 mV,  10 mV,   0 mV) -> (...) --> ( 25.00) -> ( 16.67 mV)
(-10 mV,  10 mV,   0 mV,  10 mV,   0 mV) -> (...) --> (-25.00) -> (-16.67 mV)
( 10 mV,   0 mV,  20 mV,   0 mV,   0 mV) -> (...) --> (  1.14) -> (  0.76 mV)
(-10 mV,   0 mV,  10 mV,   0 mV,   0 mV) -> (...) --> ( -2.08) -> ( -1.39 mV)
( 10 mV,   0 mV,   0 mV,   0 mV,  20 mV) -> (...) --> ( -7.50) -> ( -5.00 mV)
(-10 mV,   0 mV,   0 mV,   0 mV,  10 mV) -> (...) --> (-22.50) -> (-15.00 mV)
```

### Torque Guessing Network

Inputs: Current Position, Desired Position and Velocity. Guesses torque
modifcation to velocity.
to position to match a desired position, with "constant" effects from damping,
inertia, etc. Input quantities are current position, desired position, current velocity.

Position can change at most 4 mV in one direction per step, so a position error
of 5 or more should elicit maximum torque. To maintain the same position, a
maximum velocity should elicit maximum opposite torque.

#### Values/Calculated

```
( 0 mV,  0 mV,   0 mV) -> ( 0.00,  0.00,  0.00) --> (-1.42) -> (-11.4 mV)
( 0 mV,  5 mV,   0 mV) -> ( 0.00,  0.20,  0.00) --> ( 2.25) -> ( 18.0 mV)
( 0 mV, -5 mV,   0 mV) -> ( 0.00, -0.20,  0.00) --> (-2.25) -> (-18.0 mV)
( 5 mV,  0 mV,   0 mV) -> ( 0.20,  0.00,  0.00) --> (-2.25) -> (-18.0 mV)
(-5 mV,  0 mV,   0 mV) -> (-0.20,  0.00,  0.00) --> ( 2.25) -> ( 18.0 mV)
( 0 mV,  2 mV,   0 mV) -> ( 0.00,  0.08,  0.00) --> ( 2.25) -> ( 18.0 mV)
( 0 mV, -2 mV,   0 mV) -> ( 0.00, -0.08,  0.00) --> (-2.25) -> (-18.0 mV)
( 0 mV,  0 mV,  20 mV) -> ( 0.00,  0.00,  5.00) --> (-1.42) -> (-11.4 mV)
( 0 mV,  0 mV, -20 mV) -> ( 0.00,  0.00, -5.00) --> (-1.42) -> (-11.4 mV)
( 0 mV,  1 mV,  10 mV) -> ( 0.00,  0.04,  2.50) --> ( 2.25) -> ( 18.0 mV)
( 1 mV,  0 mV, -10 mV) -> ( 0.04,  0.00, -2.50) --> (-2.25) -> (-18.0 mV)
( 2 mV, -2 mV,   0 mV) -> ( 0.08, -0.08,  0.00) --> (-2.25) -> (-18.0 mV)
```

### Desired Torque -> Pressures

Inputs: Theta, Torque. Outputs -> Ext Pressure, Flx Pressure
The Theta, Torque range to +- 20 mV, joint limits, Not sure on max torque
applied (+- 2.5 Nm). Values in mV (rad) and Nm

#### Values/Calculated

```
(  0 mV,   0 mV) -> ( 0.00,  0.00) --> (231, 230) -> (7.5 mV,  7.5 mV)
(  0 mV,  20 mV) -> ( 0.00,  2.50) --> (540,   0) -> (17.4 mV, 0.0 mV)
(  0 mV, -20 mV) -> ( 0.00, -2.50) --> (  0, 540) -> (0.0 mV, 17.4 mV)
( 20 mV,   0 mV) -> ( 0.79,  0.00) --> (231, 230) -> (7.5 mV,  7.5 mV)
( 20 mV,  20 mV) -> ( 0.79,  2.50) --> (540,   0) -> (17.4 mV, 0.0 mV)
( 20 mV, -20 mV) -> ( 0.79, -2.50) --> (  0, 540) -> (0.0 mV, 17.4 mV)
(-20 mV,   0 mV) -> (-0.79,  0.00) --> (231, 230) -> (7.5 mV,  7.5 mV)
(-20 mV,  20 mV) -> (-0.79,  2.50) --> (540,   0) -> (17.4 mV, 0.0 mV)
(-20 mV, -20 mV) -> (-0.79, -2.50) --> (  0, 540) -> (0.0 mV, 17.4 mV)
( 10 mV,   0 mV) -> ( 0.39,  0.00) --> (231, 230) -> (7.5 mV,  7.5 mV)
( 10 mV,  20 mV) -> ( 0.39,  2.50) --> (540,   0) -> (17.4 mV, 0.0 mV)
( 10 mV, -20 mV) -> ( 0.39, -2.50) --> (  0, 540) -> (0.0 mV, 17.4 mV)
```

In general I think this covers a lot of different sub networks, or at least as
thoroughly as I can get without a consistent Wifi connection.

## CPG

Do this. This is a thing. I need to do. Later.
