from flask import (Blueprint, render_template, redirect, url_for,
                   request, flash)
from flask_login import login_user, logout_user, login_required, current_user
from models import db
from models.user import User
from extensions import bcrypt
from utils.mailer import send_verification_email, send_reset_password_email
from datetime import datetime  
from functools import wraps
import time
import re

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            if not user.is_verified:
                flash(
                    "Votre email n'est pas encore vérifié. "
                    "Vérifiez votre boîte mail ou renvoyez le lien.",
                    "warning"
                )
                return render_template("auth/login.html", unverified_email=email)
            
            user.last_login = datetime.utcnow()
            db.session.commit()  # Sauvegarde la date de dernière connexion


            login_user(user, remember=True)
            flash(f"Salut {user.username} 👋", "success")
            next_page = request.args.get("next")
            if not next_page or not next_page.startswith("/"):
                next_page = url_for("main.index")
            return redirect(next_page)

        flash("Email ou mot de passe invalide.", "error")

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email    = request.form.get("email",    "").strip()
        password = request.form.get("password", "")

        if User.query.filter_by(email=email).first():
            flash("Cet email est déjà utilisé.", "error")
            return render_template("auth/register.html")

        if User.query.filter_by(username=username).first():
            flash("Ce nom d'utilisateur est déjà pris.", "error")
            return render_template("auth/register.html")

        if len(password) < 6:
            flash("Le mot de passe doit contenir au moins 6 caractères.", "error")
            return render_template("auth/register.html")

        hashed = bcrypt.generate_password_hash(password).decode("utf-8")
        user   = User(username=username, email=email, password=hashed)
        token  = user.generate_verification_token()

        db.session.add(user)
        db.session.commit()

        verify_url = url_for("auth.verify_email", token=token, _external=True)
        mail_sent  = send_verification_email(user, verify_url)

        if mail_sent:
            flash(
                f"Compte créé ! Un email de vérification a été envoyé à {email}. "
                "Vérifiez votre boîte mail (et les spams).",
                "success"
            )
        else:
            flash(
                "Compte créé, mais l'email de vérification n'a pas pu être envoyé. "
                "Contactez le support.",
                "warning"
            )

        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/verify/<token>")
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()

    if not user:
        flash("Lien de vérification invalide.", "error")
        return redirect(url_for("auth.login"))

    if not user.is_verification_token_valid(token):
        flash("Ce lien a expiré. Connectez-vous pour en recevoir un nouveau.", "warning")
        return redirect(url_for("auth.login"))

    user.is_verified         = True
    user.verification_token  = None
    user.verification_expiry = None
    db.session.commit()

    flash("Email vérifié avec succès ! Vous pouvez maintenant vous connecter.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/resend-verification", methods=["GET", "POST"])
def resend_verification():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        user  = User.query.filter_by(email=email).first()

        if user and not user.is_verified:
            token      = user.generate_verification_token()
            db.session.commit()
            verify_url = url_for("auth.verify_email", token=token, _external=True)
            send_verification_email(user, verify_url)

        flash(
            "Si cet email correspond à un compte non vérifié, un nouveau lien "
            "vient d'être envoyé.",
            "info"
        )
        return redirect(url_for("auth.login"))

    prefill = request.args.get("email", "")
    return render_template("auth/resend_verification.html", prefill_email=prefill)


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        user  = User.query.filter_by(email=email).first()

        if user and user.is_verified:
            token     = user.generate_reset_token()
            db.session.commit()
            reset_url = url_for("auth.reset_password", token=token, _external=True)
            send_reset_password_email(user, reset_url)

        flash(
            "Si cet email est associé à un compte vérifié, un lien de "
            "réinitialisation a été envoyé.",
            "info"
        )
        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    user = User.query.filter_by(reset_token=token).first()

    if not user or not user.is_reset_token_valid(token):
        flash("Ce lien est invalide ou a expiré. Faites une nouvelle demande.", "error")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        password  = request.form.get("password",  "")
        password2 = request.form.get("password2", "")

        if len(password) < 6:
            flash("Le mot de passe doit contenir au moins 6 caractères.", "error")
            return render_template("auth/reset_password.html", token=token)

        if password != password2:
            flash("Les mots de passe ne correspondent pas.", "error")
            return render_template("auth/reset_password.html", token=token)

        user.password    = bcrypt.generate_password_hash(password).decode("utf-8")
        user.reset_token  = None
        user.reset_expiry = None
        db.session.commit()

        flash("Mot de passe modifié avec succès ! Vous pouvez vous connecter.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", token=token)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Vous avez été déconnecté.", "info")
    return redirect(url_for("auth.login"))

@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """Page de profil utilisateur"""
    if request.method == "POST":
        current_user.first_name = request.form.get("first_name", "")
        current_user.last_name = request.form.get("last_name", "")
        current_user.institution = request.form.get("institution", "")
        current_user.bio = request.form.get("bio", "")
        db.session.commit()
        flash("Profil mis à jour avec succès.", "success")
        return redirect(url_for("auth.profile"))
    
    return render_template("auth/profile.html", user=current_user)


@auth_bp.route("/change-password-page")
@login_required
def change_password_page():
    """Page de changement de mot de passe"""
    return render_template("auth/change_password.html")


@auth_bp.route("/change-password", methods=["POST"])
@login_required
def change_password():
    """Changer le mot de passe"""
    current_password = request.form.get("current_password")
    new_password = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")
    
    if not current_user.check_password(current_password):
        flash("Mot de passe actuel incorrect.", "error")
        return redirect(url_for("auth.change_password_page"))
    
    if len(new_password) < 6:
        flash("Le nouveau mot de passe doit contenir au moins 6 caractères.", "error")
        return redirect(url_for("auth.change_password_page"))
    
    if new_password != confirm_password:
        flash("Les nouveaux mots de passe ne correspondent pas.", "error")
        return redirect(url_for("auth.change_password_page"))
    
    current_user.set_password(new_password)
    db.session.commit()
    flash("Mot de passe modifié avec succès.", "success")
    return redirect(url_for("auth.profile"))
