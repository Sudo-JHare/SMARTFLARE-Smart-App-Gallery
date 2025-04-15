#app/auth.py

import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db, oauth
from app.models import User
from app.forms import LoginForm, RegisterForm
from werkzeug.security import generate_password_hash

auth_bp = Blueprint('auth', __name__)

# OAuth setup
google = None
github = None

# Initialize Google OAuth only if valid credentials are provided
if os.getenv('GOOGLE_CLIENT_ID') and os.getenv('GOOGLE_CLIENT_SECRET') and \
   os.getenv('GOOGLE_CLIENT_ID') != 'your-google-client-id' and \
   os.getenv('GOOGLE_CLIENT_SECRET') != 'your-google-client-secret':
    google = oauth.remote_app(
        'google',
        consumer_key=os.getenv('GOOGLE_CLIENT_ID'),
        consumer_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        request_token_params={'scope': 'email profile'},
        base_url='https://www.googleapis.com/oauth2/v1/',
        request_token_url=None,
        access_token_method='POST',
        access_token_url='https://accounts.google.com/o/oauth2/token',
        authorize_url='https://accounts.google.com/o/oauth2/auth',
    )

# Initialize GitHub OAuth only if valid credentials are provided
if os.getenv('GITHUB_CLIENT_ID') and os.getenv('GITHUB_CLIENT_SECRET'):
    github = oauth.remote_app(
        'github',
        consumer_key=os.getenv('GITHUB_CLIENT_ID'),
        consumer_secret=os.getenv('GITHUB_CLIENT_SECRET'),
        request_token_params={'scope': 'user:email'},
        base_url='https://api.github.com/',
        request_token_url=None,
        access_token_method='POST',
        access_token_url='https://github.com/login/oauth/access_token',
        authorize_url='https://github.com/login/oauth/authorize',
    )

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('gallery.gallery'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('gallery.gallery'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('gallery.gallery'))
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered.', 'danger')
            return render_template('register_user.html', form=form)
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already taken.', 'danger')
            return render_template('register_user.html', form=form)
        user = User(
            username=form.username.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('Registration successful! You are now logged in.', 'success')
        return redirect(url_for('gallery.gallery'))
    return render_template('register_user.html', form=form)

@auth_bp.route('/login/google')
def login_google():
    if not google:
        flash('Google login is not configured.', 'danger')
        return redirect(url_for('auth.login'))
    return google.authorize(callback=url_for('auth.google_authorized', _external=True))

@auth_bp.route('/login/google/authorized')
def google_authorized():
    if not google:
        flash('Google login is not configured.', 'danger')
        return redirect(url_for('auth.login'))
    resp = google.authorized_response()
    if resp is None or resp.get('access_token') is None:
        flash('Google login failed.', 'danger')
        return redirect(url_for('auth.login'))
    session['google_token'] = (resp['access_token'], '')
    user_info = google.get('userinfo').data
    user = User.query.filter_by(oauth_provider='google', oauth_id=user_info['id']).first()
    if not user:
        email = user_info.get('email')
        if not email:
            flash('Google account has no verified email.', 'danger')
            return redirect(url_for('auth.login'))
        user = User(
            username=email.split('@')[0],
            email=email,
            oauth_provider='google',
            oauth_id=user_info['id']
        )
        db.session.add(user)
        db.session.commit()
    login_user(user)
    flash('Logged in with Google!', 'success')
    return redirect(url_for('gallery.gallery'))

@auth_bp.route('/login/github')
def login_github():
    if not github:
        flash('GitHub login is not configured.', 'danger')
        return redirect(url_for('auth.login'))
    return github.authorize(callback=url_for('auth.github_authorized', _external=True))

@auth_bp.route('/login/github/authorized')
def github_authorized():
    if not github:
        flash('GitHub login is not configured.', 'danger')
        return redirect(url_for('auth.login'))
    resp = github.authorized_response()
    if resp is None or resp.get('access_token') is None:
        flash('GitHub login failed.', 'danger')
        return redirect(url_for('auth.login'))
    session['github_token'] = (resp['access_token'], '')
    user_info = github.get('user').data
    emails = github.get('user/emails').data
    primary_email = None
    for email in emails:
        if email.get('primary') and email.get('verified'):
            primary_email = email['email']
            break
    if not primary_email:
        primary_email = f"{user_info['login']}@github.com"
    user = User.query.filter_by(oauth_provider='github', oauth_id=str(user_info['id'])).first()
    if not user:
        user = User(
            username=user_info['login'],
            email=primary_email,
            oauth_provider='github',
            oauth_id=str(user_info['id'])
        )
        db.session.add(user)
        db.session.commit()
    login_user(user)
    flash('Logged in with GitHub!', 'success')
    return redirect(url_for('gallery.gallery'))

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('gallery.gallery'))

# Define token getters only if OAuth is configured
if google:
    @google.tokengetter
    def get_google_oauth_token():
        return session.get('google_token')

if github:
    @github.tokengetter
    def get_github_oauth_token():
        return session.get('github_token')