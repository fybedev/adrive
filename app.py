from flask import (
    Flask,
    render_template,
    session,
    request,
    url_for,
    send_from_directory,
    flash,
    jsonify
)

# TODO move to lightdb instead of json dbload and dbsave
from tools.utils import redirect
from lightdb import LightDB
from tools.geo_loc import geo_loc_bp
from tools.auth import auth_bp

from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix


import os
import random
import threading
import time

# import logging
# import logging.handlers

l_db = LightDB()

app = Flask('adrive', static_folder='static', template_folder='templates')
app.config['UPLOAD_DIRECTORY'] = 'uploads/'
app.config['MAX_CONTENT_LENGTH'] = 1000000 * 1024 * 1024
app.config['SECRET_KEY'] = str(random.randint(99999, 9999999))
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)
app.register_blueprint(geo_loc_bp)
app.register_blueprint(auth_bp)

# handler = logging.handlers.RotatingFileHandler('logs', maxBytes=1024 * 1024)
# logging.getLogger('werkzeug').setLevel(logging.DEBUG)
# logging.getLogger('werkzeug').addHandler(handler)
# app.logger.setLevel(logging.WARNING)
# app.logger.addHandler(handler)

@app.route('/')
def index():
    return redirect(url_for('upload'))

@app.route('/dashboard')
def dashboard():
    db = l_db['files']
    udb = l_db['users']
    
    if session.get('loggedIn', False) == False:
        flash('You must be signed in to view the dashboard!', 'error')
        return redirect(url_for('upload'))
    
    username = session.get('username')
    userfiles = []
    quota_usage_gb = 0
    
    if not username:
        flash('An error occurred. Please sign in again.', 'error')
        session['loggedIn'] = False
        session.pop('username', None)
        return redirect(url_for('upload'))
    
    for file in db:
        if db[file].get('owner') == username:
            db[file]['file'] = file
            db[file]['code'] = file.split('_')[-1]
            # Use original_filename for display if available
            db[file]['display_name'] = db[file].get('original_filename', file)
            userfiles.append(db[file])
            
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

@app.route('/upload')
def upload():
    db = l_db['files']
    udb = l_db['users']
    loggedIn = session.get('loggedIn', False)
    username = session.get('username', '')
    quota_gb = None
    quota_usage_gb = 0.0
    try:
        if loggedIn and username:
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
            for file in db:
                if db[file].get('owner') == username:
                    userfiles.append(db[file])
            for userfile in userfiles:
                usf_mb = userfile.get('size_megabytes', 0)
                if usf_mb:
                    quota_usage_gb += usf_mb / 1024
            quota_usage_gb = round(quota_usage_gb, 1)
        else:
            quota_gb = 5.0
            quota_usage_gb = 0.0
    except Exception:
        quota_gb = quota_gb or 0
        quota_usage_gb = quota_usage_gb or 0.0

    return render_template('upload.html', loggedIn=loggedIn, username=username, quota_gb=quota_gb, quota_usage=quota_usage_gb)

@app.route('/sendfile', methods=['POST'])
def sendfile():
        db = l_db['files']
        udb = l_db['users']
        file = request.files['file']
        reusable = request.form.get('reusable')
        loggedIn = session.get('loggedIn', False)
        username = session.get('username', '')


        if file:
            try:
                original_filename = file.filename
                extension = os.path.splitext(file.filename)[1].lower()

                fileid = str(random.randint(100000, 99999999))
                # Use secure_filename for the disk storage but keep original filename in DB
                safe_filename = secure_filename(original_filename) or 'file'
                dest_name = safe_filename + f'_{fileid}'
                dest_path = os.path.join(app.config['UPLOAD_DIRECTORY'], dest_name)

                file.save(dest_path)
                print(dest_name)

                try:
                    size_bytes = os.path.getsize(dest_path)
                except Exception:
                    size_bytes = 0
                size_megabytes = round(size_bytes / (1024 * 1024), 1)
                file_gb = size_megabytes / 1024

                remaining_gb = None
                if loggedIn and username:
                    try:
                        udb = l_db['users']
                        user_rec = None
                        for u in udb:
                            if u.get('username') == username:
                                user_rec = u
                                break
                        user_quota_gb = user_rec.get('quota_gb', 0) if user_rec else 0
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
                    remaining_gb = 0.0

                entry = {
                    "reusable": True if reusable else False, 
                    "size_megabytes": size_megabytes,
                    "original_filename": original_filename
                }
                if loggedIn and username and file_gb <= remaining_gb:
                    entry["owner"] = username

                db[dest_name] = entry

                if reusable:
                    flash('Download code: ' + fileid, 'info')
                else:
                    flash('1-Time Download code: ' + fileid, 'info')

                return redirect(url_for('upload'))

            except RequestEntityTooLarge:
                return 'File is larger than the size limit.'
            
@app.route('/delete/<code>', methods=['GET', 'POST'])
def delete(code):
    db = l_db['files']
    udb = l_db['users']
    for file in db:
        if file.split('_')[-1] == code:
            if db[file].get('owner') != session.get('username'):
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
            db.pop(file)
            flash('File with code ' + code + ' has been deleted.', 'info')
            return redirect(url_for('dashboard'))
            
@app.route('/download')
def download_without_code():
    flash('No code provided!', 'error')
    return redirect(url_for('upload'))
    
@app.route('/download/<code>', methods=['GET', 'POST'])
def download(code):
    db = l_db['files']
    udb = l_db['users']
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
            for file_entry in list(db.keys()):
                if file_entry.split('_')[-1] == code:
                    print(f"Deleting: {file_entry}")
                    print
                    db.pop(file_entry)
                    print(f"Deleted! DB now has {len(db)} files")
                    break
            flash('Invalid code! Check if you typed the correct code, and for one-time codes, make sure nobody else entered the code before you did.', 'error')
            return redirect(url_for('upload'))
        else:
            # Get original filename from database if it exists
            original_filename = db[filename].get('original_filename', filename.replace(f'_{code}', ''))
            
            os.rename('uploads/' + filename, 'uploads/' + filename.replace(f'_{code}', ''))
            def deleteFile():
                db.pop(filename)
            def backRename():
                time.sleep(1)
                os.rename('uploads/' + filename.replace(f'_{code}', ''), 'uploads/' + filename)
            if db[filename]['reusable']:
                backToNameFunc = threading.Thread(target=backRename)
                backToNameFunc.start()
            if db[filename]['reusable'] == False:
                deleteFunc = threading.Thread(target=deleteFile)
                deleteFunc.start()

            return send_from_directory(app.config['UPLOAD_DIRECTORY'], filename.replace(f'_{code}', ''), as_attachment=True, download_name=original_filename)
                
    except Exception as e:
        print(f"Error in download: {e}")
        print(f"Type: {type(e)}")
        import traceback
        traceback.print_exc()
        flash('Invalid code! Check if you typed the correct code, and for one-time codes, make sure nobody else entered the code before you did.', 'error')
        return redirect(url_for('upload'))

port = int(os.environ.get("ADRIVE_PORT", 3133))
app.run(debug=True, port=port, host='0.0.0.0')
