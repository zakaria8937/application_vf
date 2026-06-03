-- ================================================
-- DONNÉES ENRICHIES - 25+ composants industriels
-- ================================================

INSERT OR REPLACE INTO molecules (name, formula, tc, pc, omega, a_vdw, b_vdw, is_public, user_id) VALUES
-- Alcanes
('Méthane', 'CH4', 190.6, 46.1, 0.011, 0.2283, 4.301e-5, 1, NULL),
('Éthane', 'C2H6', 305.3, 48.7, 0.099, 0.5562, 6.380e-5, 1, NULL),
('Propane', 'C3H8', 369.8, 42.5, 0.153, 0.9385, 9.049e-5, 1, NULL),
('Butane', 'C4H10', 425.1, 38.0, 0.200, 1.370, 1.162e-4, 1, NULL),
('Pentane', 'C5H12', 469.7, 33.7, 0.252, 1.840, 1.424e-4, 1, NULL),
('Hexane', 'C6H14', 507.6, 30.3, 0.301, 2.380, 1.680e-4, 1, NULL),
('Heptane', 'C7H16', 540.3, 27.4, 0.350, 2.960, 1.930e-4, 1, NULL),
('Octane', 'C8H18', 568.8, 24.9, 0.398, 3.580, 2.180e-4, 1, NULL),

-- Gaz industriels
('Azote', 'N2', 126.2, 34.0, 0.039, 0.1370, 3.870e-5, 1, NULL),
('Oxygène', 'O2', 154.6, 50.4, 0.022, 0.1382, 3.186e-5, 1, NULL),
('Hydrogène', 'H2', 33.2, 13.0, -0.216, 0.02476, 2.661e-5, 1, NULL),
('Hélium', 'He', 5.2, 2.27, -0.387, 0.00346, 2.380e-5, 1, NULL),
('Argon', 'Ar', 150.9, 48.6, 0.000, 0.1367, 3.205e-5, 1, NULL),

-- Composés carbonés
('Monoxyde de carbone', 'CO', 132.9, 35.0, 0.049, 0.1471, 3.950e-5, 1, NULL),
('Dioxyde de carbone', 'CO2', 304.1, 73.8, 0.239, 0.3658, 4.286e-5, 1, NULL),

-- Composés soufrés et azotés
('Sulfure d\'hydrogène', 'H2S', 373.5, 89.6, 0.100, 0.4480, 4.280e-5, 1, NULL),
('Ammoniac', 'NH3', 405.5, 113.6, 0.250, 0.4225, 3.707e-5, 1, NULL),

-- Composés polaires
('Eau', 'H2O', 647.1, 220.6, 0.345, 0.5536, 3.049e-5, 1, NULL),
('Méthanol', 'CH3OH', 512.6, 80.9, 0.564, 0.9465, 4.270e-5, 1, NULL),
('Éthanol', 'C2H5OH', 514.0, 61.4, 0.644, 1.235, 5.430e-5, 1, NULL),
('Acétone', 'C3H6O', 508.2, 47.0, 0.307, 1.420, 7.280e-5, 1, NULL),

-- Aromatiques
('Benzène', 'C6H6', 562.2, 48.9, 0.212, 1.820, 8.410e-5, 1, NULL),
('Toluène', 'C7H8', 591.8, 41.1, 0.263, 2.450, 9.680e-5, 1, NULL);