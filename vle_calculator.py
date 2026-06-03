import math
from typing import Dict, List, Tuple, Optional
from thermodynamics import get_model, NRTLModel, UNIQUACModel, UNIFACModel, WilsonModel

# Constantes
R = 8.314  # J/(mol·K)


class VLECalculator:
    """Calculateur d'équilibre liquide-vapeur"""

    def __init__(self):
        self.R = R

    # =========================================================
    # SATURATION PRESSURE (Antoine)
    # =========================================================
    def calculate_saturation_pressure(self, component: str, T: float) -> float:
        """
        Calcule la pression de saturation via l'équation d'Antoine
        P_sat en bar, T en K
        """
        # Paramètres d'Antoine (A, B, C) - T en °C, P en mmHg
        antoine_params = {
            'Water': {'A': 8.07131, 'B': 1730.63, 'C': 233.426},
            'Methanol': {'A': 8.08097, 'B': 1582.271, 'C': 239.726},
            'Ethanol': {'A': 8.20417, 'B': 1642.89, 'C': 230.3},
            'Acetone': {'A': 7.02447, 'B': 1161.0, 'C': 224.0},
            'Benzene': {'A': 6.90565, 'B': 1211.033, 'C': 220.79},
            'Methane': {'A': 6.61184, 'B': 389.93, 'C': 266.69},
            'n-Butane': {'A': 6.80896, 'B': 935.86, 'C': 238.73},
        }
        
        if component not in antoine_params:
            return 0.1  # Valeur par défaut
        
        params = antoine_params[component]
        T_celsius = T - 273.15
        log10_Psat = params['A'] - params['B'] / (T_celsius + params['C'])
        P_sat_mmHg = 10 ** log10_Psat
        P_sat_bar = P_sat_mmHg * 0.00133322
        
        return max(P_sat_bar, 0.001)

    # =========================================================
    # CALCUL DES COEFFICIENTS D'ACTIVITÉ
    # =========================================================
    def calculate_activity_coefficients(
        self, 
        x1: float, 
        T: float, 
        model_name: str, 
        params: Dict
    ) -> Tuple[float, float]:
        """
        Calcule les coefficients d'activité gamma1 et gamma2
        Version robuste avec protection contre les divisions par zéro
        """
        # Protection contre les valeurs invalides
        if x1 <= 0.001:
            x1 = 0.001
        if x1 >= 0.999:
            x1 = 0.999
        if T <= 0:
            T = 298.15
        
        x = [x1, 1 - x1]
        
        try:
            if model_name == 'NRTL':
                # Paramètres NRTL
                a12 = params.get('a12', 0)
                a21 = params.get('a21', 0)
                alpha = params.get('alpha', 0.3)
                
                # Créer la matrice d'interaction
                a = [[0, a12], [a21, 0]]
                
                model = NRTLModel(alpha=alpha)
                gamma = model.calculate_activity_coefficients(x, a, T)
                
            elif model_name == 'UNIQUAC':
                # Paramètres UNIQUAC
                r = [params.get('r1', 1.0), params.get('r2', 1.0)]
                q = [params.get('q1', 1.0), params.get('q2', 1.0)]
                a12 = params.get('a12', 0)
                a21 = params.get('a21', 0)
                a = [[0, a12], [a21, 0]]
                
                model = UNIQUACModel()
                gamma = model.calculate_activity_coefficients(x, r, q, a, T)
                
            elif model_name == 'Wilson':
                # Paramètres Wilson
                V = [params.get('V1', 50.0), params.get('V2', 50.0)]
                lambda12 = params.get('lambda12', 1000)
                lambda21 = params.get('lambda21', 1000)
                lambda_params = [[0, lambda12], [lambda21, 0]]
                
                model = WilsonModel()
                gamma = model.calculate_activity_coefficients(x, lambda_params, V, T)
                
            elif model_name == 'UNIFAC':
                # Paramètres UNIFAC
                component_groups = params.get('component_groups', [{}, {}])
                group_interaction = params.get('group_interaction', [[0, 0], [0, 0]])
                
                model = UNIFACModel()
                gamma = model.calculate_activity_coefficients(x, component_groups, group_interaction, T)
                
            else:
                gamma = [1.0, 1.0]
            
            # Vérifier et corriger les valeurs NaN ou infinies
            if math.isnan(gamma[0]) or math.isinf(gamma[0]):
                gamma[0] = 1.0
            if math.isnan(gamma[1]) or math.isinf(gamma[1]):
                gamma[1] = 1.0
                
            return gamma[0], gamma[1]
            
        except Exception as e:
            print(f"Erreur dans calculate_activity_coefficients pour {model_name}: {e}")
            return 1.0, 1.0

    # =========================================================
    # BUBBLE POINT PRESSURE
    # =========================================================
    def bubble_point_pressure(
        self, 
        x: List[float], 
        T: float, 
        components: List[str],
        model: Optional[str] = None,
        model_params: Optional[Dict] = None
    ) -> Dict:
        """
        Calcule la pression de bulle
        """
        n = len(x)
        
        # Protection des fractions molaires
        x_safe = []
        for val in x:
            if val <= 0:
                x_safe.append(0.001)
            elif val >= 1:
                x_safe.append(0.999)
            else:
                x_safe.append(val)
        
        # Normaliser pour que la somme soit 1
        total = sum(x_safe)
        if total > 0:
            x_safe = [xi / total for xi in x_safe]
        
        P_sat = [self.calculate_saturation_pressure(comp, T) for comp in components]
        
        if model is None or model == 'ideal':
            gamma = [1.0, 1.0]
            partial_pressures = [x_safe[i] * P_sat[i] for i in range(n)]
            P_total = sum(partial_pressures)
            equations_used = ["Loi de Raoult: P_i = x_i · P_i^sat(T)"]
        else:
            # Calcul des coefficients d'activité
            gamma1, gamma2 = self.calculate_activity_coefficients(x_safe[0], T, model, model_params or {})
            gamma = [gamma1, gamma2]
            partial_pressures = [x_safe[i] * gamma[i] * P_sat[i] for i in range(n)]
            P_total = sum(partial_pressures)
            equations_used = [f"Loi de Raoult modifiée avec {model}"]
        
        # Éviter division par zéro pour la composition vapeur
        if P_total <= 0:
            P_total = 0.001
            y = [0.5, 0.5]
        else:
            y = [p / P_total for p in partial_pressures]
        
        return {
            'bubble_pressure': P_total,
            'vapor_composition': y,
            'activity_coefficients': gamma,
            'saturation_pressures': P_sat,
            'partial_pressures': partial_pressures,
            'model': model or 'ideal',
            'equations_used': equations_used,
            'temperature': T,
            'components': components
        }

    # =========================================================
    # GAMMA CURVE
    # =========================================================
    def generate_gamma_curve(
        self, 
        components: List[str], 
        T: float, 
        model: str, 
        model_params: Dict,
        n_points: int = 50
    ) -> Dict:
        """
        Génère la courbe des coefficients d'activité
        Version robuste avec protection contre les erreurs
        """
        x1_values = []
        gamma1_values = []
        gamma2_values = []
        ge_rt_values = []
        
        for i in range(n_points + 1):
            x1 = i / n_points
            
            # Éviter les valeurs extrêmes qui causent des problèmes
            if x1 <= 0.001:
                x1 = 0.001
            if x1 >= 0.999:
                x1 = 0.999
            
            try:
                gamma1, gamma2 = self.calculate_activity_coefficients(x1, T, model, model_params)
                
                # Vérifier les valeurs
                if math.isnan(gamma1) or math.isinf(gamma1):
                    gamma1 = 1.0
                if math.isnan(gamma2) or math.isinf(gamma2):
                    gamma2 = 1.0
                
                x1_values.append(x1)
                gamma1_values.append(gamma1)
                gamma2_values.append(gamma2)
                
                # G^E/RT = x1*ln(gamma1) + x2*ln(gamma2)
                x2 = 1 - x1
                try:
                    ge_rt = x1 * math.log(gamma1) + x2 * math.log(gamma2)
                    if math.isnan(ge_rt) or math.isinf(ge_rt):
                        ge_rt = 0.0
                except (ValueError, OverflowError):
                    ge_rt = 0.0
                ge_rt_values.append(ge_rt)
                
            except Exception as e:
                print(f"Erreur pour x1={x1}: {e}")
                x1_values.append(x1)
                gamma1_values.append(1.0)
                gamma2_values.append(1.0)
                ge_rt_values.append(0.0)
        
        return {
            'x1': x1_values,
            'gamma1': gamma1_values,
            'gamma2': gamma2_values,
            'excess_gibbs_rt': ge_rt_values,
            'temperature': T,
            'components': components,
            'model': model
        }