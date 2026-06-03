from models import db, login_manager
from flask_login import UserMixin
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import secrets
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    __tablename__ = "users"

    # ============================================
    # Colonnes principales
    # ============================================
    id                  = db.Column(db.Integer, primary_key=True)
    username            = db.Column(db.String(80),  unique=True, nullable=False)
    email               = db.Column(db.String(120), unique=True, nullable=False)
    password            = db.Column(db.String(200), nullable=False)
    role                = db.Column(db.Enum("student", "teacher", "admin"), default="student")
    
    # Profil utilisateur
    first_name          = db.Column(db.String(100), nullable=True)
    last_name           = db.Column(db.String(100), nullable=True)
    institution         = db.Column(db.String(200), nullable=True)
    avatar_url          = db.Column(db.String(500), nullable=True)
    bio                 = db.Column(db.Text, nullable=True)
    
    # Statistiques et préférences
    calculations_count  = db.Column(db.Integer, default=0)
    preferred_eos       = db.Column(db.Enum("pr", "srk", "vdw", "ideal"), default="pr")
    theme               = db.Column(db.Enum("light", "dark"), default="light")
    
    # Compte et sécurité
    is_active           = db.Column(db.Boolean, default=True)
    is_verified         = db.Column(db.Boolean, default=False, nullable=False)
    
    # === NOUVEAU - last_login ===
    last_login          = db.Column(db.DateTime, nullable=True)  # ← AJOUTER CETTE LIGNE
    
    # Timestamps
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at          = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ── Vérification email ─────────────────────────────────────────────────
    verification_token  = db.Column(db.String(100), nullable=True)
    verification_expiry = db.Column(db.DateTime, nullable=True)

    # ── Réinitialisation mot de passe ──────────────────────────────────────
    reset_token         = db.Column(db.String(100), nullable=True)
    reset_expiry        = db.Column(db.DateTime, nullable=True)
    
    # ── Bannissement ────────────────────────────────────────────────────────
    ban_reason          = db.Column(db.Text, nullable=True)
    banned_at           = db.Column(db.DateTime, nullable=True)

    # ============================================
    # Relations
    # ============================================
    calculations = db.relationship("Calculation", backref="user", lazy=True, cascade="all, delete-orphan")
    molecules = db.relationship("Molecule", backref="user", lazy=True, cascade="all, delete-orphan")

    # ============================================
    # Propriétés
    # ============================================
    
    @property
    def full_name(self) -> str:
        """Nom complet de l'utilisateur"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.username
    
    @property
    def is_admin(self) -> bool:
        """Vérifie si l'utilisateur est administrateur"""
        return self.role == "admin"
    
    @property
    def is_teacher(self) -> bool:
        """Vérifie si l'utilisateur est enseignant"""
        return self.role in ["teacher", "admin"]
    
    @property
    def is_banned(self) -> bool:
        """Vérifie si l'utilisateur est banni"""
        return not self.is_active
    
    @property
    def account_age_days(self) -> int:
        """Âge du compte en jours"""
        if self.created_at:
            delta = datetime.utcnow() - self.created_at
            return delta.days
        return 0

    # ============================================
    # Gestion des mots de passe
    # ============================================
    
    def set_password(self, password: str) -> None:
        """Hache et définit le mot de passe"""
        self.password = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """Vérifie le mot de passe"""
        return check_password_hash(self.password, password)
    
    # ============================================
    # Gestion des tokens de vérification
    # ============================================
    
    def generate_verification_token(self) -> str:
        """Génère un token de vérification valable 24h"""
        self.verification_token = secrets.token_urlsafe(32)
        self.verification_expiry = datetime.utcnow() + timedelta(hours=24)
        return self.verification_token
    
    def is_verification_token_valid(self, token: str) -> bool:
        """Vérifie la validité du token de vérification"""
        return (
            self.verification_token == token
            and self.verification_expiry is not None
            and datetime.utcnow() < self.verification_expiry
        )
    
    def verify_email(self) -> None:
        """Marque l'email comme vérifié et nettoie les tokens"""
        self.is_verified = True
        self.verification_token = None
        self.verification_expiry = None
    
    # ============================================
    # Gestion des tokens de réinitialisation
    # ============================================
    
    def generate_reset_token(self) -> str:
        """Génère un token de réinitialisation valable 1h"""
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_expiry = datetime.utcnow() + timedelta(hours=1)
        return self.reset_token
    
    def is_reset_token_valid(self, token: str) -> bool:
        """Vérifie la validité du token de réinitialisation"""
        return (
            self.reset_token == token
            and self.reset_expiry is not None
            and datetime.utcnow() < self.reset_expiry
        )
    
    def clear_reset_token(self) -> None:
        """Nettoie le token après réinitialisation"""
        self.reset_token = None
        self.reset_expiry = None
    
    # ============================================
    # Gestion de session
    # ============================================
    
    def record_login(self, ip_address: Optional[str] = None) -> None:
        """Enregistre la dernière connexion"""
        self.last_login = datetime.utcnow()
        # Si vous avez une colonne last_ip, décommentez la ligne suivante
        # if ip_address:
        #     self.last_ip = ip_address
        db.session.commit()
    
    # ============================================
    # Statistiques utilisateur
    # ============================================
    
    def increment_calculation_count(self, save: bool = True) -> None:
        """Incrémente le compteur de calculs"""
        self.calculations_count += 1
        if save:
            db.session.commit()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques de l'utilisateur"""
        from sqlalchemy import func
        
        total_calcs = self.calculations.count() if hasattr(self, 'calculations') else 0
        
        last_calc = None
        if hasattr(self, 'calculations'):
            last_calc = self.calculations.order_by(
                db.desc("created_at")
            ).first()
        
        return {
            "total_calculations": total_calcs,
            "custom_molecules": self.molecules.count() if hasattr(self, 'molecules') else 0,
            "last_calculation_date": last_calc.created_at.isoformat() if last_calc else None,
            "account_age_days": self.account_age_days,
            "is_verified": self.is_verified,
            "role": self.role,
        }
    
    # ============================================
    # Méthodes de classe
    # ============================================
    
    @classmethod
    def get_by_email(cls, email: str) -> Optional["User"]:
        """Récupère un utilisateur par son email"""
        return cls.query.filter_by(email=email).first()
    
    @classmethod
    def get_by_username(cls, username: str) -> Optional["User"]:
        """Récupère un utilisateur par son nom d'utilisateur"""
        return cls.query.filter_by(username=username).first()
    
    @classmethod
    def get_by_verification_token(cls, token: str) -> Optional["User"]:
        """Récupère un utilisateur par token de vérification"""
        return cls.query.filter_by(verification_token=token).first()
    
    @classmethod
    def get_by_reset_token(cls, token: str) -> Optional["User"]:
        """Récupère un utilisateur par token de réinitialisation"""
        return cls.query.filter_by(reset_token=token).first()
    
    @classmethod
    def get_active_users(cls, days: int = 7) -> List["User"]:
        """Retourne les utilisateurs actifs depuis X jours"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        return cls.query.filter(cls.last_login >= cutoff).all()
    
    @classmethod
    def cleanup_expired_tokens(cls) -> int:
        """Nettoie les tokens expirés"""
        now = datetime.utcnow()
        
        verified_count = cls.query.filter(
            cls.verification_expiry < now,
            cls.is_verified == False
        ).update({"verification_token": None, "verification_expiry": None})
        
        reset_count = cls.query.filter(
            cls.reset_expiry < now
        ).update({"reset_token": None, "reset_expiry": None})
        
        db.session.commit()
        return verified_count + reset_count
    
    # ============================================
    # Méthodes d'administration
    # ============================================
    
    def ban(self, reason: str = None) -> None:
        """Bannit un utilisateur"""
        self.is_active = False
        self.ban_reason = reason
        self.banned_at = datetime.utcnow()
        db.session.commit()
    
    def unban(self) -> None:
        """Lève le bannissement"""
        self.is_active = True
        self.ban_reason = None
        self.banned_at = None
        db.session.commit()
    
    def promote_to_teacher(self) -> None:
        """Promouvoit un étudiant en enseignant"""
        if self.role == "student":
            self.role = "teacher"
            db.session.commit()
    
    def promote_to_admin(self) -> None:
        """Promouvoit en administrateur (sécurité)"""
        self.role = "admin"
        db.session.commit()
    
    # ============================================
    # Sérialisation
    # ============================================
    
    def to_dict(self, sensitive: bool = False) -> Dict[str, Any]:
        """Convertit l'utilisateur en dictionnaire"""
        data = {
            "id": self.id,
            "username": self.username,
            "full_name": self.full_name,
            "role": self.role,
            "is_verified": self.is_verified,
            "is_active": self.is_active,
            "calculations_count": self.calculations_count,
            "preferred_eos": self.preferred_eos,
            "theme": self.theme,
            "institution": self.institution,
            "avatar_url": self.avatar_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
        
        if sensitive:
            data["email"] = self.email
            data["bio"] = self.bio
        
        return data
    
    # ============================================
    # Méthodes d'affichage
    # ============================================
    
    def __repr__(self) -> str:
        return f"<User {self.id}: {self.username} ({self.role})>"
    
    def __str__(self) -> str:
        return f"{self.username} ({self.email})"


# ============================================
# User loader pour Flask-Login
# ============================================
@login_manager.user_loader
def load_user(user_id: str) -> Optional[User]:
    """Charge un utilisateur depuis l'ID stocké en session"""
    try:
        return db.session.get(User, int(user_id))
    except (ValueError, TypeError):
        return None