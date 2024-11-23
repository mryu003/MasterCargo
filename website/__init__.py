from flask import Flask, render_template, send_from_directory, request, redirect, url_for, jsonify
from werkzeug.utils import safe_join
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
        MANIFEST_FOLDER=MANIFEST_FOLDER,
        LOG_FOLDER=LOG_FOLDER
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    os.makedirs(app.config['MANIFEST_FOLDER'], exist_ok=True)
    os.makedirs(app.config['LOG_FOLDER'], exist_ok=True)

    @app.route('/', methods=['GET', 'POST'])
    def index():
        curr_year = time.strftime("%Y")
        file_name = f"KeoghsPort{curr_year}.txt"
        log_file_path = os.path.join(app.config['LOG_FOLDER'], file_name)

        if os.path.exists(log_file_path):
            return redirect(url_for('home'))

        return render_template('home.html', logged_in=False)

    @app.route('/home', methods=['GET', 'POST'])
    def home():
        curr_year = time.strftime("%Y")
        file_name = f"KeoghsPort{curr_year}.txt"
        log_file_path = os.path.join(app.config['LOG_FOLDER'], file_name)
        if request.method == 'POST':
            username = request.form.get('username')
            if username:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(log_file_path, 'a') as file:
                    file.write(f"{timestamp} {username} signed in\n")

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
        filename = f"KeoghsPort{curr_year}.txt"
        return send_from_directory(app.config['LOG_FOLDER'], filename, as_attachment=True)

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
