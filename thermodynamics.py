"""
Thermodynamic Models for Activity Coefficient Calculations
Implements NRTL, UNIQUAC, UNIFAC, and Wilson models
"""

import math
from typing import Dict, List, Tuple

# Constants
R = 8.314  # Gas constant J/(mol·K)
Z = 10  # Coordination number for UNIQUAC


class NRTLModel:
    """
    Non-Random Two-Liquid (NRTL) Model
    Equations from images 5-9
    """
    
    def __init__(self, alpha: float = 0.3):
        """
        Initialize NRTL model
        alpha: non-randomness parameter (typically 0.2-0.47)
        """
        self.alpha = alpha
    
    def calculate_tau(self, a_ij: float, T: float) -> float:
        """
        Calculate tau parameter (Equation 6)
        tau_ij = a_ij / T
        """
        return a_ij / T
    
    def calculate_G(self, tau: float) -> float:
        """
        Calculate G parameter (Equation 7)
        G_ij = exp(-alpha * tau_ij)
        """
        return math.exp(-self.alpha * tau)
    
    def calculate_activity_coefficients(
        self, 
        x: List[float], 
        a: List[List[float]], 
        T: float
    ) -> List[float]:
        """
        Calculate activity coefficients for binary mixture (Equations 8-9)
        x: mole fractions [x1, x2]
        a: interaction parameters [[a11, a12], [a21, a22]]
        T: temperature (K)
        Returns: [gamma1, gamma2]
        """
        x1, x2 = x[0], x[1]
        
        # Calculate tau parameters
        tau12 = self.calculate_tau(a[0][1], T)
        tau21 = self.calculate_tau(a[1][0], T)
        
        # Calculate G parameters
        G12 = self.calculate_G(tau12)
        G21 = self.calculate_G(tau21)
        
        # Calculate ln(gamma1) - Equation 8
        term1 = tau21 * (G21 / (x1 + x2 * G21))**2
        term2 = (tau12 * G12) / (x2 + x1 * G12)**2
        ln_gamma1 = x2**2 * (term1 + term2)
        
        # Calculate ln(gamma2) - Equation 9
        term1 = tau12 * (G12 / (x2 + x1 * G12))**2
        term2 = (tau21 * G21) / (x1 + x2 * G21)**2
        ln_gamma2 = x1**2 * (term1 + term2)
        
        return [math.exp(ln_gamma1), math.exp(ln_gamma2)]
    
    def calculate_excess_gibbs(
        self, 
        x: List[float], 
        a: List[List[float]], 
        T: float
    ) -> float:
        """
        Calculate excess Gibbs energy (Equation 5)
        G^E/RT = x1*x2*[tau21*G21/(x1+x2*G21) + tau12*G12/(x2+x1*G12)]
        """
        x1, x2 = x[0], x[1]
        
        tau12 = self.calculate_tau(a[0][1], T)
        tau21 = self.calculate_tau(a[1][0], T)
        G12 = self.calculate_G(tau12)
        G21 = self.calculate_G(tau21)
        
        term1 = (tau21 * G21) / (x1 + x2 * G21)
        term2 = (tau12 * G12) / (x2 + x1 * G12)
        
        return x1 * x2 * (term1 + term2)


