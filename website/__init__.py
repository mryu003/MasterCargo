from flask import Flask, render_template, send_from_directory, request, redirect, url_for, jsonify, session, make_response
from werkzeug.utils import safe_join
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

    @app.route('/', methods=['GET', 'POST'])
    def index():

        #Last visited page - added to cookie. Repeated for each new page
        resp = make_response(render_template('home.html', logged_in=False))
        resp.set_cookie('last_visited', 'index')  
        session['last_visited'] = 'index'  
        
        curr_year = datetime.now().year
        file_name = f"KeoghsPort{curr_year}.txt"

        log_file_path = os.path.join(app.config['LOG_FOLDER'], file_name)

        if os.path.exists(log_file_path):
            return redirect(url_for('home'))
        

        return resp

        if request.method == 'POST':
            return home()
        
        return render_template('signin.html')

        return render_template('home.html', logged_in=False)

    @app.route('/home', methods=['GET', 'POST'])
    def home():

        resp = make_response(render_template('home.html', logged_in=True))
        resp.set_cookie('last_visited', 'home')  
        session['last_visited'] = 'home' 

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

        # Get ast visited page from cookie and session and display 
        last_visited_cookie = request.cookies.get('last_visited', 'None')
        last_visited_session = session.get('last_visited', 'None')

        resp.set_cookie('last_visited', 'home')  
        return resp

    @app.route('/load', methods=['GET', 'POST'])
    def load():
        resp = make_response(render_template('load.html', loaded_items=[]))
        resp.set_cookie('last_visited', 'load') 
        session['last_visited'] = 'load' 
        
        if 'loaded_items' not in session:
            session['loaded_items'] = []

        if request.method == 'POST':
            items = request.form.get('items')
            if items:
                try:
                    new_items = json.loads(items)
                    session['loaded_items'] = new_items
                    print("Session data after POST:", session['loaded_items'])
                except json.JSONDecodeError:
                    return "Invalid items data", 400

            return redirect(url_for('balance'))

        print("Session data on GET:", session.get('loaded_items', []))
        return render_template('load.html', loaded_items=session['loaded_items'])

    @app.route('/unload', methods=['GET', 'POST'])
    def unload():
        manifest_folder = app.config['MANIFEST_FOLDER']
        curr_year = time.strftime("%Y")
        file_name = f"KeoghsPort{curr_year}.txt"
        manifest_file_path = os.path.join(manifest_folder, file_name)

        # Ensure the manifest file exists
        if not os.path.exists(manifest_file_path):
            return "Manifest file not found. Please upload it first.", 404

        # Initialize containers list
        containers = []
        try:
            # Read containers from the manifest file
            with open(manifest_file_path, 'r') as file:
                containers = [line.strip() for line in file if line.strip()]
        except Exception as e:
            return f"Error reading manifest file: {e}", 500

        if request.method == 'POST':
            selected_containers = request.form.getlist('container')
            print(selected_containers)
            if selected_containers:
                processed_containers_path = os.path.join(manifest_folder, "unloaded_containers.txt")
                try:
                    with open(processed_containers_path, 'a') as file:
                        for container in selected_containers:
                            file.write(f"{container}\n")
                    return f"Successfully unloaded: {', '.join(selected_containers)}"
                except Exception as e:
                    return f"Error saving unloaded containers: {e}", 500

        # Render the unloading page with a list of containers
        return render_template('unload.html', containers=containers)

    @app.route('/balance')
    def balance():
        resp = make_response(render_template('balance.html'))
        resp.set_cookie('last_visited', 'balance') 
        session['last_visited'] = 'balance'  
        return resp

    @app.route('/download')
    def download_log():
        curr_year = datetime.now().year
        filename = f"KeoghsPort{curr_year}.txt"
        log_file_dir = os.path.join('../', app.config['LOG_FOLDER'])
        return send_from_directory(log_file_dir, filename, as_attachment=True)

    @app.route('/download/<filename>')
    def download_manifest(filename):
        manifests_path = app.config['MANIFEST_FOLDER']
        safe_path = safe_join(manifests_path, filename)
        return send_from_directory(directory=manifests_path, path=safe_path, as_attachment=True)

    @app.route('/upload', methods=['GET', 'POST'])
    def upload():
        next_page = request.args.get('next', 'home')

        if request.method == 'POST' and 'fileUpload' in request.files:
            file = request.files['fileUpload']
            if file:
                filename = file.filename
                original_file_path = os.path.join(app.config['MANIFEST_FOLDER'], filename)
                file.save(original_file_path)

                modified_filename = filename.replace('.txt', 'OUTBOUND.txt')
                modified_file_path = os.path.join(app.config['MANIFEST_FOLDER'], modified_filename)

                with open(original_file_path, 'r') as original_file:
                    content = original_file.read()

                with open(modified_file_path, 'w') as modified_file:
                    modified_file.write(content)

                return redirect(url_for(next_page))

        return render_template('upload.html', next_page=next_page)

    @app.route('/add_note', methods=['POST'])
    def add_note():
        data = request.get_json()
        note = data.get('note', '').strip()

        if not note:
            return jsonify({"error": "Note is empty"}), 400

        curr_year = time.strftime("%Y")
        file_name = f"KeoghsPort{curr_year}.txt"
        file_path = os.path.join(app.config['LOG_FOLDER'], file_name)

        try:
            with open(file_path, 'a') as log_file:
                log_file.write(note + '\n')
            return jsonify({"message": "Note added successfully"}), 200
        except Exception as e:
            return jsonify({"error": f"Failed to add note: {e}"}), 500

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
