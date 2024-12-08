from website.classes import Ship, Container, get_ship_grid, get_balance_diff

def test_balance_1():
    file_path = './tests/ship_cases/ShipCase1.txt'
    ship_grid = get_ship_grid(file_path)
    ship = Ship(ship_grid)
    steps = ship.get_balance_steps()

    weight_diff = get_balance_diff(steps[-1].ship_grid)
    assert weight_diff <= 0.1

def test_balance_2():
    file_path = './tests/ship_cases/ShipCase2.txt'
    ship_grid = get_ship_grid(file_path)
    ship = Ship(ship_grid)
    steps = ship.get_balance_steps()

    weight_diff = get_balance_diff(steps[-1].ship_grid)
    assert weight_diff <= 0.1

def test_balance_3():
    file_path = './tests/ship_cases/ShipCase3.txt'
    ship_grid = get_ship_grid(file_path)
    ship = Ship(ship_grid)
    steps = ship.get_balance_steps()

    weight_diff = get_balance_diff(steps[-1].ship_grid)
    assert weight_diff <= 0.1

def test_balance_4():
    file_path = './tests/ship_cases/ShipCase4.txt'
    ship_grid = get_ship_grid(file_path)
    ship = Ship(ship_grid)
    steps = ship.get_balance_steps()

    weight_diff = get_balance_diff(steps[-1].ship_grid)
    assert weight_diff <= 0.1

# def test_balance_5():
#     file_path = './tests/ship_cases/ShipCase5.txt'
#     ship_grid = get_ship_grid(file_path)
#     ship = Ship(ship_grid)
#     steps = ship.get_balance_steps()

#     weight_diff = get_balance_diff(steps[-1].ship_grid)
#     assert weight_diff <= 0.1

def test_balance_6():
    file_path = './tests/ship_cases/SilverQueen.txt'
    ship_grid = get_ship_grid(file_path)
    ship = Ship(ship_grid)
    steps = ship.get_balance_steps()

    weight_diff = get_balance_diff(steps[-1].ship_grid)
    assert weight_diff <= 0.1
