from flask import Flask, render_template, send_from_directory, request, redirect, url_for, make_response, session
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
        from website.classes import get_ship_grid, Ship, Container

        resp = make_response(render_template('load.html', loaded_items=session.get('loaded_items', [])))
        resp.set_cookie('last_visited', 'load')
        session['last_visited'] = 'load'

        manifest_path = session.get('manifest_path')
        ship_grid = None
        if manifest_path:
            ship_grid = get_ship_grid(manifest_path)

            session['initial_grid'] = [
                [
                    {
                        'name': cell.name if cell else 'NAN',
                        'weight': cell.weight if cell else 0,
                    }
                    for cell in row
                ]
                for row in ship_grid
            ]

        if request.method == 'POST':
            items = request.form.get('items')
            if items:
                session['loaded_items'] = json.loads(items)

            if ship_grid:
                try:
                    ship = Ship(ship_grid)
                    loaded_items = session.get('loaded_items', [])
                    load_containers = [Container(item['name'], item['weight']) for item in loaded_items]
                    unload_containers = [[0, 1], [0, 2]]  # This is temporary
                    steps = ship.get_transfer_steps(load_containers, unload_containers)
                    session['steps'] = [
                        {
                            'op': step.op,
                            'name': step.name,
                            'weight': step.weight,
                            'from_pos': step.from_pos,
                            'to_pos': step.to_pos,
                            'time': step.time,
                            'ship_grid': [
                                [
                                    {
                                        'name': cell.name if cell else 'NAN',
                                        'weight': cell.weight if cell else 0,
                                    }
                                    for cell in row
                                ]
                                for row in step.ship_grid
                            ],
                        }
                        for step in steps
                    ]

                    return redirect(url_for('transfer'))
                except Exception as e:
                    print(f"Error processing steps: {e}")
                    return "Error calculating transfer steps.", 400

        return resp


    @app.route('/balance', methods=['GET', 'POST'])
    def balance():
        steps = session.get('steps', [])
        if steps:
            for step in steps:
                print(f"Operation: {step.op}, Name: {step.name}, From: {step.from_pos}, To: {step.to_pos}")
        return make_response(render_template('balance.html'))

    @app.route('/download')
    def download_log():
        curr_year = datetime.now().year
        filename = f"KeoghsPort{curr_year}.txt"
        log_file_dir = os.path.join('../', app.config['LOG_FOLDER'])
        return send_from_directory(log_file_dir, filename, as_attachment=True)

    @app.route('/upload', methods=['GET', 'POST'])
    def upload():
        next_page = request.args.get('next', 'home')

        if request.method == 'POST':
            if 'fileUpload' in request.files:
                file = request.files['fileUpload']
                if file:
                    filename = file.filename
                    file_path = os.path.join(app.config['MANIFEST_FOLDER'], filename)
                    file.save(file_path)
                    session['manifest_path'] = file_path

                    with open(file_path, 'r') as manifest_file:
                        content = manifest_file.readlines()

                    container_count = len([line for line in content if line.strip()])

                    curr_year = datetime.now().year
                    log_file_name = f"KeoghsPort{curr_year}.txt"
                    log_file_path = os.path.join(app.config['LOG_FOLDER'], log_file_name)
                    timestamp = get_pst_time()
                    log_entry = f"{timestamp}\tManifest {filename} opened, there are {container_count} containers on board\n"

                    with open(log_file_path, 'a') as log_file:
                        log_file.write(log_entry)

                    if next_page == 'load':
                        return redirect(url_for('load'))
                    elif next_page == 'balance':
                        return redirect(url_for('balance'))

        return render_template('upload.html', next_page=next_page)


    @app.route('/transfer', methods=['GET', 'POST'])
    def transfer():
        steps = session.get('steps', [])
        total_steps = len(steps)
        total_time = sum(step['time'] for step in steps)

        if request.method == 'POST':
            current_step = int(request.form.get('current_step', 0)) + 1
        else:
            current_step = 0

        if current_step >= total_steps:
            return "All steps completed."

        if current_step == 0:
            prev_grid = session.get('initial_grid')
        else:
            prev_grid = steps[current_step - 1]['ship_grid']

        def adjust_position(pos):
            return [p + 1 for p in pos] if pos != [-1, -1] else "Truck"

        step = steps[current_step]
        step['from_pos'] = adjust_position(step['from_pos'])
        step['to_pos'] = adjust_position(step['to_pos'])

        return render_template(
            'transfer.html',
            step=step,
            current_step=current_step,
            total_steps=total_steps,
            total_time=total_time,
            grid=prev_grid[::-1]
        )



    
    return app
