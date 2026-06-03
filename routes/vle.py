from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from vle_calculator import VLECalculator
from core.gas_database import GAS_DB
import numpy as np
import traceback
from models.calculation import Calculation  # Ajouter en haut
from models import db 

vle_bp = Blueprint("vle", __name__)
vle_calculator = VLECalculator()


@vle_bp.route("/")
@login_required
def vle_index():
    """Page principale VLE avec tous les composants"""
    components_list = []
    for key, gas in GAS_DB.items():
        components_list.append({
            'key': key,
            'name': gas['name'],
            'formula': gas['formula'],
            'Tc': gas['Tc'],
            'Pc': gas['Pc'],
            'omega': gas['omega']
        })
    components_list.sort(key=lambda x: x['name'])
    
    return render_template("vle.html", components=components_list)


@vle_bp.route("/calculate", methods=["POST"])
@login_required
def vle_calculate():
    """Calcul VLE avec tous les types de mélanges"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data received'}), 400
        
        # Récupération des données
        components = data.get('components', ['Water', 'Methanol'])
        temperature = float(data.get('temperature', 298.15))
        pressure = float(data.get('pressure', 1.0))
        mole_fractions = [float(x) for x in data.get('mole_fractions', [0.5, 0.5])]
        
        # Normalisation des fractions molaires
        total = sum(mole_fractions)
        if abs(total - 1.0) > 0.01:
            mole_fractions = [x / total for x in mole_fractions]
        
        # Type de modèle
        model_type = data.get('model_type', 'ideal')
        
        # =========================================================
        # CAS 1: MÉLANGE IDÉAL (Loi de Raoult)
        # =========================================================
        if model_type == 'ideal':
            result = vle_calculator.bubble_point_pressure(
                mole_fractions, temperature, components, None, None
            )
            equations = [
                "📖 Loi de Raoult: P_i = x_i · P_i^sat(T)",
                "📊 Pression totale: P = Σ P_i",
                "💨 Composition vapeur: y_i = P_i / P",
                "γ_i = 1 (mélange idéal)"
            ]
        
        # =========================================================
        # CAS 2: ÉQUATIONS D'ÉTAT (EOS avec règles de mélange)
        # =========================================================
        elif model_type == 'eos':
            eos_model = data.get('model', 'pr')  # pr, vdw, srk
            model_params = data.get('model_params', {})
            
            # Ajouter les paramètres critiques des composants
            for key, gas in GAS_DB.items():
                if gas['name'] == components[0]:
                    model_params.setdefault('tc1', gas['Tc'])
                    model_params.setdefault('pc1', gas['Pc'])
                    model_params.setdefault('w1', gas['omega'])
                if gas['name'] == components[1]:
                    model_params.setdefault('tc2', gas['Tc'])
                    model_params.setdefault('pc2', gas['Pc'])
                    model_params.setdefault('w2', gas['omega'])
            
            result = vle_calculator.bubble_point_pressure(
                mole_fractions, temperature, components, eos_model, model_params
            )
            
            eos_names = {'pr': 'Peng-Robinson', 'vdw': 'Van der Waals', 'srk': 'Soave-Redlich-Kwong'}
            equations = [
                f"⚡ Équation d'état: {eos_names.get(eos_model, eos_model.upper())}",
                "🔧 Règle de mélange de Van der Waals: a_m = ΣᵢΣⱼ xᵢxⱼaᵢⱼ, b_m = Σᵢ xᵢbᵢ",
                f"🔬 Paramètre d'interaction binaire: k₁₂ = {model_params.get('k12', 0)}",
                "📊 Résolution de l'équation cubique pour Z"
            ]
        
        # =========================================================
        # CAS 3: MODÈLES D'ACTIVITÉ (NRTL, UNIQUAC, UNIFAC, Wilson)
        # =========================================================
        elif model_type == 'activity':
            activity_model = data.get('model', 'NRTL')
            model_params = data.get('model_params', {})
            
            result = vle_calculator.bubble_point_pressure(
                mole_fractions, temperature, components, activity_model, model_params
            )
            
            # Équations spécifiques à chaque modèle
            if activity_model == 'NRTL':
                equations = [
                    "📐 Loi de Raoult modifiée: P_i = x_i · γ_i · P_i^sat(T)",
                    "🔬 Modèle NRTL (Non-Random Two-Liquid)",
                    f"α = {model_params.get('alpha', 0.3)}",
                    f"a₁₂ = {model_params.get('a12', 0)} K, a₂₁ = {model_params.get('a21', 0)} K",
                    "τ₁₂ = a₁₂/T, G₁₂ = exp(-α·τ₁₂)",
                    "ln(γ₁) = x₂²[τ₂₁(G₂₁/(x₁+x₂G₂₁))² + τ₁₂G₁₂/(x₂+x₁G₁₂)²]"
                ]
            elif activity_model == 'UNIQUAC':
                equations = [
                    "📐 Loi de Raoult modifiée: P_i = x_i · γ_i · P_i^sat(T)",
                    "🧩 Modèle UNIQUAC (Universal Quasi-Chemical)",
                    f"r₁ = {model_params.get('r1', 1.0)}, r₂ = {model_params.get('r2', 1.0)}",
                    f"q₁ = {model_params.get('q1', 1.0)}, q₂ = {model_params.get('q2', 1.0)}",
                    f"a₁₂ = {model_params.get('a12', 0)} K, a₂₁ = {model_params.get('a21', 0)} K",
                    "ln(γ_i) = ln(γ_i^C) + ln(γ_i^R) (combinatoire + résiduelle)"
                ]
            elif activity_model == 'Wilson':
                equations = [
                    "📐 Loi de Raoult modifiée: P_i = x_i · γ_i · P_i^sat(T)",
                    "📈 Modèle de Wilson",
                    f"V₁ = {model_params.get('V1', 50)} cm³/mol, V₂ = {model_params.get('V2', 50)} cm³/mol",
                    f"λ₁₂ = {model_params.get('lambda12', 1000)} J/mol, λ₂₁ = {model_params.get('lambda21', 1000)} J/mol",
                    "ln(γ₁) = -ln(x₁ + Λ₁₂x₂) + x₂(Λ₁₂/(x₁+Λ₁₂x₂) - Λ₂₁/(x₂+Λ₂₁x₁))",
                    "Λ₁₂ = (V₂/V₁)·exp(-λ₁₂/RT)"
                ]
            elif activity_model == 'UNIFAC':
                equations = [
                    "📐 Loi de Raoult modifiée: P_i = x_i · γ_i · P_i^sat(T)",
                    "🔬 Modèle UNIFAC (contribution de groupes)",
                    f"Groupes composant 1: {model_params.get('groups1', 'CH3:1,CH2:1,OH:1')}",
                    f"Groupes composant 2: {model_params.get('groups2', 'H2O:1')}",
                    "ln(γ_i) = ln(γ_i^C) + ln(γ_i^R)",
                    "Partie combinatoire: taille et forme des molécules",
                    "Partie résiduelle: interactions entre groupes"
                ]
            else:
                equations = ["📐 Loi de Raoult modifiée avec coefficients d'activité"]
        
        else:
            result = vle_calculator.bubble_point_pressure(
                mole_fractions, temperature, components, None, None
            )
            equations = ["Loi de Raoult"]
        
        # Ajout des métadonnées au résultat
        result['equations_used'] = equations
        result['model_used'] = model_type
        result['temperature'] = temperature
        result['components'] = components
        result['pressure_input'] = pressure
        
        # === AJOUTER LA SAUVEGARDE ===
        calc = Calculation(
            user_id=current_user.id,
            gas_name=f"VLE: {components[0]}-{components[1]}",
            temperature=temperature,
            pressure=pressure * 1e5,
            equations_used=f"model:{model_type}",
            calculation_type="vle"
        )
        calc.set_results({
            'components': components,
            'mole_fractions': mole_fractions,
            'bubble_pressure': result.get('bubble_pressure'),
            'vapor_composition': result.get('vapor_composition')
        })
        db.session.add(calc)
        db.session.commit()
        # ============================
        
        return jsonify({'success': True, 'result': result})
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@vle_bp.route("/gamma", methods=["POST"])
@login_required
def vle_gamma():
    """Génère la courbe des coefficients d'activité"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data received'}), 400
        
        components = data.get('components', ['Water', 'Methanol'])
        temperature = float(data.get('temperature', 298.15))
        model = data.get('model', 'NRTL')
        model_params = data.get('model_params', {})
        n_points = data.get('n_points', 50)
        
        result = vle_calculator.generate_gamma_curve(
            components, temperature, model, model_params, n_points
        )
        
        return jsonify({'success': True, 'result': result})
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@vle_bp.route("/components", methods=["GET"])
@login_required
def vle_components():
    """Retourne la liste de tous les composants disponibles"""
    components = []
    for key, gas in GAS_DB.items():
        components.append({
            'key': key,
            'name': gas['name'],
            'formula': gas['formula'],
            'Tc': gas['Tc'],
            'Pc': gas['Pc'],
            'omega': gas['omega']
        })
    components.sort(key=lambda x: x['name'])
    return jsonify({'components': components})