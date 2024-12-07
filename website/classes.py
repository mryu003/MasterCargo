import re
import copy

MAX_ROW = 8
MAX_COL = 12
SHIP_IN_OUT = [8, 0]
TRUCK = [-1, -1]
UNUSED = 'UNUSED'
NAN = 'NAN'
LOAD = 'LOAD'
UNLOAD = 'UNLOAD'
MOVE = 'MOVE'
START = 'START'


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
    def __init__(self, 
                 op: str, 
                 name: str, 
                 weight: int, 
                 from_pos: list, 
                 to_pos: list, 
                 time: int,
                 prev_grid: list,
                 ship_grid: list,
                 load_containers: list,
                 unload_containers: list,
                 fval: int,
                 step: int):
        super().__init__(op, name, weight, from_pos, to_pos, time)
        self.prev_grid = prev_grid
        self.ship_grid = ship_grid
        self.load_containers = load_containers
        self.unload_containers = unload_containers
        self.fval = fval
        self.step = step

    def generate_children(self):
        children = []
        for x, y in self.unload_containers:
            if self.ship_grid[x + 1][y].name != UNUSED:
                top_x, top_y = self.find_top_container([x, y])
                time, new_loc_x, new_loc_y = self.move_top_container([top_x, top_y])
                new_ship_grid = copy.deepcopy(self.ship_grid)
                new_ship_grid[new_loc_x][new_loc_y] = self.ship_grid[top_x][top_y]
                new_ship_grid[top_x][top_y] = Container(UNUSED, 0)

                children.append(Transfer(
                                    MOVE, 
                                    self.ship_grid[top_x][top_y].name, 
                                    self.ship_grid[top_x][top_y].weight, 
                                    [top_x, top_y], 
                                    [new_loc_x, new_loc_y], 
                                    time,
                                    self.ship_grid,
                                    new_ship_grid,
                                    self.load_containers,
                                    self.unload_containers,
                                    0,
                                    self.step + 1
                                    ))
            else:
                time = self.__unload_time([x, y])
                new_ship_grid = copy.deepcopy(self.ship_grid)
                new_ship_grid[x][y] = Container(UNUSED, 0)
                new_unload_containers = copy.deepcopy(self.unload_containers)
                new_unload_containers.remove([x, y])
                children.append(Transfer(
                                    UNLOAD, 
                                    self.ship_grid[x][y].name, 
                                    self.ship_grid[x][y].weight, 
                                    [x, y], 
                                    TRUCK, 
                                    time,
                                    self.ship_grid,
                                    new_ship_grid,
                                    self.load_containers,
                                    new_unload_containers,
                                    0,
                                    self.step + 1
                                    ))

        for container in self.load_containers:
            free_loc = self.__get_free_location()
            if free_loc:
                time = self.__load_time(free_loc)
                new_ship_grid = copy.deepcopy(self.ship_grid)
                new_ship_grid[free_loc[0]][free_loc[1]] = Container(container.name, container.weight)
                new_load_containers = copy.deepcopy(self.load_containers)
                new_load_containers.pop(0)
                children.append(Transfer(
                                    LOAD, 
                                    container.name, 
                                    container.weight, 
                                    TRUCK, 
                                    free_loc, 
                                    time,
                                    self.ship_grid,
                                    new_ship_grid,
                                    new_load_containers,
                                    self.unload_containers,
                                    0,
                                    self.step + 1))

        return children
    
    def find_top_container(self, source: list) -> list:
        top_x = source[0]
        while top_x < MAX_ROW and self.ship_grid[top_x][source[1]].name != UNUSED:
            if top_x == MAX_ROW - 1:
                return [top_x, source[1]]
            top_x += 1
        return [top_x - 1, source[1]]

    
    def move_top_container(self, source: list) -> list:
        queue = [source]
        visited = set()

        while queue:
            curr = queue.pop(0)
            visited.add(tuple(curr))
            if self.ship_grid[curr[0]][curr[1]].name == UNUSED and self.ship_grid[curr[0] - 1][curr[1]].name != UNUSED:
                return [manhattan_distance(source, curr), curr[0], curr[1]]
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                new_x, new_y = curr[0] + dx, curr[1] + dy
                if 0 <= new_x < MAX_ROW and 0 <= new_y < MAX_COL and (new_x, new_y) not in visited:
                    queue.append([new_x, new_y])

        return None
    
    def __get_free_location(self) -> list:
        for col in range(MAX_COL):
            for row in range(MAX_ROW):
                if self.ship_grid[row][col].name == UNUSED:
                    return [row, col]
                
        return None
    
    def __unload_time(self, source: list) -> int:
        return manhattan_distance(source, SHIP_IN_OUT)
    
    def __load_time(self, dest: list) -> int:
        return manhattan_distance(SHIP_IN_OUT, dest)
    


class Ship:
    def __init__(self, ship_grid: list):
        self.ship_grid = ship_grid
        self.open_set = []
        self.closed_set = []

    def get_transfer_steps(self, load_containers: list, unload_containers: list) -> list:
        if not self.has_space(load_containers, unload_containers):
            return None
        
        start = self.ship_grid
        goal = 0
        came_from = {}

        start_node = Transfer(
            START, 
            NAN, 
            0, 
            TRUCK, 
            TRUCK, 
            0,
            start,
            start,
            load_containers,
            unload_containers,
            0,
            0
        )

        self.open_set.append(start_node)

        while self.open_set:
            self.open_set.sort(key=lambda x: x.fval)
            curr_node = self.open_set.pop(0)
            curr_node.fval = curr_node.step + curr_node.time
            self.closed_set.append(curr_node)

            curr_goal = len(curr_node.load_containers) + len(curr_node.unload_containers)
            if curr_goal == goal:
                return self.__get_path(came_from, curr_node)
            
            children = curr_node.generate_children()
            for child in children:
                if child in self.closed_set:
                    continue
                self.open_set.append(child)
                came_from[child] = curr_node

        return None

    def __get_path(self, came_from: dict, curr_node: Transfer) -> list:
        path = []
        while curr_node.op != START:
            path.append(curr_node)
            curr_node = came_from[curr_node]
        return path[::-1]

    
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