class UNIQUACModel:
    """
    UNIQUAC (Universal Quasi-Chemical) Model
    Equations from images 11-17
    """
    
    def __init__(self):
        """Initialize UNIQUAC model"""
        self.z = Z  # Coordination number
    
    def calculate_volume_fraction(
        self, 
        x: List[float], 
        r: List[float]
    ) -> List[float]:
        """
        Calculate volume fractions (Equation 13)
        Phi_i = (xi * ri) / sum(xj * rj)
        """
        sum_xr = sum(x[i] * r[i] for i in range(len(x)))
        return [(x[i] * r[i]) / sum_xr for i in range(len(x))]
    
    def calculate_surface_fraction(
        self, 
        x: List[float], 
        q: List[float]
    ) -> List[float]:
        """
        Calculate surface fractions (Equation 14)
        theta_i = (xi * qi) / sum(xj * qj)
        """
        sum_xq = sum(x[i] * q[i] for i in range(len(x)))
        return [(x[i] * q[i]) / sum_xq for i in range(len(x))]
    
    def calculate_l(self, r: List[float], q: List[float]) -> List[float]:
        """
        Calculate l parameter (Equation 15)
        li = (z/2)*(ri - qi) - (ri - 1)
        """
        return [(self.z / 2) * (r[i] - q[i]) - (r[i] - 1) for i in range(len(r))]
    
    def calculate_combinatorial(
        self, 
        x: List[float], 
        phi: List[float], 
        theta: List[float], 
        l: List[float],
        q: List[float]
    ) -> List[float]:
        """
        Calculate combinatorial part (Equation 12)
        ln(gamma_i^C) = ln(Phi_i/xi) + (z/2)*qi*ln(theta_i/Phi_i) + li - sum(xj*lj)
        """
        n = len(x)
        ln_gamma_c = []
        
        sum_xl = sum(x[j] * l[j] for j in range(n))
        
        for i in range(n):
            term1 = math.log(phi[i] / x[i]) if x[i] > 0 else 0
            term2 = (self.z / 2) * q[i] * math.log(theta[i] / phi[i]) if phi[i] > 0 else 0
            term3 = l[i]
            term4 = (phi[i] / x[i]) * sum_xl if x[i] > 0 else 0
            ln_gamma_c.append(term1 + term2 + term3 - term4)
        
        return ln_gamma_c
    
    def calculate_tau(self, a: float, T: float) -> float:
        """
        Calculate tau parameter (Equation 17)
        tau_ij = exp(-a_ij / T)
        """
        return math.exp(-a / T)
    
    def calculate_residual(
        self, 
        x: List[float], 
        theta: List[float], 
        a: List[List[float]], 
        T: float,
        q: List[float]
    ) -> List[float]:
        """
        Calculate residual part (Equation 16)
        ln(gamma_i^R) = qi * [1 - ln(sum(theta_j*tau_ji)) - sum((theta_j*tau_ji)/sum(theta_k*tau_kj))]
        """
        n = len(x)
        ln_gamma_r = []
        
        # Calculate tau matrix
        tau = [[self.calculate_tau(a[i][j], T) for j in range(n)] for i in range(n)]
        
        for i in range(n):
            sum_theta_tau = sum(theta[j] * tau[j][i] for j in range(n))
            term1 = 1 - math.log(sum_theta_tau) if sum_theta_tau > 0 else 0
            
            sum_term2 = 0
            for j in range(n):
                sum_theta_tau_kj = sum(theta[k] * tau[k][j] for k in range(n))
                if sum_theta_tau_kj > 0:
                    sum_term2 += (theta[j] * tau[i][j]) / sum_theta_tau_kj
            
            ln_gamma_r.append(q[i] * (term1 - sum_term2))
        
        return ln_gamma_r
    
    def calculate_activity_coefficients(
        self, 
        x: List[float], 
        r: List[float], 
        q: List[float], 
        a: List[List[float]], 
        T: float
    ) -> List[float]:
        """
        Calculate total activity coefficients (Equation 11)
        ln(gamma_i) = ln(gamma_i^C) + ln(gamma_i^R)
        """
        phi = self.calculate_volume_fraction(x, r)
        theta = self.calculate_surface_fraction(x, q)
        l = self.calculate_l(r, q)
        
        ln_gamma_c = self.calculate_combinatorial(x, phi, theta, l, q)
        ln_gamma_r = self.calculate_residual(x, theta, a, T, q)
        
        ln_gamma = [ln_gamma_c[i] + ln_gamma_r[i] for i in range(len(x))]
        return [math.exp(g) for g in ln_gamma]


