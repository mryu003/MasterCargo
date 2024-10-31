# pip install flask
# pip install flask-sqlalchemy 

from website import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True) #Turn this to false when turning it in