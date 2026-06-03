# EOS Compare — Application de Comparaison des Équations d'État

## Installation

```bash
pip install -r requirements.txt
```

## Lancer l'application

```bash
python app.py
```
Puis ouvrir : http://localhost:5000

## Structure du projet

```
eos_compare/
├── app.py              ← Point d'entrée Flask
├── config.py           ← Configuration
├── requirements.txt    ← Dépendances Python
├── core/               ← Moteur de calcul scientifique
│   ├── gas_database.py ← Données des 8 gaz
│   ├── eos_solver.py   ← 4 équations d'état (GP, VdW, SRK, PR)
│   ├── isotherms.py    ← Courbes P(Vm)
│   └── z_factor.py     ← Facteur de compressibilité Z
├── models/             ← Base de données SQLAlchemy
├── routes/             ← Routes Flask
├── templates/          ← Pages HTML
└── static/             ← CSS + JavaScript
```

## Modules disponibles
- **EOS Explorer** : Comparer Vm et Z pour T et P donnés
- **Isothermes** : Courbes P-V pour plusieurs températures
- **Facteur Z** : Compressibilité en fonction de la pression
- **Propriétés** : Base de données des gaz
