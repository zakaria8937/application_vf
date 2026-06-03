import numpy as np
from .eos_solver import (
    ideal_gas_pressure, vdw_pressure, srk_pressure, pr_pressure, R
)

def generate_isotherms(gas, T_list, Vm_min=None, Vm_max=None, n_points=200):
    """
    Génère les courbes P(Vm) pour plusieurs températures et les 4 EOS.
    Retourne un dict prêt pour Chart.js.
    """
    Tc = gas["Tc"]
    Pc = gas["Pc"]
    omega = gas["omega"]
    a = gas["a"]
    b = gas["b"]

    b_srk_approx = 0.08664 * R * Tc / (Pc * 1e5)
    Vm_min = Vm_min or b_srk_approx * 1.05
    Vm_max = Vm_max or Vm_min * 200

    Vm_arr = np.linspace(Vm_min, Vm_max, n_points)
    Vm_L = (Vm_arr * 1000).tolist()  # en L/mol pour affichage

    datasets = []
    colors = ["#1d4ed8", "#dc2626", "#16a34a", "#f97316"]
    dashes = [[], [6,3], [2,4], [8,3,2,3]]  # style par EOS
    eos_idx = ["Gaz Parfait", "Van der Waals", "SRK", "Peng-Robinson"]

    for idx, T in enumerate(T_list):
        for eos_name, calc_fn, extra in [
            ("Gaz Parfait", ideal_gas_pressure, {}),
            ("Van der Waals", vdw_pressure, {"a": a, "b": b}),
            ("SRK", srk_pressure, {"Tc": Tc, "Pc": Pc, "omega": omega}),
            ("Peng-Robinson", pr_pressure, {"Tc": Tc, "Pc": Pc, "omega": omega}),
        ]:
            try:
                P_arr = [calc_fn(T, Vm, **extra) / 1e5 for Vm in Vm_arr]  # en bar
                P_arr = [p if p > 0 else None for p in P_arr]
                datasets.append({
                    "label": f"{eos_name} — T={T}K",
                    "data": [{"x": x, "y": y} for x, y in zip(Vm_L, P_arr) if y],
                    "borderColor": colors[idx % len(colors)],
                    "borderDash": dashes[eos_idx.index(eos_name)],
                    "fill": False,
                    "tension": 0.2,
                    "pointRadius": 0,
                })
            except Exception:
                pass

    return {
        "datasets": datasets,
        "Vm_range": [Vm_min * 1000, Vm_max * 1000],
        "gas": {
            "name": gas.get("name", ""),
            "formula": gas.get("formula", ""),
            "Tc": Tc,
        },
    }
