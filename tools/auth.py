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
from tools.utils import *
from tools.db_auth import *
from lightdb import LightDB

auth_bp = Blueprint('auth', __name__)

l_db = LightDB()

@auth_bp.route('/logout')
def logout():
    # Sign out user and redirect to upload page
    session['loggedIn'] = False
    session.pop('username', None)
    flash('Successfully signed out!', 'info')
    return redirect(url_for('upload'))

@auth_bp.route('/login', methods=['GET', 'POST'])
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

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    udb = udbload()
    
    if request.method == 'GET':
        return render_template('register.html')
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        for user in udb:
            if user['username'] == username:
                flash('Username already taken!', 'error')
                return redirect(url_for('register'))
        
        udb.append({
            'username': username,
            'password': password,
            'quota_gb': 3
        })
        
        udbsave(udb)
        flash('Successfully registered! You can now sign in.', 'info')
        return redirect(url_for('auth.login'))
    