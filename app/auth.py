from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user
from .extensions import bcrypt
from app.models import User

auth = Blueprint('auth', __name__)

# -------------------- LOGIN --------------------
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.get_by_email(email)  # MongoDB lookup
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('routes.panel'))
        else:
            flash('Correo o contraseña incorrectos', 'danger')

    return render_template('login.html')

# -------------------- REGISTRO --------------------
@auth.route('/register', methods=['GET', 'POST'])
def register():
    from app.extensions import mongo  # Import aquí para evitar errores circulares

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'danger')
            return redirect(url_for('auth.register'))

        # Verificar si el usuario ya existe
        if User.get_by_email(email):
            flash('Correo ya registrado', 'danger')
            return redirect(url_for('auth.register'))

        # Hashear la contraseña y guardar el usuario en MongoDB
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        mongo.db.users.insert_one({
            "email": email,
            "password": hashed_password
        })

        flash('Usuario registrado exitosamente', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')

# -------------------- LOGOUT --------------------
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
