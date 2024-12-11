from flask import Flask, render_template, send_from_directory, request, redirect, url_for, make_response, session, send_file
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

        
        # Get last visited page from the session 
        last_visited = session.get('last_visited', request.cookies.get('last_visited'))
        resp = make_response(render_template('signin.html', logged_in=False))
        
        resp.set_cookie('last_visited', 'index')
        session['last_visited'] = 'index'


        curr_year = datetime.now().year
        file_name = f"KeoghsPort{curr_year}.txt"
        log_file_path = os.path.join(app.config['LOG_FOLDER'], file_name)

        if last_visited and last_visited != 'index':
            try:
                print(f"Redirecting to: {last_visited}")  
                return redirect(url_for(last_visited))
            except Exception as e:
                print(f"Error during redirection: {e}")

        # If log file exists - redirect to home page
        if os.path.exists(log_file_path):
            return redirect(url_for('home'))

        print("No valid last visited page found. Redirecting to index.")
        resp = make_response(render_template('home.html', logged_in=False))
        resp.set_cookie('last_visited', 'index')  
        session['last_visited'] = 'index'  
        return resp

        if os.path.exists(log_file_path):
            return redirect(url_for('home'))

        if request.method == 'POST':
            return home()
        return resp

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
                
                return '', 204

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
        #resp = make_response(render_template('balance.html'))
        # resp.set_cooke('last_visited', 'balance')
        #session['last_visited'] = 'balance'
        
        from website.classes import get_ship_grid, Ship, Container, get_balance_diff

        steps = session.get('balance_steps', [])
        total_steps = len(steps)

        if request.method == 'POST':
            current_step = int(request.form.get('current_step', 0)) + 1
        else:
            current_step = 0

        if current_step == 0:
            manifest_path = session.get('manifest_path')
            if not manifest_path:
                return "Manifest not uploaded.", 400

            try:
                ship_grid = get_ship_grid(manifest_path)
                ship = Ship(ship_grid)
                balance_steps = ship.get_balance_steps()

                if balance_steps is None:
                    sift_steps = ship.get_sift_steps()
                    session['balance_steps'] = [
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
                        for step in sift_steps
                    ]
                else:
                    session['balance_steps'] = [
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
                        for step in balance_steps
                    ]

                steps = session['balance_steps']
                total_steps = len(steps)

            except Exception as e:
                print(f"Error generating balance steps: {e}")
                return "Error calculating balance steps.", 400

        if current_step >= total_steps:
            manifest_path = session.get('manifest_path')
            base_name = os.path.basename(manifest_path).rsplit('.', 1)[0]
            outbound_file_name = f"{base_name}OUTBOUND.txt"
            manifest_folder = os.path.dirname(manifest_path)
            outbound_file_path = os.path.join(manifest_folder, outbound_file_name)

            final_grid = steps[-1]['ship_grid']
            with open(outbound_file_path, 'w') as outbound_file:
                for row_idx, row in enumerate(final_grid):
                    for col_idx, cell in enumerate(row):
                        outbound_file.write(
                            f"[{row_idx + 1:02},{col_idx + 1:02}], "
                            f"{{{cell['weight']:05}}}, {cell['name']}\n"
                        )

            return render_template(
                'balance.html',
                completed=True,
                outbound_file_name=outbound_file_name,
                outbound_file_path=url_for('download_balanced', filename=outbound_file_name)
            )

        if current_step == 0:
            display_grid = get_ship_grid(session.get('manifest_path'))[::-1]
        else:
            display_grid = steps[current_step - 1]['ship_grid'][::-1]

        step = steps[current_step]

        def adjust_position(pos):
            return [p + 1 for p in pos] if pos != [-1, -1] else "BUFFER"

        step['from_pos'] = adjust_position(step['from_pos'])
        step['to_pos'] = adjust_position(step['to_pos'])

        curr_year = datetime.now().year
        log_file_name = f"KeoghsPort{curr_year}.txt"
        log_file_path = os.path.join(app.config['LOG_FOLDER'], log_file_name)

        from_pos = 'BUFFER' if step['op'] == 'SHIP' else step['from_pos']
        to_pos = 'BUFFER' if step['op'] == 'BUFFER' else step['to_pos']

        log_entry = f"{get_pst_time()}\t{step['name']} moved from {from_pos} to {to_pos}\n"

        with open(log_file_path, 'a') as log_file:
            log_file.write(log_entry)

        manifest_path = session.get('manifest_path')
        base_name = os.path.basename(manifest_path).rsplit('.', 1)[0]
        updated_manifest_path = os.path.join(os.path.dirname(manifest_path), f"{base_name}OUTBOUND.txt")
        with open(updated_manifest_path, 'w') as manifest_file:
            for row_idx, row in enumerate(step['ship_grid']):
                for col_idx, cell in enumerate(row):
                    manifest_file.write(
                        f"[{row_idx + 1:02},{col_idx + 1:02}], "
                        f"{{{cell['weight']:05}}}, {cell['name']}\n"
                    )

        resp = make_response(render_template(
            'balance.html',
            step=step,
            current_step=current_step,
            total_steps=total_steps,
            display_grid=display_grid,
            enumerate=enumerate,
            grid_length=len(display_grid)
        ))
        session['last_visited'] = 'balance'
        resp.set_cookie('last_visited', 'balance')  
        return resp
        


    @app.route('/download_balanced/<filename>')
    def download_balanced(filename):
        manifest_path = session.get('manifest_path')
        if not manifest_path:
            return "Manifest path not found.", 400

        manifest_folder = os.path.abspath(os.path.dirname(manifest_path))
        file_path = os.path.join(manifest_folder, filename)

        if os.path.exists(file_path):
            curr_year = datetime.now().year
            log_file_name = f"KeoghsPort{curr_year}.txt"
            log_file_path = os.path.join(app.config['LOG_FOLDER'], log_file_name)
            timestamp = get_pst_time()
            log_entry = f"{timestamp}\tManifest {filename} downloaded\n"
            
            if not os.path.exists(app.config['LOG_FOLDER']):
                os.makedirs(app.config['LOG_FOLDER'])

            with open(log_file_path, 'a') as log_file:
                log_file.write(log_entry)

            return send_file(file_path, as_attachment=True)
        else:
            return f"File {filename} not found at {file_path}.", 404

    @app.route('/download')
    def download_log():
        curr_year = datetime.now().year
        filename = f"KeoghsPort{curr_year}.txt"
        log_file_dir = os.path.join('../', app.config['LOG_FOLDER'])
        return send_from_directory(log_file_dir, filename, as_attachment=True)


    @app.route('/upload', methods=['GET', 'POST'])
    def upload():
        next_page = request.args.get('next', 'home')
        session['last_visited_page'] = next_page

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

                    container_count = len([
                        line for line in content
                        if line.strip() and not ("UNUSED" in line or "NAN" in line)
                    ])

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

        manifest_path = session.get('manifest_path')
        if not manifest_path:
            return "Manifest path not found.", 400

        base_name = os.path.basename(manifest_path).rsplit('.', 1)[0]
        outbound_file_name = f"{base_name}OUTBOUND.txt"
        manifest_folder = os.path.dirname(manifest_path)
        outbound_file_path = os.path.join(manifest_folder, outbound_file_name)

        if current_step >= total_steps:
            final_grid = steps[-1]['ship_grid']
            with open(outbound_file_path, 'w') as outbound_file:
                for row_idx, row in enumerate(final_grid):
                    for col_idx, cell in enumerate(row):
                        outbound_file.write(
                            f"[{row_idx + 1:02},{col_idx + 1:02}], "
                            f"{{{cell['weight']:05}}}, {cell['name']}\n"
                        )

            return render_template(
                'transfer.html',
                completed=True,
                outbound_file_name=outbound_file_name,
                outbound_file_path=url_for('download_outbound', filename=outbound_file_name)
            )

        if current_step == 0:
            prev_grid = session.get('initial_grid')
        else:
            prev_grid = steps[current_step - 1]['ship_grid']

        with open(outbound_file_path, 'w') as outbound_file:
            for row_idx, row in enumerate(prev_grid):
                for col_idx, cell in enumerate(row):
                    outbound_file.write(
                        f"[{row_idx + 1:02},{col_idx + 1:02}], "
                        f"{{{cell['weight']:05}}}, {cell['name']}\n"
                    )

        def adjust_position(pos):
            return [p + 1 for p in pos] if pos != [-1, -1] else "Truck"

        step = steps[current_step]
        step['from_pos'] = adjust_position(step['from_pos'])
        step['to_pos'] = adjust_position(step['to_pos'])

        curr_year = datetime.now().year
        file_name = f"KeoghsPort{curr_year}.txt"
        log_file_path = os.path.join(app.config['LOG_FOLDER'], file_name)
        operation_mapping = {"UNLOAD": "offloaded", "MOVE": "moved", "LOAD": "loaded"}
        operation = operation_mapping.get(step['op'].upper(), step['op'].lower())
        name = step['name']
        timestamp = get_pst_time()

        if step['op'].upper() == "MOVE":
            log_entry = f"{timestamp}\t{name} {operation} from {step['from_pos']} to {step['to_pos']}\n"
        else:
            log_entry = f"{timestamp}\t{name} {operation} from {step['from_pos']}\n"

        with open(log_file_path, 'a') as log_file:
            log_file.write(log_entry)

        return render_template(
            'transfer.html',
            step=step,
            current_step=current_step,
            total_steps=total_steps,
            total_time=total_time,
            grid=prev_grid[::-1],
            completed=False,
            enumerate=enumerate
        )
    
    @app.route('/download/<filename>')
    def download_outbound(filename):
        manifest_path = session.get('manifest_path')
        if not manifest_path:
            return "Manifest path not found.", 400

        manifest_folder = os.path.abspath(os.path.dirname(manifest_path))
        file_path = os.path.join(manifest_folder, filename)

        if os.path.exists(file_path):
            curr_year = datetime.now().year
            log_file_name = f"KeoghsPort{curr_year}.txt"
            log_file_path = os.path.join(app.config['LOG_FOLDER'], log_file_name)
            timestamp = get_pst_time()
            log_entry = f"{timestamp}\tManifest {filename} downloaded\n"
            
            if not os.path.exists(app.config['LOG_FOLDER']):
                os.makedirs(app.config['LOG_FOLDER'])

            with open(log_file_path, 'a') as log_file:
                log_file.write(log_entry)

            return send_file(file_path, as_attachment=True)
        else:
            return f"File {filename} not found at {file_path}.", 404

        
        return render_template('upload.html', next_page = next_page)
    
    @app.route('/add_comment', methods=['POST'])
    def add_comment():
        curr_year = datetime.now().year
        file_name = f"KeoghsPort{curr_year}.txt"
        log_file_path = os.path.join(app.config['LOG_FOLDER'], file_name)

        comment = request.form.get('comment')
        if comment:
            timestamp = get_pst_time()

            if not os.path.exists(app.config['LOG_FOLDER']):
                os.makedirs(app.config['LOG_FOLDER'])

            with open(log_file_path, 'a') as file:
                file.write(f"{timestamp}\tComment: {comment}\n")
        
        return '', 204


    @app.route('/logout', methods=['POST'])
    def logout():
        curr_year = datetime.now().year
        file_name = f"KeoghsPort{curr_year}.txt"
        log_file_path = os.path.join(app.config['LOG_FOLDER'], file_name)

        if not os.path.exists(app.config['LOG_FOLDER']):
            os.makedirs(app.config['LOG_FOLDER'])

        timestamp = get_pst_time()

        with open(log_file_path, 'a') as file:
            file.write(f"{timestamp}\tLog File Closed\n")

        # Make the log file read-only
        #os.chmod(log_file_path, stat.S_IREAD)

        # session['year_closed'] = True

        return redirect(url_for('index'))
        return resp

    return app