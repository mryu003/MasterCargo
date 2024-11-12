from flask import Flask, render_template, send_from_directory
import time
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/home')
def home():
    return render_template('home.html')

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
    return send_from_directory(log_files, file_name, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)  #Change this to false when we turn in