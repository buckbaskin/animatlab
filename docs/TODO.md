# TODO

## Next Steps
- [x] Linear stability analysis of PD angle/torque control for large angles
- [x] Level curve for stiffness -> pick stiffness -> select angle from there
- [x] Build a dynamic model, 2 different Festos, negative feedback based on pressure/position curves. This is a numerical model where everything happens nicely. 
- [x] Test out dynamic behavior. Ex. for 0 applied torque, no damping, expect oscillation
- [x] Incorporate a discrete pressure update, update frequency of the controllers. Limits stability at high stiffness
- [x] Refactoring...
- [ ] Quantify. Tracking accuracy and internal potential energy
- [ ] Build a better controller for the slower update with fixed values
- [ ] Explicitly model sensor input as a function of state
- [ ] Get a static single joint that works for multiple changing weights

## Potential Analysis

- [ ] Do a model of how fast it can track
- [ ] Control input, desired position, sin wave of frequency, Bode plot, analyze
- [ ] Numerically analyze nonlinear system, doing the same stuff as for a linear system

## Building a Better Controller
- [.] Does it look close to linear for constant pressures?
- [ ] How does this change with stiffness?
- [ ] Also, related: what does the motion update do for constant control pressure?

## Future Thoughts
- [ ] Update stiffness in a 3 joint model in simulation adding or removing weights
