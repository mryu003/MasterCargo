from flask import Flask, render_template, send_from_directory, request, redirect, url_for
import time
import os
from datetime import datetime

app = Flask(__name__)

manifest_folder = os.path.join(app.static_folder, 'manifests')
app.config['manifest_folder'] = manifest_folder

if not os.path.exists(manifest_folder):
    os.makedirs(manifest_folder)

@app.route('/', methods = ['GET', 'POST'])
def index():
    curr_year = time.strftime("%Y")
    file_name = "KeoghsPort" + curr_year + ".txt"
    log_files_dir = os.path.join(app.static_folder, 'log_files')
    log_file_path = os.path.join(log_files_dir, file_name)

    if os.path.exists(log_file_path):
        return redirect(url_for('home'))
    
    return render_template('home.html', logged_in = False)

@app.route('/home', methods = ['GET', 'POST'])
def home():
    curr_year = time.strftime("%Y")
    file_name = "KeoghsPort" + curr_year + ".txt"
    log_files_dir = os.path.join(app.static_folder, 'log_files')
    log_file_path = os.path.join(log_files_dir, file_name)
    if request.method == 'POST':
        username = request.form.get('username')
        if username:
            if not os.path.exists(log_files_dir):
                os.makedirs(log_files_dir)

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
    file_name = "KeoghsPort" + curr_year + ".txt"
    log_files = os.path.join(app.static_folder, 'log_files')
    return send_from_directory(log_files, file_name, as_attachment = True)

@app.route('/upload', methods = ['GET', 'POST'])
def upload():
    next_page = request.args.get('next', 'home')
    
    if request.method == 'POST':
        if 'fileUpload' in request.files:
            file = request.files['fileUpload']
            if file:
                filename = file.filename
                original_file_path = os.path.join(app.config['manifest_folder'], filename)
                file.save(original_file_path)

                modified_filename = filename.replace('.txt', 'OUTBOUND.txt')
                modified_file_path = os.path.join(app.config['manifest_folder'], modified_filename)

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

if __name__ == '__main__':
    app.run(debug=True)  #Change this to false when we turn in