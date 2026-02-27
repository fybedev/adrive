from flask import (
    Blueprint,
    app,
    redirect,
    request,
    render_template,
    jsonify,
    session,
    flash,
    url_for
)
from tools.db_auth import *
from lightdb import LightDB

auth_bp = Blueprint('auth', __name__)

l_db = LightDB()

@auth_bp.route('/logout')
def logout():
    # Sign out user and redirect to upload page
    session['loggedIn'] = False
    session.pop('username', None)
    session.clear()
    flash('Successfully signed out!', 'info')
    return redirect(url_for('upload'))

@auth_bp.route('/login.old', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if check_if_auth(username, password):
            session['loggedIn'] = True
            session['username'] = username
            flash('Successfully signed in!', 'info')
            return redirect(url_for('upload'))
    
    flash('Invalid username or password!', 'error')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register.old', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if check_if_user_exists(username):
            flash('Username already exists!', 'error')
            return redirect(url_for('auth.register'))
        
        register_user(username, password, quota_gb=3)
        
        flash('Successfully registered! You can now sign in.', 'info')
        return redirect(url_for('auth.login'))
    