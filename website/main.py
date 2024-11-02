from flask import Flask, render_template

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

if __name__ == '__main__':
    app.run(debug=True)  #Change this to false when we turn in