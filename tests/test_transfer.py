from website.classes import Ship, Container, get_ship_grid

def test_unload_only():
    # TODO: Add step information: locations, time, etc.

    file_path = './tests/ship_cases/ShipCase1.txt'
    ship_grid = get_ship_grid(file_path)
    load_containers = []
    unload_containers = [[0,1]]
    
    ship = Ship(ship_grid)
    steps = ship.get_transfer_steps(load_containers, unload_containers)
    
    assert steps[0].name == "Cat"
    assert steps[0].weight == 99
    assert steps[0].from_pos == [0, 1]
    assert steps[0].time == 9
    assert ship.ship_grid[0][1].name == 'UNUSED'

def test_load_only():
    file_path = './tests/ship_cases/ShipCase2.txt'
    ship_grid = get_ship_grid(file_path)
    bat_container = Container('Bat', 431)
    load_containers = [bat_container]
    unload_containers = []

    ship = Ship(ship_grid)
    steps = ship.get_transfer_steps(load_containers, unload_containers)

    assert steps[0].name == "Bat"
    assert steps[0].weight == 431
    assert ship.ship_grid[3][0].name == "Bat"