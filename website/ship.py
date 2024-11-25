import os
import re

MAX_ROW = 8
MAX_COL = 12
BUFFER_SHIP = 4
SHIP_IN_OUT = [8, 0]
TRUCK = [0, 0]
UNUSED = 'UNUSED'
NAN = 'NAN'
LOAD = 'LOAD'
UNLOAD = 'UNLOAD'

class Container:
    def __init__(self, name, weight):
        self.name = name
        self.weight = weight

class Ship:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.ship_grid = self.__get_ship_grid()
    
    def __get_ship_grid(self) -> list:
        lines = self.__read_manifest_file()
        grid = [[None for _ in range(MAX_COL)] for _ in range(MAX_ROW)]
        self.__populate_grid(grid, lines)

        return grid

    def __read_manifest_file(self) -> list:
        with open(self.file_path, 'r') as file:
            return file.readlines()
    
    def __populate_grid(self, grid: list, lines: list) -> None:
        pattern = re.compile(r'\[(\d{2}),(\d{2})\], \{(\d{5})\}, (\w+)')
        for line in lines:
            match = pattern.match(line)
            row, col, weight, container = match.groups()
            grid[int(row) - 1][int(col) - 1] = Container(container, int(weight))

    def get_transfer_steps(self, load_containers: list, unload_containers: list) -> list:
        if not self.has_space(load_containers, unload_containers):
            return None
        steps = []
        for x, y in unload_containers:
            time = self.__unload_time([x, y])
            steps.append({"op": UNLOAD,
                          "name": self.ship_grid[x][y].name, 
                          "from_name": "SHIP",
                          "from_pos": [x, y],
                          "to_name": "TRUCK",
                          "to_pos": TRUCK,
                          "time": time})
            self.ship_grid[x][y] = Container(UNUSED, 0)

        for container in load_containers:
            free_loc = self.__get_free_location()
            if free_loc:
                time = self.__manhattan_distance(SHIP_IN_OUT, free_loc)
                steps.append({"op": LOAD,
                              "name": container.get("name"),
                              "weight": container.get("weight"),
                              "from_name": "TRUCK",
                              "from_pos": TRUCK,
                              "to_name": "SHIP",
                              "to_pos": free_loc,
                              "time": time})
                self.ship_grid[free_loc[0]][free_loc[1]] = Container(container.get("name"), container.get("weight"))

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
        return self.__manhattan_distance(source, SHIP_IN_OUT)

    def __load_time(self, dest: list) -> int:
        pass

    def __manhattan_distance(self, start: list, end: list) -> int:
        return abs(start[0] - end[0]) + abs(start[1] - end[1])




        

