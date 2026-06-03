import numpy as np

R = 8.314  # Constante des gaz parfaits (J/mol.K)

# ─────────────────────────────────────────────
# 1. Gaz Parfait : PV = nRT  →  P = RT/Vm
# ─────────────────────────────────────────────
def ideal_gas_pressure(T, Vm):
    """Calcule P avec l'équation des gaz parfaits."""
    return R * T / Vm

def ideal_gas_volume(T, P):
    """Calcule Vm avec l'équation des gaz parfaits."""
    return R * T / P

# ─────────────────────────────────────────────
# 2. Van der Waals : (P + a/Vm²)(Vm - b) = RT
# ─────────────────────────────────────────────
def vdw_pressure(T, Vm, a, b):
    """Calcule P avec l'équation de Van der Waals."""
    return (R * T / (Vm - b)) - (a / Vm**2)

def vdw_volume(T, P, a, b):
    """Résout le volume molaire avec Van der Waals (équation cubique)."""
    # Vm³ - (b + RT/P)Vm² + (a/P)Vm - ab/P = 0
    coeffs = [
        1,
        -(b + R*T/P),
        a/P,
        -a*b/P
    ]
    roots = np.roots(coeffs)
    real_roots = [r.real for r in roots if abs(r.imag) < 1e-10 and r.real > b]
    return sorted(real_roots)

# ─────────────────────────────────────────────
# 3. SRK (Soave-Redlich-Kwong)
# ─────────────────────────────────────────────
def srk_params(Tc, Pc, omega, T):
    """Calcule les paramètres a et b pour SRK."""
    Tr = T / Tc
    m = 0.480 + 1.574*omega - 0.176*omega**2
    alpha = (1 + m*(1 - Tr**0.5))**2
    a = 0.42748 * (R**2 * Tc**2 / (Pc*1e5)) * alpha
    b = 0.08664 * R * Tc / (Pc*1e5)
    return a, b

def srk_pressure(T, Vm, Tc, Pc, omega):
    """Calcule P avec l'équation SRK."""
    a, b = srk_params(Tc, Pc, omega, T)
    return (R*T / (Vm - b)) - (a / (Vm*(Vm + b)))

def srk_volume(T, P, Tc, Pc, omega):
    """Résout Vm avec SRK."""
    a, b = srk_params(Tc, Pc, omega, T)
    A = a*P / (R*T)**2
    B = b*P / (R*T)
    coeffs = [1, -1, A - B - B**2, -A*B]
    roots = np.roots(coeffs)
    Z_roots = [r.real for r in roots if abs(r.imag) < 1e-10 and r.real > 0]
    Vm_roots = [z * R * T / P for z in Z_roots]
    return sorted([v for v in Vm_roots if v > b])

# ─────────────────────────────────────────────
# 4. Peng-Robinson (PR)
# ─────────────────────────────────────────────
def pr_params(Tc, Pc, omega, T):
    """Calcule les paramètres a et b pour Peng-Robinson."""
    Tr = T / Tc
    kappa = 0.37464 + 1.54226*omega - 0.26992*omega**2
    alpha = (1 + kappa*(1 - Tr**0.5))**2
    a = 0.45724 * (R**2 * Tc**2 / (Pc*1e5)) * alpha
    b = 0.07780 * R * Tc / (Pc*1e5)
    return a, b

def pr_pressure(T, Vm, Tc, Pc, omega):
    """Calcule P avec l'équation de Peng-Robinson."""
    a, b = pr_params(Tc, Pc, omega, T)
    return (R*T / (Vm - b)) - (a / (Vm*(Vm + b) + b*(Vm - b)))

def pr_volume(T, P, Tc, Pc, omega):
    """Résout Vm avec Peng-Robinson."""
    a, b = pr_params(Tc, Pc, omega, T)
    A = a*P / (R*T)**2
    B = b*P / (R*T)
    coeffs = [1, -(1 - B), A - 3*B**2 - 2*B, -(A*B - B**2 - B**3)]
    roots = np.roots(coeffs)
    Z_roots = [r.real for r in roots if abs(r.imag) < 1e-10 and r.real > 0]
    Vm_roots = [z * R * T / P for z in Z_roots]
    return sorted([v for v in Vm_roots if v > b])