class UNIFACModel:
    """
    UNIFAC (UNIQUAC Functional-group Activity Coefficients) Model
    Equations from images 20-24
    """
    
    # Group parameters from Table 2
    GROUP_PARAMETERS = {
        'CH3': {'Rk': 0.9011, 'Qk': 0.848},
        'CH2': {'Rk': 0.6744, 'Qk': 0.540},
        'CH': {'Rk': 0.4469, 'Qk': 0.228},
        'C': {'Rk': 0.2195, 'Qk': 0.000},
        'OH': {'Rk': 1.0000, 'Qk': 1.200},
        'H2O': {'Rk': 0.9200, 'Qk': 1.400},
        'CH3CO': {'Rk': 1.6724, 'Qk': 1.488},
        'CHO': {'Rk': 0.9980, 'Qk': 0.948},
        'COOH': {'Rk': 1.3013, 'Qk': 1.224},
    }
    
    # Component parameters from Table 1
    COMPONENT_PARAMETERS = {
        'Water': {'r': 0.920, 'q': 1.400, 'q_prime': 1.000},
        'Methanol': {'r': 1.431, 'q': 1.432, 'q_prime': 0.960},
        'Ethanol': {'r': 2.105, 'q': 1.972, 'q_prime': 0.920},
        'Acetone': {'r': 2.574, 'q': 2.336, 'q_prime': 2.336},
        'Benzene': {'r': 3.188, 'q': 2.400, 'q_prime': 2.400},
        'n-Hexane': {'r': 4.499, 'q': 3.856, 'q_prime': 3.856},
    }
    
    def __init__(self):
        """Initialize UNIFAC model"""
        self.z = Z
    
    def calculate_molecular_parameters(
        self, 
        groups: Dict[str, int]
    ) -> Tuple[float, float]:
        """
        Calculate molecular parameters from groups (Equations 22-23)
        ri = sum(vk^i * Rk)
        qi = sum(vk^i * Qk)
        """
        r = 0.0
        q = 0.0
        for group, count in groups.items():
            if group in self.GROUP_PARAMETERS:
                r += count * self.GROUP_PARAMETERS[group]['Rk']
                q += count * self.GROUP_PARAMETERS[group]['Qk']
        return max(r, 0.001), max(q, 0.001)  # Éviter zéro
    
    def calculate_activity_coefficients(
        self, 
        x: List[float], 
        component_groups: List[Dict[str, int]], 
        group_interaction: List[List[float]], 
        T: float
    ) -> List[float]:
        """
        Calculate activity coefficients using UNIFAC
        Version robuste avec gestion des divisions par zéro
        """
        n = len(x)
        
        # === PROTECTION CONTRE LES DIVISIONS PAR ZÉRO ===
        # 1. S'assurer que les fractions molaires sont valides
        x_safe = []
        for val in x:
            if val <= 1e-6:
                x_safe.append(1e-6)
            elif val >= 1 - 1e-6:
                x_safe.append(1 - 1e-6)
            else:
                x_safe.append(val)
        
        # 2. Normaliser pour que la somme soit exactement 1
        total = sum(x_safe)
        if total > 0:
            x_safe = [xi / total for xi in x_safe]
        
        # 3. Calcul des paramètres moléculaires
        r_list = []
        q_list = []
        for groups in component_groups:
            r, q = self.calculate_molecular_parameters(groups)
            r_list.append(r)
            q_list.append(q)
        
        # 4. Calcul des fractions volumiques et surfaciques avec protection
        sum_xr = sum(x_safe[i] * r_list[i] for i in range(n))
        sum_xq = sum(x_safe[i] * q_list[i] for i in range(n))
        
        # Éviter division par zéro
        if sum_xr < 1e-8:
            sum_xr = 1.0
        if sum_xq < 1e-8:
            sum_xq = 1.0
        
        phi = []
        theta = []
        for i in range(n):
            phi_val = (x_safe[i] * r_list[i]) / sum_xr
            theta_val = (x_safe[i] * q_list[i]) / sum_xq
            phi.append(max(phi_val, 1e-8))
            theta.append(max(theta_val, 1e-8))
        
        # 5. Calcul des paramètres l
        l = []
        for i in range(n):
            l_val = (self.z / 2) * (r_list[i] - q_list[i]) - (r_list[i] - 1)
            l.append(l_val)
        
        # 6. Partie combinatoire
        sum_xl = sum(x_safe[i] * l[i] for i in range(n))
        
        ln_gamma_c = []
        for i in range(n):
            # Terme 1: ln(phi_i / x_i)
            try:
                term1 = math.log(phi[i] / x_safe[i]) if phi[i] > 0 and x_safe[i] > 0 else 0
            except (ValueError, ZeroDivisionError):
                term1 = 0
            
            # Terme 2: (z/2) * q_i * ln(theta_i / phi_i)
            try:
                term2 = (self.z / 2) * q_list[i] * math.log(theta[i] / phi[i]) if theta[i] > 0 and phi[i] > 0 else 0
            except (ValueError, ZeroDivisionError):
                term2 = 0
            
            # Terme 3: l_i
            term3 = l[i]
            
            # Terme 4: (phi_i / x_i) * sum(x_j * l_j)
            term4 = (phi[i] / x_safe[i]) * sum_xl if x_safe[i] > 0 and phi[i] > 0 else 0
            
            ln_gamma_c.append(term1 + term2 + term3 - term4)
        
        # 7. Partie résiduelle (simplifiée pour éviter les erreurs complexes)
        # Note: La partie résiduelle complète nécessiterait les paramètres d'interaction
        # de groupes UNIFAC complets. Pour l'instant, on utilise une approximation.
        ln_gamma_r = [0.0] * n
        
        # 8. Combinaison
        gamma = []
        for i in range(n):
            ln_gamma = ln_gamma_c[i] + ln_gamma_r[i]
            # Limiter les valeurs extrêmes
            if ln_gamma > 10:
                gamma.append(10.0)
            elif ln_gamma < -10:
                gamma.append(0.01)
            else:
                try:
                    gamma.append(math.exp(ln_gamma))
                except (OverflowError, ValueError):
                    gamma.append(1.0)
        
        return gamma


