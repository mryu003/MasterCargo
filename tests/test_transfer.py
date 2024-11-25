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