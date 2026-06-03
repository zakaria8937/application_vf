from flask import Flask
from extensions import bcrypt 
from config import config
from models import db, login_manager
from models.user import User
from routes.main import main_bp
from routes.api import api_bp
from routes.auth import auth_bp
from routes.vle import vle_bp
from routes.admin import admin_bp
import os

def create_app(env=None):
    app = Flask(__name__)
    env = env or os.getenv("FLASK_ENV", "default")
    app.config.from_object(config[env])

    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    # Enregistrer les blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(vle_bp, url_prefix="/vle")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # Initialiser la base de données au démarrage
    with app.app_context():
        db.create_all()
        
        # Créer un admin par défaut si aucun n'existe
        admin_exists = User.query.filter_by(role='admin').first()
        if not admin_exists:
            # Utiliser bcrypt directement pour hacher le mot de passe
            hashed_password = bcrypt.generate_password_hash("Admin123!").decode("utf-8")
            
            admin = User(
                username="admin",
                email="admin@eos-compare.com",
                password=hashed_password,
                role="admin",
                is_verified=True
            )
            db.session.add(admin)
            db.session.commit()
            print("=" * 50)
            print("✅ Compte admin créé avec succès !")
            print("   Email: admin@eos-compare.com")
            print("   Mot de passe: Admin123!")
            print("=" * 50)
        else:
            print("ℹ️ Un compte admin existe déjà.")

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
