from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from models import db
from models.calculation import Calculation
from models.molecule import Molecule
from core.eos_solver import compare_all, recommend_best_eos
from core.isotherms import generate_isotherms
from core.z_factor import z_curve
from core.gas_database import GAS_DB, get_gas_by_key, get_gas_by_formula

api_bp = Blueprint("api", __name__)


def get_gas(gas_key):
    if gas_key in GAS_DB:
        return GAS_DB[gas_key]
    gas = get_gas_by_formula(gas_key)
    if gas:
        return gas
    
    return None


@api_bp.route("/eos", methods=["POST"])
@login_required
def api_eos():
    data = request.get_json()
    gas_key = data.get("gas", "methane")
    T = float(data.get("T", 300))
    P_bar = float(data.get("P", 10))
    P = P_bar * 1e5

    gas = get_gas(gas_key)
    if not gas:
        return jsonify({"error": "Gaz non trouvé"}), 404

    try:
        results = compare_all(T, P, gas)
        best_eos = recommend_best_eos(T, P, gas, results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    calc = Calculation(
        user_id=current_user.id,
        gas_name=gas.get("name", gas_key),
        temperature=T,
        pressure=P,
        equations_used=",".join(results.keys()),
    )
    calc.set_results({k: {"Vm": v["Vm"], "Z": v["Z"], "label": v["label"]} for k, v in results.items()})
    db.session.add(calc)
    db.session.commit()

    results["best_eos"] = best_eos
    return jsonify(results)


@api_bp.route("/isotherms", methods=["POST"])
@login_required
def api_isotherms():
    data = request.get_json()
    gas = get_gas(data.get("gas", "methane"))
    t_list = data.get("temperatures", [300, 400, 500])
    vm_min = data.get("vmMin")
    vm_max = data.get("vmMax")
    if not gas:
        return jsonify({"error": "Gaz non trouvé"}), 404
    
    result = generate_isotherms(
        gas,
        t_list,
        Vm_min=float(vm_min) / 1000 if vm_min else None,
        Vm_max=float(vm_max) / 1000 if vm_max else None,
        n_points=420,
    )
    
    # === AJOUTER LA SAUVEGARDE ===
    calc = Calculation(
        user_id=current_user.id,
        gas_name=gas.get("name", data.get("gas", "unknown")),
        temperature=t_list[0] if t_list else 300,
        pressure=1e5,  # Pression par défaut pour les isothermes
        equations_used="isotherms",
        calculation_type="isotherm"
    )
    calc.set_results({"isotherms": "generated", "temperatures": t_list})
    db.session.add(calc)
    db.session.commit()
    # ============================
    
    return jsonify(result)


@api_bp.route("/z-curve", methods=["POST"])
@login_required
def api_z_curve():
    data = request.get_json()
    gas = get_gas(data.get("gas", "methane"))
    T = float(data.get("T", 300))
    if not gas:
        return jsonify({"error": "Gaz non trouvé"}), 404
    
    result = z_curve(gas, T)
    
    # ========== AJOUTER LA SAUVEGARDE ==========
    calc = Calculation(
        user_id=current_user.id,
        gas_name=gas.get("name", data.get("gas", "unknown")),
        temperature=T,
        pressure=1e5,  # Pression de référence
        equations_used="z_factor",
        calculation_type="z_factor"  # Important !
    )
    calc.set_results({
        "Z": result.get("Z", []),
        "P": result.get("P", []),
        "gas": gas.get("name")
    })
    db.session.add(calc)
    db.session.commit()
    # ===========================================
    
    return jsonify(result)


@api_bp.route("/gases", methods=["GET"])
@login_required
def api_gases():
    gases = {k: {"name": v["name"], "formula": v["formula"]} for k, v in GAS_DB.items()}
    custom = Molecule.query.all()
    for mol in custom:
        gases[mol.formula] = {"name": mol.name, "formula": mol.formula}
    return jsonify(gases)


@api_bp.route("/history", methods=["GET"])
@login_required
def api_history():
    calcs = Calculation.query.order_by(Calculation.created_at.desc()).limit(20).all()
    return jsonify([
        {
            "id": c.id,
            "gas": c.gas_name,
            "T": c.temperature,
            "P": c.pressure,
            "created_at": c.created_at.strftime("%Y-%m-%d %H:%M"),
        }
        for c in calcs
    ])


@api_bp.route("/molecule", methods=["POST"])
@login_required
def add_molecule():
    d = request.get_json()
    mol = Molecule(
        name=d["name"],
        formula=d["formula"],
        tc=float(d["Tc"]),
        pc=float(d["Pc"]),
        omega=float(d["omega"]),
        a_vdw=float(d["a"]),
        b_vdw=float(d["b"]),
        user_id=current_user.id,
    )
    db.session.add(mol)
    db.session.commit()
    return jsonify({"success": True, "id": mol.id})