# ─────────────────────────────────────────────
# Fonction principale : compare toutes les EOS
# ─────────────────────────────────────────────
def compare_all(T, P, gas):
    """Compare les 4 équations d'état pour un gaz donné."""
    Tc = gas["Tc"]
    Pc = gas["Pc"]
    omega = gas["omega"]
    a_vdw = gas["a"]
    b_vdw = gas["b"]

    results = {}

    # Gaz parfait
    Vm_ig = ideal_gas_volume(T, P)
    results["ideal_gas"] = {"Vm": Vm_ig, "Z": 1.0, "label": "Gaz Parfait"}

    # Van der Waals
    vdw_vols = vdw_volume(T, P, a_vdw, b_vdw)
    Vm_vdw = max(vdw_vols) if vdw_vols else None
    if Vm_vdw:
        Z_vdw = P * Vm_vdw / (R * T)
        results["vdw"] = {"Vm": Vm_vdw, "Z": Z_vdw, "label": "Van der Waals"}

    # SRK
    srk_vols = srk_volume(T, P, Tc, Pc, omega)
    Vm_srk = max(srk_vols) if srk_vols else None
    if Vm_srk:
        Z_srk = P * Vm_srk / (R * T)
        results["srk"] = {"Vm": Vm_srk, "Z": Z_srk, "label": "SRK"}

    # Peng-Robinson
    pr_vols = pr_volume(T, P, Tc, Pc, omega)
    Vm_pr = max(pr_vols) if pr_vols else None
    if Vm_pr:
        Z_pr = P * Vm_pr / (R * T)
        results["pr"] = {"Vm": Vm_pr, "Z": Z_pr, "label": "Peng-Robinson"}

    return results


def recommend_best_eos(T, P, gas, results):
    """Recommande l'EOS la plus adaptée au regime thermodynamique."""
    Tc = gas["Tc"]
    Pc_pa = gas["Pc"] * 1e5
    omega = gas["omega"]
    formula = gas.get("formula", "")

    Tr = T / Tc
    Pr = P / Pc_pa
    available = set(results.keys())

    if "ideal_gas" in available and Pr < 0.05 and Tr > 1.5:
        key = "ideal_gas"
        confidence = "élevée"
        reason = (
            "Le fluide est loin de la zone critique et la pression reduite est faible; "
            "le comportement est presque ideal."
        )
    elif "pr" in available and (Pr >= 0.1 or 0.75 <= Tr <= 1.3 or omega >= 0.1 or formula == "H2O"):
        key = "pr"
        confidence = "élevée" if Pr >= 0.5 or 0.85 <= Tr <= 1.2 else "moyenne"
        reason = (
            "Peng-Robinson est généralement plus robuste pour les fluides reels, "
            "les fortes pressions, les fluides avec facteur acentrique eleve et les zones proches du critique."
        )
    elif "srk" in available and Tr > 1.1:
        key = "srk"
        confidence = "moyenne"
        reason = "SRK est un bon compromis pour les phases vapeur de gaz legers a pression moderee."
    elif "pr" in available:
        key = "pr"
        confidence = "moyenne"
        reason = "Peng-Robinson offre le meilleur choix general parmi les EOS cubiques disponibles."
    elif "srk" in available:
        key = "srk"
        confidence = "moyenne"
        reason = "SRK est la meilleure option disponible apres filtrage des solutions valides."
    elif "vdw" in available:
        key = "vdw"
        confidence = "faible"
        reason = "Van der Waals est disponible, mais reste une approximation qualitative."
    else:
        key = "ideal_gas"
        confidence = "faible"
        reason = "Seule l'EOS des gaz parfaits est disponible pour ces conditions."

    best = results[key]
    print(f"[DEBUG] Tr={Tr}, Pr={Pr}, omega={omega}, available={available}")
    print(f"[DEBUG] Selected: {key}, confidence={confidence}")
    
    return {
        "key": key,
        "label": best["label"],
        "confidence": confidence,
        "reason": reason,
        "Tr": float(Tr),
        "Pr": float(Pr),
        "Vm": float(best["Vm"]),
        "Z": float(best["Z"]),
    }
