from flask import (
    Flask,
    render_template,
    session,
    request,
    url_for,
    send_from_directory,
    flash
)
from utils import redirect, dbload, dbsave, udbload, udbsave
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

import os
import random
import threading
import time

import logging
import logging.handlers


app = Flask('adrive', static_folder='static', template_folder='templates')
app.config['UPLOAD_DIRECTORY'] = 'uploads/'
app.config['MAX_CONTENT_LENGTH'] = 1000000 * 1024 * 1024
app.config['SECRET_KEY'] = str(random.randint(99999, 9999999))

# Redirect logs to the file 'logs'
handler = logging.handlers.RotatingFileHandler('logs', maxBytes=1024 * 1024)
logging.getLogger('werkzeug').setLevel(logging.DEBUG)
logging.getLogger('werkzeug').addHandler(handler)
app.logger.setLevel(logging.WARNING)
app.logger.addHandler(handler)

@app.route('/')
def index():
    return redirect(url_for('upload'))

@app.route('/dashboard')
def dashboard():
    # Load Databases
    db = dbload()
    udb = udbload()
    
    # Check if user is a guest
    if session.get('loggedIn', False) == False:
        flash('You must be signed in to view the dashboard!', 'error')
        return redirect(url_for('upload'))
    
    # Get user quota, usage, and files
    username = session.get('username')
    userfiles = []
    quota_usage_gb = 0
    
    if not username:
        flash('An error occurred. Please sign in again.', 'error')
        session['loggedIn'] = False
        session.pop('username', None)
        return redirect(url_for('upload'))
    
    for file in db['files']:
        if db['files'][file].get('owner') == username:
            db['files'][file]['file'] = file
            db['files'][file]['code'] = file.split('_')[-1]
            userfiles.append(db['files'][file])
            
    for userfile in userfiles:
        usf_mb = userfile['size_megabytes']
        if usf_mb:
            quota_usage_gb += usf_mb / 1024
            
    quota_usage_gb = round(quota_usage_gb, 1)
    
    # Render template with variables
    return render_template(
        'dashboard.html',
        files=userfiles,
        username=username,
        quota_gb=udb[[user['username'] for user in udb].index(username)]['quota_gb'],
        quota_usage=quota_usage_gb
    )

