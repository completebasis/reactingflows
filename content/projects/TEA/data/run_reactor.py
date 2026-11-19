"""
0-D homogeneous batch reactor for the TEA hydrolysis mechanism
"""

import warnings
import cantera as ct
import numpy as np
import pandas as pd

MECH = "/Volumes/SD/ChemPhysRAS/TEA/data/tea/cantera/reactor/tea_hydrolysis_Poskr_4stages.yaml"
T0 = 700.0          # K
P0 = ct.one_atm      # Pa
Y0 = "TEA:0.6787, H2O:0.3213"
T_END = 1.0e-1       # s
OUT_CSV = "tea_hydrolysis_Poskr_4stages.csv"

# The source OpenFOAM thermo file has a genuine cp/H/S discontinuity at
# Tcommon = 2000 K for every species (verified from the raw coefficients).
# We check whether the reactor actually reaches that range further below;
# suppress the repetitive load-time warning here to keep the output readable.
with warnings.catch_warnings():
    warnings.simplefilter("ignore", UserWarning)
    gas = ct.Solution(MECH)

gas.TPY = T0, P0, Y0

# Constant volume, adiabatic homogeneous reactor
reactor = ct.IdealGasReactor(gas, clone=False)
sim = ct.ReactorNet([reactor])

# Storage
states = ct.SolutionArray(gas, extra=["t"])

# Let CVODE choose its own internal step size; we just sample the
# trajectory at a reasonable number of output points.
n_points = 400
t_out = np.linspace(0, T_END, n_points)

for tt in t_out:
    sim.advance(tt)
    states.append(reactor.phase.state, t=tt)

# ---- Save full time history to CSV ----
df = pd.DataFrame({
    "t": states.t,
    "T": states.T,
    "p": states.P,
    "density": states.density,
})
for sp in gas.species_names:
    df[sp] = states.Y[:, gas.species_index(sp)]

df.to_csv(OUT_CSV, index=False)

# ---- Console summary ----
print(f"Mechanism: {MECH}")
print(f"Initial:  T = {T0} K, P = {P0/1e5:.4f} bar, Y0 = {Y0}")
print(f"Final:    t = {states.t[-1]:.4g} s")
print(f"          T = {states.T[-1]:.2f} K   (max T = {states.T.max():.2f} K "
      f"at t = {states.t[np.argmax(states.T)]:.4g} s)")
print(f"          P = {states.P[-1]/1e5:.4f} bar")
print()
print("Final mass fractions:")
for sp in gas.species_names:
    Yf = df[sp].iloc[-1]
    if Yf > 1e-8:
        print(f"  {sp:8s} {Yf:.6e}")

print(f"\nSaved: {OUT_CSV}")

