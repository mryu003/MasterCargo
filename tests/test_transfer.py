from website.classes import Ship, Container, get_ship_grid

def test_unload_only_1():
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
    assert steps[0].ship_grid[0][1].name == 'UNUSED'

def test_load_only_2():
    file_path = './tests/ship_cases/ShipCase2.txt'
    ship_grid = get_ship_grid(file_path)
    bat_container = Container('Bat', 431)
    load_containers = [bat_container]
    unload_containers = []

    ship = Ship(ship_grid)
    steps = ship.get_transfer_steps(load_containers, unload_containers)

    assert steps[0].name == "Bat"
    assert steps[0].weight == 431
    assert steps[0].ship_grid[3][0].name == "Bat"

def test_load_unload_3():
    file_path = './tests/ship_cases/ShipCase3.txt'
    ship_grid = get_ship_grid(file_path)
    bat_container = Container('Bat', 532)
    rat_container = Container('Rat', 6317)
    load_containers = [bat_container, rat_container]
    unload_containers = [[0, 1]]

    ship = Ship(ship_grid)
    steps = ship.get_transfer_steps(load_containers, unload_containers)

    assert len(steps) == 4
    assert not steps[3].ship_grid[2][0].name == 'UNUSED'
    assert not steps[3].ship_grid[3][0].name == 'UNUSED'
    assert steps[3].ship_grid[0][1].name == 'UNUSED'
    assert steps[3].ship_grid[1][1].name == 'UNUSED'
    assert steps[3].ship_grid[1][2].name == 'Doe'

def test_load_unload_4():
    file_path = './tests/ship_cases/ShipCase4.txt'
    ship_grid = get_ship_grid(file_path)
    nat_container = Container('Nat', 2543)
    load_containers = [nat_container]
    unload_containers = [[6, 4]]

    ship = Ship(ship_grid)
    steps = ship.get_transfer_steps(load_containers, unload_containers)

    assert len(steps) == 3
    assert not steps[2].ship_grid[2][0].name == 'UNUSED'
    assert steps[2].ship_grid[6][4].name == 'UNUSED'
    assert steps[2].ship_grid[7][4].name == 'UNUSED'

def test_load_unload_5():
    file_path = './tests/ship_cases/ShipCase5.txt'
    ship_grid = get_ship_grid(file_path)
    nat_container = Container('Nat', 153)
    rat_container = Container('Rat', 2321)
    load_containers = [nat_container, rat_container]
    unload_containers = [[0, 3], [0, 4]]

    ship = Ship(ship_grid)
    steps = ship.get_transfer_steps(load_containers, unload_containers)

    assert len(steps) == 4
    assert not steps[3].ship_grid[1][0].name == 'UNUSED'
    assert not steps[3].ship_grid[2][0].name == 'UNUSED'
    assert steps[3].ship_grid[0][3].name == 'UNUSED'
    assert steps[3].ship_grid[0][4].name == 'UNUSED'

def test_load_unload_6():
    file_path = './tests/ship_cases/SilverQueen.txt'
    ship_grid = get_ship_grid(file_path)
    nat_container = Container('Nat', 5435)
    load_containers = [nat_container]
    unload_containers = [[0, 1], [0, 3]]

    ship = Ship(ship_grid)
    steps = ship.get_transfer_steps(load_containers, unload_containers)

    assert len(steps) == 4
    assert not steps[3].ship_grid[1][0].name == 'UNUSED'
    assert steps[3].ship_grid[0][1].name == 'UNUSED'
    assert steps[3].ship_grid[1][1].name == 'UNUSED'
    assert steps[3].ship_grid[0][3].name == 'UNUSED'
