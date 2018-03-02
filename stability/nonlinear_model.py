import sympy
sympy.init_printing()

from sympy import symbols, diff, simplify, latex

from sympy import cos, tan

# User inputs (desired angle, desired torque)
td, Td = symbols('\\theta_{des} Torque_{des}')

# First level geometry calculations
Lr, La, k, L0, L1, a, d, b, F = symbols('l_{rest} l_{angle} k l_{0} l_{1} \\alpha d \\beta F')

# Second level pressure calculations
P, a0, a1, a2, a3, a4, a5, a6, kmax, S = symbols('P a0 a1 a2 a3 a4 a5 a6 k_{max} S')

# Intermediate values in the modeling equation
La = L0 + L1 * cos(a + td)
k = (Lr - La) / Lr
F = Td / (d * cos(b + td))

def pprint(title, value):
    print('\section{%s}' % (title,))
    print('\\begin{equation}\n%s\n\\end{equation}' % latex(value))

pprint('$L_{angle}$', La)

pprint('$k$', k)

pprint('$F$', F)

# Final pressure calculation model
P = a0 + a1 * tan(a2 * (k / (a4 * F + kmax) + a3)) + a5 * F + a6 * S

pprint('Pressure Model', P)

# Substitute Empirical Values into model

empirical_P = P.subs([
    (a0, 254.3),
    (a1, 192.0),
    (a2, 2.0265),
    (a3, -0.461),
    (a4, -0.331),
    (a5, 1.230),
    (a6, 15.6)])

pprint('Empirical Pressure Model (subs a*)', empirical_P)

# Calculate derivative of model wrt theta
dPdtheta = diff(empirical_P, td)

pprint('$\dfrac{\partial P}{\partial \\theta}$', dPdtheta)