@app.route('/logout')
def logout():
    # Sign out user and redirect to upload page
    session['loggedIn'] = False
    session.pop('username', None)
    flash('Successfully signed out!', 'info')
    return redirect(url_for('upload'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Load User Database (UDB)
    udb = udbload()
    
    if request.method == 'GET':
        return render_template('login.html')
    if request.method == 'POST':
        # Get data from form
        username = request.form.get('username')
        password = request.form.get('password')

        # Check if user exists and password matches, log them in
        for user in udb:
            if user['username'] == username and user['password'] == password:
                session['loggedIn'] = True
                session['username'] = username
                flash('Successfully signed in!', 'info')
                return redirect(url_for('upload'))
    
    # If still here, login failed
    flash('Invalid username or password!', 'error')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Load User Database (UDB)
    udb = udbload()
    
    if request.method == 'GET':
        return render_template('register.html')
    if request.method == 'POST':
        # Get data from form
        username = request.form.get('username')
        password = request.form.get('password')

        # Check if username is already taken
        for user in udb:
            if user['username'] == username:
                flash('Username already taken!', 'error')
                return redirect(url_for('register'))
        
        # Create new user with default quota of 3GB
        udb.append({
            'username': username,
            'password': password,
            'quota_gb': 3
        })
        
        udbsave(udb)
        flash('Successfully registered! You can now sign in.', 'info')
        return redirect(url_for('login'))

@app.route('/upload')
def upload():
    loggedIn = session.get('loggedIn', False)
    username = session.get('username', '')
    quota_gb = None
    quota_usage_gb = 0.0
    try:
        if loggedIn and username:
            db = dbload()
            udb = udbload()
            # find user record in udb
            user_rec = None
            for u in udb:
                if u.get('username') == username:
                    user_rec = u
                    break
            if user_rec:
                quota_gb = user_rec.get('quota_gb', 0)
            else:
                quota_gb = 0
            userfiles = []
            for file in db.get('files', {}):
                if db['files'][file].get('owner') == username:
                    userfiles.append(db['files'][file])
            for userfile in userfiles:
                usf_mb = userfile.get('size_megabytes', 0)
                if usf_mb:
                    quota_usage_gb += usf_mb / 1024
            quota_usage_gb = round(quota_usage_gb, 1)
        else:
            # not logged in: treat as guest with 1GB manageable quota
            quota_gb = 5.0
            quota_usage_gb = 0.0
    except Exception:
        quota_gb = quota_gb or 0
        quota_usage_gb = quota_usage_gb or 0.0

    return render_template('upload.html', loggedIn=loggedIn, username=username, quota_gb=quota_gb, quota_usage=quota_usage_gb)

@app.route('/sendfile', methods=['POST'])
def sendfile():
        db = dbload()
        file = request.files['file']
        reusable = request.form.get('reusable')
        loggedIn = session.get('loggedIn', False)
        username = session.get('username', '')


        if file:
            try:
                extension = os.path.splitext(file.filename)[1].lower()

                fileid = str(random.randint(100000, 99999999))
                dest_name = secure_filename(file.filename) + f'_{fileid}'
                dest_path = os.path.join(app.config['UPLOAD_DIRECTORY'], dest_name)

                # save file first, then inspect size on disk
                file.save(dest_path)
                print(dest_name)

                # get file size in bytes and convert to MB/GB
                try:
                    size_bytes = os.path.getsize(dest_path)
                except Exception:
                    size_bytes = 0
                size_megabytes = round(size_bytes / (1024 * 1024), 1)
                file_gb = size_megabytes / 1024

                # determine user's remaining quota
                remaining_gb = None
                if loggedIn and username:
                    try:
                        udb = udbload()
                        # find user record
                        user_rec = None
                        for u in udb:
                            if u.get('username') == username:
                                user_rec = u
                                break
                        user_quota_gb = user_rec.get('quota_gb', 0) if user_rec else 0
                        # compute current usage
                        usage_gb = 0.0
                        for fkey, fval in db.get('files', {}).items():
                            if fval.get('owner') == username:
                                usf_mb = fval.get('size_megabytes', 0)
                                if usf_mb:
                                    usage_gb += usf_mb / 1024
                        usage_gb = round(usage_gb, 1)
                        remaining_gb = max(0.0, user_quota_gb - usage_gb)
                    except Exception:
                        remaining_gb = 0.0
                else:
                    # guests: they don't get owner set; treat remaining as 0 so owner won't be set
                    remaining_gb = 0.0

                # build DB entry; only set owner if user is logged in AND file fits remaining quota
                entry = {"reusable": True if reusable else False, "size_megabytes": size_megabytes}
                if loggedIn and username and file_gb <= remaining_gb:
                    entry["owner"] = username

                db["files"][dest_name] = entry

                if reusable:
                    flash('Download code: ' + fileid, 'info')
                else:
                    flash('1-Time Download code: ' + fileid, 'info')

                dbsave(db)
                return redirect(url_for('upload'))

            except RequestEntityTooLarge:
                return 'File is larger than the size limit.'
            
@app.route('/delete/<code>', methods=['GET', 'POST'])
def delete(code):
    db = dbload()
    for file in db['files']:
        if file.split('_')[-1] == code:
            if db['files'][file].get('owner') != session.get('username'):
                flash('You do not own this file and cannot delete it.', 'error')
                return redirect(url_for('upload'))
            try:
                os.remove('uploads/' + file)
            except FileNotFoundError:
                print('couldnt delete from os bc file not found.')
            try:
                os.remove('uploads/' + file.split('_')[0])
            except FileNotFoundError:
                print('couldnt delete from os bc file not found. (2)')
            db['files'].pop(file)
            dbsave(db)
            flash('File with code ' + code + ' has been deleted.', 'info')
            return redirect(url_for('dashboard'))
            
@app.route('/download')
def download_without_code():
    flash('No code provided!', 'error')
    return redirect(url_for('upload'))
    
@app.route('/download/<code>', methods=['GET', 'POST'])
def download(code):
    db = dbload()
    try:
        found = False
        filename = ''
        files = os.listdir('uploads')
        for file in files:
            if file.split('_')[-1] == code:
                found = True
                filename = file
        
        if not found:
            print(filename)
            # Search db for the entry with this code and remove it
            for file_entry in list(db['files'].keys()):
                if file_entry.split('_')[-1] == code:
                    print(f"Deleting: {file_entry}")
                    print
                    db['files'].pop(file_entry)
                    dbsave(db)
                    print(f"Deleted! DB now has {len(db['files'])} files")
                    break
            flash('Invalid code! Check if you typed the correct code, and for one-time codes, make sure nobody else entered the code before you did.', 'error')
            return redirect(url_for('upload'))
        else:
            os.rename('uploads/' + filename, 'uploads/' + filename.replace(f'_{code}', ''))
            def deleteFile():
                db['files'].pop(filename)
                dbsave(db)
            def backRename():
                time.sleep(1)
                os.rename('uploads/' + filename.replace(f'_{code}', ''), 'uploads/' + filename)
            if db['files'][filename]['reusable']:
                backToNameFunc = threading.Thread(target=backRename)
                backToNameFunc.start()
            if db['files'][filename]['reusable'] == False:
                deleteFunc = threading.Thread(target=deleteFile)
                deleteFunc.start()

            return send_from_directory(app.config['UPLOAD_DIRECTORY'], filename.replace(f'_{code}', ''), as_attachment=True)
                
    except Exception as e:
        print(f"Error in download: {e}")
        print(f"Type: {type(e)}")
        import traceback
        traceback.print_exc()
        flash('Invalid code! Check if you typed the correct code, and for one-time codes, make sure nobody else entered the code before you did.', 'error')
        return redirect(url_for('upload'))

app.run(debug=True, port=3133, host='0.0.0.0')
