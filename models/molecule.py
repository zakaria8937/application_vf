from models import db

class Molecule(db.Model):
    __tablename__ = "molecules"

    id      = db.Column(db.Integer, primary_key=True)
    name    = db.Column(db.String(100), nullable=False)
    formula = db.Column(db.String(50))
    tc      = db.Column(db.Float, comment="Température critique (K)")
    pc      = db.Column(db.Float, comment="Pression critique (bar)")
    omega   = db.Column(db.Float, comment="Facteur acentrique")
    a_vdw   = db.Column(db.Float, comment="Constante a VdW (Pa.m6/mol2)")
    b_vdw   = db.Column(db.Float, comment="Constante b VdW (m3/mol)")
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    def to_dict(self):
        return {
            "name":    self.name,
            "formula": self.formula,
            "Tc":      self.tc,
            "Pc":      self.pc,
            "omega":   self.omega,
            "a":       self.a_vdw,
            "b":       self.b_vdw,
        }

    def __repr__(self):
        return f"<Molecule {self.name} ({self.formula})>"
