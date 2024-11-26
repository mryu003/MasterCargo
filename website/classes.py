import re

MAX_ROW = 8
MAX_COL = 12
BUFFER_SHIP = 4
SHIP_IN_OUT = [8, 0]
TRUCK = [-1, -1]
UNUSED = 'UNUSED'
NAN = 'NAN'
LOAD = 'LOAD'
UNLOAD = 'UNLOAD'


def get_ship_grid(file_path: str) -> list:
    grid = [[None for _ in range(MAX_COL)] for _ in range(MAX_ROW)]
    pattern = re.compile(r'\[(\d{2}),(\d{2})\], \{(\d{5})\}, (\w+)')
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            match = pattern.match(line)
            row, col, weight, container = match.groups()
            grid[int(row) - 1][int(col) - 1] = Container(container, int(weight))
    return grid

def manhattan_distance(start: list, end: list) -> int:
    return abs(start[0] - end[0]) + abs(start[1] - end[1])

class Container:
    def __init__(self, name, weight):
        self.name = name
        self.weight = weight

class Node:
    def __init__(self, op: str, name: str, weight: int, from_pos: list, to_pos: list, time: int):
        self.op = op
        self.name = name
        self.weight = weight
        self.from_pos = from_pos
        self.to_pos = to_pos
        self.time = time

class Transfer(Node):
    def __init__(self, op: str, name: str, weight: int, from_pos: list, to_pos: list, time: int):
        super().__init__(op, name, weight, from_pos, to_pos, time)


class Ship:
    def __init__(self, ship_grid: list):
        self.ship_grid = ship_grid

    def get_transfer_steps(self, load_containers: list, unload_containers: list) -> list:
        if not self.has_space(load_containers, unload_containers):
            return None
        
        steps = []
        for x, y in unload_containers:
            time = self.__unload_time([x, y])
            steps.append(Transfer(
                                UNLOAD, 
                                self.ship_grid[x][y].name, 
                                self.ship_grid[x][y].weight, 
                                [x, y], 
                                TRUCK, 
                                time))
            self.ship_grid[x][y] = Container(UNUSED, 0)

        for container in load_containers:
            free_loc = self.__get_free_location()
            if free_loc:
                time = self.__load_time(free_loc)
                steps.append(Transfer(
                                    LOAD, 
                                    container.name, 
                                    container.weight, 
                                    TRUCK, 
                                    free_loc, 
                                    time))
                self.ship_grid[free_loc[0]][free_loc[1]] = Container(container.name, container.weight)

        return steps
    
    def __get_free_location(self) -> list:
        for col in range(MAX_COL):
            for row in range(MAX_ROW):
                if self.ship_grid[row][col].name == UNUSED:
                    return [row, col]
                
        return None
    
    def has_space(self, load_containers: list, unload_containers: list) -> bool:
        curr_free_space = self.__get_free_space()
        new_free_space = curr_free_space + len(unload_containers)
        return new_free_space >= len(load_containers)
    
    def __get_free_space(self) -> int:
        free_space = 0
        for row in range(MAX_ROW):
            for col in range(MAX_COL):
                if self.ship_grid[row][col].name == UNUSED:
                    free_space += 1

        return free_space
    
    def __unload_time(self, source: list) -> int:
        return manhattan_distance(source, SHIP_IN_OUT)

    def __load_time(self, dest: list) -> int:
        return manhattan_distance(SHIP_IN_OUT, dest)

    




        

