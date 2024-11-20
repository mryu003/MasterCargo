from flask import Flask, render_template, send_from_directory, safe_join, request, redirect, url_for
import time
import os
from datetime import datetime

MANIFEST_FOLDER = './manifests'
LOG_FOLDER = './log_files'
ALLOWED_EXTENSIONS = {'txt'}

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
        curr_year = time.strftime("%Y")
        file_name = "KeoghsPort" + curr_year + ".txt"
        log_file_path = os.path.join(app.config['LOG_FOLDER'], file_name)

        if os.path.exists(log_file_path):
            return redirect(url_for('home'))
        
        return render_template('home.html', logged_in = False)

    @app.route('/home', methods = ['GET', 'POST'])
    def home():
        curr_year = time.strftime("%Y")
        file_name = "KeoghsPort" + curr_year + ".txt"
        log_file_path = os.path.join(app.config['LOG_FOLDER'], file_name)
        if request.method == 'POST':
            username = request.form.get('username')
            if username:
                if not os.path.exists(LOG_FOLDER):
                    os.makedirs(LOG_FOLDER)

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                with open(log_file_path, 'a') as file:
                    file.write(f"{timestamp} {username} signed in \n")
                
                return redirect(url_for('home'))

        return render_template('home.html', logged_in=True)

    @app.route('/load')
    def load():
        return render_template('load.html')

    @app.route('/balance')
    def balance():
        return render_template('balance.html')

    @app.route('/download')
    def download_log():
        curr_year = time.strftime("%Y")
        filename = "KeoghsPort" + curr_year + ".txt"
        log_file_dir = os.path.join('../', app.config['LOG_FOLDER'])
        return send_from_directory(log_file_dir, filename, as_attachment = True)

    @app.route('/download/<filename>')
    def download_manifest(filename):
        # Ensure the filename is safe and comes from the 'manifests' directory
        manifests_path = safe_join(app.static_folder, 'manifests')
        return send_from_directory(directory=manifests_path, path=filename, as_attachment=True)

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

    @app.route('/add_note', methods=['POST'])
    def add_note():
        data = request.get_json()
        note = data.get('note', '').strip()

        if not note:
            return jsonify({"error": "Note is empty"}), 400

        curr_year = time.strftime("%Y")
        file_name = f"KeoghsPort{curr_year}.txt"
        log_files_path = os.path.join(app.static_folder, 'log_files')
        os.makedirs(log_files_path, exist_ok=True)  # Ensure the directory exists

        file_path = os.path.join(log_files_path, file_name)

        try:
            with open(file_path, 'a') as log_file:
                log_file.write(note + '\n')
            return jsonify({"message": "Note added successfully"}), 200
        except Exception as e:
            print(f"Error writing note: {e}")
            return jsonify({"error": "Failed to add note"}), 500
            
    return app
