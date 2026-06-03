# Base de données des gaz avec leurs propriétés critiques
# Tc (K), Pc (bar), omega (facteur acentrique), a_vdw (Pa.m6/mol2), b_vdw (m3/mol)

R = 8.314  # Constante des gaz parfaits

def calculate_vdw_params(Tc, Pc):
    """Calcule a et b de Van der Waals à partir de Tc et Pc"""
    Pc_pa = Pc * 1e5
    a = (27/64) * (R**2 * Tc**2 / Pc_pa)
    b = (1/8) * (R * Tc / Pc_pa)
    return a, b

GAS_DB = {
    # ========== ALCANES ==========
    "methane": {
        "name": "Méthane",
        "formula": "CH4",
        "Tc": 190.6,
        "Pc": 46.1,
        "omega": 0.011,
        "a": 0.2283,
        "b": 4.301e-5,
    },
    "ethane": {
        "name": "Éthane",
        "formula": "C2H6",
        "Tc": 305.3,
        "Pc": 48.7,
        "omega": 0.099,
        "a": 0.5562,
        "b": 6.380e-5,
    },
    "propane": {
        "name": "Propane",
        "formula": "C3H8",
        "Tc": 369.8,
        "Pc": 42.5,
        "omega": 0.153,
        "a": 0.9385,
        "b": 9.049e-5,
    },
    "butane": {
        "name": "Butane",
        "formula": "C4H10",
        "Tc": 425.1,
        "Pc": 38.0,
        "omega": 0.200,
        "a": 1.370,
        "b": 1.162e-4,
    },
    "pentane": {
        "name": "Pentane",
        "formula": "C5H12",
        "Tc": 469.7,
        "Pc": 33.7,
        "omega": 0.252,
        "a": 1.840,
        "b": 1.424e-4,
    },
    "hexane": {
        "name": "Hexane",
        "formula": "C6H14",
        "Tc": 507.6,
        "Pc": 30.3,
        "omega": 0.301,
        "a": 2.380,
        "b": 1.680e-4,
    },
    "heptane": {
        "name": "Heptane",
        "formula": "C7H16",
        "Tc": 540.3,
        "Pc": 27.4,
        "omega": 0.350,
        "a": 2.960,
        "b": 1.930e-4,
    },
    "octane": {
        "name": "Octane",
        "formula": "C8H18",
        "Tc": 568.8,
        "Pc": 24.9,
        "omega": 0.398,
        "a": 3.580,
        "b": 2.180e-4,
    },
    
    # ========== GAZ INDUSTRIELS ==========
    "n2": {
        "name": "Azote",
        "formula": "N2",
        "Tc": 126.2,
        "Pc": 34.0,
        "omega": 0.039,
        "a": 0.1370,
        "b": 3.870e-5,
    },
    "o2": {
        "name": "Oxygène",
        "formula": "O2",
        "Tc": 154.6,
        "Pc": 50.4,
        "omega": 0.022,
        "a": 0.1382,
        "b": 3.186e-5,
    },
    "h2": {
        "name": "Hydrogène",
        "formula": "H2",
        "Tc": 33.2,
        "Pc": 13.0,
        "omega": -0.216,
        "a": 0.02476,
        "b": 2.661e-5,
    },
    "helium": {
        "name": "Hélium",
        "formula": "He",
        "Tc": 5.2,
        "Pc": 2.27,
        "omega": -0.387,
        "a": 0.00346,
        "b": 2.380e-5,
    },
    "argon": {
        "name": "Argon",
        "formula": "Ar",
        "Tc": 150.9,
        "Pc": 48.6,
        "omega": 0.000,
        "a": 0.1367,
        "b": 3.205e-5,
    },
    
    # ========== COMPOSÉS CARBONÉS ==========
    "co": {
        "name": "Monoxyde de carbone",
        "formula": "CO",
        "Tc": 132.9,
        "Pc": 35.0,
        "omega": 0.049,
        "a": 0.1471,
        "b": 3.950e-5,
    },
    "co2": {
        "name": "Dioxyde de carbone",
        "formula": "CO2",
        "Tc": 304.1,
        "Pc": 73.8,
        "omega": 0.239,
        "a": 0.3658,
        "b": 4.286e-5,
    },
    
    # ========== COMPOSÉS SOUFRÉS ET AZOTÉS ==========
    "h2s": {
        "name": "Sulfure d'hydrogène",
        "formula": "H2S",
        "Tc": 373.5,
        "Pc": 89.6,
        "omega": 0.100,
        "a": 0.4480,
        "b": 4.280e-5,
    },
    "nh3": {
        "name": "Ammoniac",
        "formula": "NH3",
        "Tc": 405.5,
        "Pc": 113.6,
        "omega": 0.250,
        "a": 0.4225,
        "b": 3.707e-5,
    },
    
    # ========== COMPOSÉS POLAIRES ==========
    "h2o": {
        "name": "Eau",
        "formula": "H2O",
        "Tc": 647.1,
        "Pc": 220.6,
        "omega": 0.345,
        "a": 0.5536,
        "b": 3.049e-5,
    },
    "methanol": {
        "name": "Méthanol",
        "formula": "CH3OH",
        "Tc": 512.6,
        "Pc": 80.9,
        "omega": 0.564,
        "a": 0.9465,
        "b": 4.270e-5,
    },
    "ethanol": {
        "name": "Éthanol",
        "formula": "C2H5OH",
        "Tc": 514.0,
        "Pc": 61.4,
        "omega": 0.644,
        "a": 1.235,
        "b": 5.430e-5,
    },
    "acetone": {
        "name": "Acétone",
        "formula": "C3H6O",
        "Tc": 508.2,
        "Pc": 47.0,
        "omega": 0.307,
        "a": 1.420,
        "b": 7.280e-5,
    },
    
    # ========== AROMATIQUES ==========
    "benzene": {
        "name": "Benzène",
        "formula": "C6H6",
        "Tc": 562.2,
        "Pc": 48.9,
        "omega": 0.212,
        "a": 1.820,
        "b": 8.410e-5,
    },
    "toluene": {
        "name": "Toluène",
        "formula": "C7H8",
        "Tc": 591.8,
        "Pc": 41.1,
        "omega": 0.263,
        "a": 2.450,
        "b": 9.680e-5,
    },
}


def get_gas_list():
    """Retourne la liste des gaz disponibles pour les menus déroulants"""
    return [
        {"key": key, "name": gas["name"], "formula": gas["formula"]}
        for key, gas in GAS_DB.items()
    ]


def get_gas_by_key(key):
    """Récupère un gaz par sa clé"""
    return GAS_DB.get(key)


def get_gas_by_formula(formula):
    """Récupère un gaz par sa formule"""
    for key, gas in GAS_DB.items():
        if gas["formula"] == formula:
            return gas
    return None