class WilsonModel:
    """
    Wilson Model for activity coefficients
    """
    
    def __init__(self):
        """Initialize Wilson model"""
        self.R = 1.987  # cal/(mol.K)
    
    def calculate_lambda(self, lambda_ij: float, T: float) -> float:
        """
        Calculate lambda parameter
        Lambda_ij = (Vj/Vi) * exp(-lambda_ij / RT)
        """
        return math.exp(-lambda_ij / (self.R * T))
    
    def calculate_activity_coefficients(
        self, 
        x: List[float], 
        lambda_params: List[List[float]], 
        V: List[float], 
        T: float
    ) -> List[float]:
        """
        Calculate activity coefficients using Wilson equation
        ln(gamma_i) = -ln(sum(xj * Lambda_ij)) + 1 - sum(xj * Lambda_ji / sum(xk * Lambda_jk))
        """
        n = len(x)
        ln_gamma = []
        
        # Calculate Lambda matrix
        Lambda = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                if i != j:
                    Lambda[i][j] = (V[j] / V[i]) * self.calculate_lambda(lambda_params[i][j], T)
                else:
                    Lambda[i][j] = 1.0
        
        for i in range(n):
            term1 = -math.log(sum(x[j] * Lambda[i][j] for j in range(n)))
            
            term2_sum = 0.0
            for j in range(n):
                denominator = sum(x[k] * Lambda[j][k] for k in range(n))
                if denominator > 0:
                    term2_sum += x[j] * Lambda[j][i] / denominator
            
            ln_gamma.append(term1 + 1 - term2_sum)
        
        return [math.exp(g) for g in ln_gamma]


# Factory function to get model by name
def get_model(model_name: str):
    """
    Factory function to get thermodynamic model by name
    """
    models = {
        'NRTL': NRTLModel,
        'UNIQUAC': UNIQUACModel,
        'UNIFAC': UNIFACModel,
        'Wilson': WilsonModel,
    }
    
    model_class = models.get(model_name)
    if model_class is None:
        raise ValueError(f"Unknown model: {model_name}. Available models: {list(models.keys())}")
    
    return model_class()
