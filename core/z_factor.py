import numpy as np
from .eos_solver import pr_volume, R

def z_curve(gas, T, P_min=1e4, P_max=200e5, n=100):
    """Calcule Z = PVm/RT en fonction de P pour l'EOS Peng-Robinson."""
    P_arr = np.linspace(P_min, P_max, n)
    Z_arr = []
    P_valid = []
    for P in P_arr:
        vols = pr_volume(T, P, gas["Tc"], gas["Pc"], gas["omega"])
        if vols:
            Vm = max(vols)
            Z = P * Vm / (R * T)
            Z_arr.append(Z)
            P_valid.append(P / 1e5)  # bar
    return {"P": P_valid, "Z": Z_arr}
