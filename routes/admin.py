# routes/admin.py

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db
from models.user import User
from models.calculation import Calculation
from models.molecule import Molecule
from functools import wraps
from datetime import datetime, timedelta

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(f):
    """Décorateur pour vérifier que l'utilisateur est admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Veuillez vous connecter.", "warning")
            return redirect(url_for("auth.login"))
        if current_user.role != 'admin':
            flash("Accès non autorisé. Zone administrateur réservée.", "error")
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    """Dashboard admin"""
    from sqlalchemy import func
    
    # Statistiques utilisateurs
    total_users = User.query.count()
    verified_users = User.query.filter_by(is_verified=True).count()
    unverified_users = User.query.filter_by(is_verified=False).count()
    
    week_ago = datetime.utcnow() - timedelta(days=7)
    active_users = User.query.filter(User.last_login >= week_ago).count()
    inactive_users = User.query.filter_by(is_active=False).count()
    
    # Statistiques par rôle
    admins = User.query.filter_by(role='admin').count()
    teachers = User.query.filter_by(role='teacher').count()
    students = User.query.filter_by(role='student').count()
    
    # Statistiques globales
    total_calculations = Calculation.query.count()
    total_custom_gases = Molecule.query.filter(Molecule.user_id.isnot(None)).count()
    calculations_7d = Calculation.query.filter(
        Calculation.created_at >= week_ago
    ).count()
    
    # Évolution des inscriptions (7 derniers jours)
    registration_data = []
    for i in range(6, -1, -1):
        date = datetime.utcnow().date() - timedelta(days=i)
        next_date = date + timedelta(days=1)
        count = User.query.filter(
            User.created_at >= date,
            User.created_at < next_date
        ).count()
        registration_data.append({
            'date': date.strftime('%d/%m'),
            'count': count
        })
    
    stats = {
        'total_users': total_users,
        'verified_users': verified_users,
        'unverified_users': unverified_users,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'admins': admins,
        'teachers': teachers,
        'students': students,
        'total_calculations': total_calculations,
        'total_custom_gases': total_custom_gases,
        'calculations_7d': calculations_7d,
    }
    
    return render_template(
        "admin/dashboard.html",
        stats=stats,
        registration_data=registration_data
    )


@admin_bp.route("/users")
@login_required
@admin_required
def users():
    """Liste des utilisateurs"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = User.query
    
    if search:
        query = query.filter(
            db.or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        )
    
    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template(
        "admin/users.html",
        users=pagination.items,
        pagination=pagination,
        search=search
    )


@admin_bp.route("/users/<int:user_id>/toggle-verify", methods=["POST"])
@login_required
@admin_required
def toggle_verify(user_id):
    """Vérifier manuellement un utilisateur"""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        return jsonify({'error': 'Vous ne pouvez pas vous vérifier vous-même'}), 400
    
    user.is_verified = not user.is_verified
    if user.is_verified:
        user.verification_token = None
        user.verification_expiry = None
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'is_verified': user.is_verified,
        'message': f"Utilisateur {user.username} {'vérifié' if user.is_verified else 'non vérifié'}"
    })


@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
@login_required
@admin_required
def toggle_active(user_id):
    """Activer/désactiver un utilisateur"""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        return jsonify({'error': 'Vous ne pouvez pas vous désactiver vous-même'}), 400
    
    user.is_active = not user.is_active
    db.session.commit()
    
    return jsonify({
        'success': True,
        'is_active': user.is_active,
        'message': f"Compte {user.username} {'activé' if user.is_active else 'désactivé'}"
    })


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    """Supprimer un utilisateur"""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        return jsonify({'error': 'Vous ne pouvez pas vous supprimer vous-même'}), 400
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f"Utilisateur {username} supprimé"
    })


@admin_bp.route("/users/<int:user_id>/role", methods=["POST"])
@login_required
@admin_required
def change_role(user_id):
    """Changer le rôle d'un utilisateur"""
    user = User.query.get_or_404(user_id)
    new_role = request.json.get('role')
    
    if new_role not in ['student', 'teacher', 'admin']:
        return jsonify({'error': 'Rôle invalide'}), 400
    
    if user.id == current_user.id and new_role != 'admin':
        return jsonify({'error': 'Vous ne pouvez pas changer votre propre rôle'}), 400
    
    user.role = new_role
    db.session.commit()
    
    return jsonify({
        'success': True,
        'role': user.role,
        'message': f"Rôle de {user.username} changé en {new_role}"
    })