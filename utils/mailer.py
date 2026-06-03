import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import current_app, url_for

# Configuration
MAIL_SENDER_EMAIL = os.getenv("MAIL_SENDER_EMAIL", "Eos.compare@gmail.com")
MAIL_SENDER_NAME = os.getenv("MAIL_SENDER_NAME", "EOS Compare")
MAIL_SMTP_SERVER = "smtp.gmail.com"
MAIL_SMTP_PORT = 587
MAIL_SENDER_PASSWORD = os.getenv("MAIL_PASSWORD", "EOSAPPTHERMO2026")
MAIL_ENABLED = os.getenv("MAIL_ENABLED", "true").lower() == "true"


def _send_email(to_email: str, subject: str, html_body: str) -> bool:
    """Envoie un email HTML."""
    if not MAIL_ENABLED:
        print(f"[MAIL DEBUG] Email would be sent to {to_email}: {subject}")
        return True
    
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{MAIL_SENDER_NAME} <{MAIL_SENDER_EMAIL}>"
        msg["To"] = to_email
        
        part = MIMEText(html_body, "html", "utf-8")
        msg.attach(part)
        
        with smtplib.SMTP(MAIL_SMTP_SERVER, MAIL_SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(MAIL_SENDER_EMAIL, MAIL_SENDER_PASSWORD)
            server.sendmail(MAIL_SENDER_EMAIL, to_email, msg.as_string())
        return True
    except Exception as e:
        current_app.logger.error(f"[Mailer] Erreur: {e}")
        return False


def send_verification_email(user, verify_url: str) -> bool:
    """Envoie l'email de vérification."""
    content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #06b6d4;">Vérification de votre compte EOS Compare</h2>
        <p>Bonjour <strong>{user.username}</strong>,</p>
        <p>Merci de vous être inscrit sur EOS Compare. Pour activer votre compte, veuillez cliquer sur le lien ci-dessous :</p>
        <p style="text-align: center; margin: 30px 0;">
            <a href="{verify_url}" style="background: linear-gradient(135deg, #06b6d4, #7c3aed); color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px;">Vérifier mon email</a>
        </p>
        <p>Ce lien expire dans <strong>24 heures</strong>.</p>
        <p>Si vous n'avez pas créé de compte, ignorez cet email.</p>
        <hr>
        <p style="font-size: 12px; color: #666;">EOS Compare - Équations d'État pour Gaz Réels</p>
    </div>
    """
    return _send_email(user.email, "Vérifiez votre email - EOS Compare", content)


def send_reset_password_email(user, reset_url: str) -> bool:
    """Envoie l'email de réinitialisation."""
    content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #f59e0b;">Réinitialisation de votre mot de passe</h2>
        <p>Bonjour <strong>{user.username}</strong>,</p>
        <p>Vous avez demandé la réinitialisation de votre mot de passe. Cliquez sur le lien ci-dessous :</p>
        <p style="text-align: center; margin: 30px 0;">
            <a href="{reset_url}" style="background: linear-gradient(135deg, #f59e0b, #7c3aed); color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px;">Réinitialiser mon mot de passe</a>
        </p>
        <p>Ce lien expire dans <strong>1 heure</strong>.</p>
        <p>Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.</p>
        <hr>
        <p style="font-size: 12px; color: #666;">EOS Compare - Équations d'État pour Gaz Réels</p>
    </div>
    """
    return _send_email(user.email, "Réinitialisation mot de passe - EOS Compare", content)