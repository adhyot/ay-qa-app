from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app.blueprints.auth import auth_bp
from app.extensions import db
from app.models.user import User
from app.models.organization import Organization
from slugify import slugify


ACCESS_PIN = '0072'


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('core.dashboard'))

    if request.method == 'POST':
        pin = request.form.get('pin', '').strip()
        if pin == ACCESS_PIN:
            user = User.query.filter_by(is_active=True).first()
            if user:
                login_user(user, remember=True)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('core.dashboard'))
        flash('Incorrect PIN. Please try again.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('core.dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        org_name = request.form.get('org_name', '').strip()

        if User.query.filter_by(email=email).first():
            flash('An account with this email already exists.', 'danger')
            return render_template('auth/register.html')

        org_slug = slugify(org_name)
        if Organization.query.filter_by(slug=org_slug).first():
            org_slug = f"{org_slug}-{email.split('@')[0]}"

        org = Organization(name=org_name, slug=org_slug)
        db.session.add(org)
        db.session.flush()

        user = User(
            email=email,
            full_name=full_name,
            org_id=org.id,
            role='admin'
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash(f'Welcome to QA Platform, {full_name}!', 'success')
        return redirect(url_for('core.dashboard'))

    return render_template('auth/register.html')
