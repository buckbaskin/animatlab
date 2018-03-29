# TODO

## Next Steps
- [x] Linear stability analysis of PD angle/torque control for large angles
- [x] Level curve for stiffness -> pick stiffness -> select angle from there
- [x] Build a dynamic model, 2 different Festos, negative feedback based on pressure/position curves. This is a numerical model where everything happens nicely. 
- [x] Test out dynamic behavior. Ex. for 0 applied torque, no damping, expect oscillation
- [x] Incorporate a discrete pressure update, update frequency of the controllers. Limits stability at high stiffness
- [x] Refactoring...
- [x] Quantify. Tracking accuracy and internal potential energy
- [x] Build a better controller for the slower update with fixed values
- [x] Explicitly model sensor input as a function of state
- [x] Investigate how changing estimated parameters affects stability
- [x] Not estimating velocity within the sensor model breaks stability
- [x] Implement a simpler mass model
- [x] Evaluate how the simple mass model estimate compares to the complex mass model estimate (graphically)
- [.] Get a static single joint that works for multiple changing weights, other parameters. Do a better job stably/smoothly updating control parameters
- [ ] Understand how long controller takes vs Simulation time. Make it run a little faster

## Potential Analysis

- [x] Do a model of how fast it can track
- [x] Control input, desired position, sin wave of frequency, Bode plot, analyze
- [x] Numerically analyze nonlinear system, doing the same stuff as for a linear system

## Building a Better Controller
- [x] Does it look close to linear for constant pressures?
- [x] How does this change with stiffness?
- [x] Also, related: what does the motion update do for constant control pressure?
- [x] Set the controller to a fixed time to reach the correct state

## Future Thoughts
- [ ] Update stiffness in a 3 joint model in simulation adding or removing weights
