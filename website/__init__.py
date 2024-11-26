from flask import Flask, render_template, send_from_directory, request, redirect, url_for, session
import time
import os
import json
from datetime import datetime
from pytz import timezone

MANIFEST_FOLDER = './manifests'
LOG_FOLDER = './log_files'
ALLOWED_EXTENSIONS = {'txt'}

def get_pst_time():
    pst = timezone('US/Pacific')
    now = datetime.now(pst)
    floored_time = now.replace(second = 0, microsecond = 0)
    return floored_time.strftime('%Y-%m-%d %H:%M')


def create_app(test_config=None):
    app = Flask(__name__)

    app.config.from_mapping(
        SECRET_KEY='dev',
    ) 

    app.config['MANIFEST_FOLDER'] = MANIFEST_FOLDER
    app.config['LOG_FOLDER'] = LOG_FOLDER

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(MANIFEST_FOLDER)
        os.makedirs(LOG_FOLDER)
    except OSError:
        pass


    @app.route('/', methods = ['GET', 'POST'])
    def index():
        curr_year = datetime.now().year
        file_name = f"KeoghsPort{curr_year}.txt"
        log_file_path = os.path.join(app.config['LOG_FOLDER'], file_name)

        if os.path.exists(log_file_path):
            return redirect(url_for('home'))
        
        if request.method == 'POST':
            return home()
        
        return render_template('signin.html')

    @app.route('/home', methods = ['GET', 'POST'])
    def home():
        curr_year = datetime.now().year
        file_name = f"KeoghsPort{curr_year}.txt"
        log_file_path = os.path.join(app.config['LOG_FOLDER'], file_name)
        if request.method == 'POST':
            username = request.form.get('username')
            if username:
                if not os.path.exists(LOG_FOLDER):
                    os.makedirs(LOG_FOLDER)

                timestamp = get_pst_time()

                with open(log_file_path, 'a') as file:
                    file.write(f"{timestamp}\t{username} signed in \n")
                
                return redirect(url_for('home'))

        return render_template('home.html', logged_in=True)


    @app.route('/load', methods=['GET', 'POST'])
    def load():
        #if loaded items doesnt exist then intialize as empty 
        if 'loaded_items' not in session:
            session['loaded_items'] = []

        if request.method == 'POST':
        # Get the submitted items from the form 
            items = request.form.get('items')
            if items:
                try:
                # Convert JSON string -> Python list
                    new_items = json.loads(items)
                # update session with the new list of items 
                    session['loaded_items'] = new_items
                    print("Session data after POST:", session['loaded_items'])
                except json.JSONDecodeError:
                    return "Invalid items data", 400

            # Redirect to the balance page after data processes 
            return redirect(url_for('balance'))

        print("Session data on GET:", session.get('loaded_items', []))
        return render_template('load.html', loaded_items=session['loaded_items'])


    @app.route('/balance')
    def balance():
        return render_template('balance.html')

    @app.route('/download')
    def download_log():
        curr_year = datetime.now().year
        filename = f"KeoghsPort{curr_year}.txt"
        log_file_dir = os.path.join('../', app.config['LOG_FOLDER'])
        return send_from_directory(log_file_dir, filename, as_attachment = True)


    @app.route('/upload', methods = ['GET', 'POST'])
    def upload():
        next_page = request.args.get('next', 'home')
        
        if request.method == 'POST':
            if 'fileUpload' in request.files:
                file = request.files['fileUpload']
                if file:
                    filename = file.filename
                    original_file_path = os.path.join(app.config['MANIFEST_FOLDER'], filename)
                    file.save(original_file_path)

                    modified_filename = filename.replace('.txt', 'OUTBOUND.txt')
                    modified_file_path = os.path.join(app.config['MANIFEST_FOLDER'], modified_filename)

                    with open(original_file_path, 'r') as file:
                        content = file.read()

                    modified_content = content
                    
                    with open(modified_file_path, 'w') as file:
                        file.write(modified_content)

                    if next_page == 'load':
                        return redirect(url_for('load'))
                    elif next_page == 'balance':
                        return redirect(url_for('balance'))
        
        return render_template('upload.html', next_page = next_page)
    
    @app.route('/logout', methods=['POST'])
    def logout():
        curr_year = datetime.now().year
        file_name = f"KeoghsPort{curr_year}.txt"
        log_file_path = os.path.join(app.config['LOG_FOLDER'], file_name)

        if not os.path.exists(app.config['LOG_FOLDER']):
            os.makedirs(app.config['LOG_FOLDER'])

        timestamp = get_pst_time()

        with open(log_file_path, 'a') as file:
            file.write(f"{timestamp}    Log File Closed\n")

        # Make the log file read-only
        #os.chmod(log_file_path, stat.S_IREAD)

        return redirect(url_for('index'))

    return app
