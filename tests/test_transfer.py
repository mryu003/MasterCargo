from website.ship import Ship

def test_unload_only():
    # TODO: Add step information: locations, time, etc.

    filename = './tests/ship_cases/ShipCase1.txt'
    load_containers = []
    unload_containers = [[0,1]]
    ship = Ship(filename)
    steps = ship.get_transfer_steps(load_containers, unload_containers)
    assert steps[0].get("name") == "Cat"
    assert ship.ship_grid[0][1].name == 'UNUSED'

def test_load_only():
    file_path = './tests/ship_cases/ShipCase2.txt'
    load_containers = [{'name': 'Bat', 'weight': 431}]
    unload_containers = []
    ship = Ship(file_path)
    steps = ship.get_transfer_steps(load_containers, unload_containers)
    assert steps[0].get("name") == "Bat"
    assert steps[0].get("weight") == 431
    assert ship.ship_grid[3][0].name == "Bat"