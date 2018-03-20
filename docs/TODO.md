# TODO

## Talking w/ Nick 3/5

### Next Steps
- [x] Linear stability analysis of PD angle/torque control for large angles
- [x] Level curve for stiffness -> pick stiffness -> select angle from there
- [x] Build a dynamic model, 2 different Festos, negative feedback based on pressure/position curves. This is a numerical model where everything happens nicely. 
- [x] Test out dynamic behavior. Ex. for 0 applied torque, no damping, expect oscillation
- [.] Incorporate a discrete pressure update, update frequency of the controllers. Limits stability at high stiffness
- [ ] Then do lagging mass models that show how low stiffness can get before a certain tolerance isn't maintained
- [ ] Control input, desired position, sin wave of frequency, Bode plot, analyze
- [ ] Numerically analyze nonlinear system, doing the same stuff as for a linear system

### Future Thoughts
- [ ] Update stiffness in a 3 joint model in simulation adding or removing weights
