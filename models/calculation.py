from models import db
from datetime import datetime
import json

class Calculation(db.Model):
    __tablename__ = "calculations"

    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    gas_name       = db.Column(db.String(50))
    temperature    = db.Column(db.Float, comment="Température en K")
    pressure       = db.Column(db.Float, comment="Pression en Pa")
    equations_used = db.Column(db.String(200))
    result_json    = db.Column(db.Text)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)

    calculation_type = db.Column(db.String(50), default="eos_explorer", 
                                  comment="eos_explorer, isotherm, vle, z_factor")

    def set_results(self, results_dict):
        self.result_json = json.dumps(results_dict)

    def get_results(self):
        return json.loads(self.result_json) if self.result_json else {}

    def __repr__(self):
        return f"<Calculation {self.gas_name} T={self.temperature}K P={self.pressure}Pa>"
