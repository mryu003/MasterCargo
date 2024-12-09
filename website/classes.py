import re
import copy
import heapq

MAX_ROW = 8
MAX_COL = 12
MAX_ROW_BUFFER = 4
MAX_COL_BUFFER = 24
SHIP_IN_OUT = [8, 0]
TRUCK = [-1, -1]
UNUSED = 'UNUSED'
NAN = 'NAN'
LOAD = 'LOAD'
UNLOAD = 'UNLOAD'
MOVE = 'MOVE'
START = 'START'
BALANCE_DIFF = 0.1
BUFFER = 'BUFFER'
SHIP = 'SHIP'
BUFFER_IN_OUT = [5, 0]
SHIP_BUFFER = 4

# =================================================================================================
# Helper functions
# =================================================================================================

def get_ship_grid(file_path: str) -> list:
    """
    Read the ship grid from the file and return it as a 2D list.
    """
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

def get_balance_diff(ship_grid: list) -> float:
    """
    Calculate the difference in weight between the left and right side of the ship grid.
    """
    left = 0
    right = 0

    for row in range(MAX_ROW):
        for col in range(MAX_COL):
            if col < MAX_COL // 2:
                left += ship_grid[row][col].weight
            else:
                right += ship_grid[row][col].weight

    abs_diff = abs(left - right)
    total_weight = left + right

    return abs_diff / total_weight

# =================================================================================================
# Classes: Container, Node, Transfer, Balance, Sift, Ship
# =================================================================================================

class Container:
    def __init__(self, name, weight):
        self.name = name
        self.weight = weight

class Node:
    """
    Base class for the Transfer, Balance, and Sift classes.
    """
    def __init__(self, op: str, name: str, weight: int, from_pos: list, to_pos: list, time: int, prev_grid: list, ship_grid: list, step: int):
        self.op = op
        self.name = name
        self.weight = weight
        self.from_pos = from_pos
        self.to_pos = to_pos
        self.time = time
        self.prev_grid = prev_grid
        self.ship_grid = ship_grid
        self.step = step

class Transfer(Node):
    """
    Class for the transfer operation.
    Methods: 
    - generate_children: Generate all possible children nodes for the current node.
    - __find_top_container: Find the top container in the column.
    - __move_top_container: Find the destination for the top container using BFS. Return the time and the new location.
    - __get_free_location: Find the first free location in the ship grid.
    - __unload_time: Calculate the time to unload the container.
    - __load_time: Calculate the time to load the container.
    - __hash__: Return the hash value of the node.
    - __eq__: Compare the current node with another node.
    """
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
        super().__init__(op, name, weight, from_pos, to_pos, time, prev_grid, ship_grid, step)
        self.fval = fval
        self.load_containers = load_containers
        self.unload_containers = unload_containers

    def generate_children(self):
        children = []
        for x, y in self.unload_containers:
            if self.ship_grid[x + 1][y].name != UNUSED:
                top_x, top_y = self.__find_top_container([x, y])
                time, new_loc_x, new_loc_y = self.__move_top_container([top_x, top_y])
                new_ship_grid = copy.deepcopy(self.ship_grid)
                new_ship_grid[new_loc_x][new_loc_y] = self.ship_grid[top_x][top_y]
                new_ship_grid[top_x][top_y] = Container(UNUSED, 0)
                fval = self.step + 1 + time + len(self.load_containers) + len(self.unload_containers)

                children.append(Transfer(
                                    op=MOVE, 
                                    name=self.ship_grid[top_x][top_y].name, 
                                    weight=self.ship_grid[top_x][top_y].weight, 
                                    from_pos=[top_x, top_y], 
                                    to_pos=[new_loc_x, new_loc_y], 
                                    time=time,
                                    prev_grid=self.ship_grid,
                                    ship_grid=new_ship_grid,
                                    load_containers=self.load_containers,
                                    unload_containers=self.unload_containers,
                                    fval=fval,
                                    step=self.step + 1
                                    ))
            else:
                time = self.__unload_time([x, y])
                new_ship_grid = copy.deepcopy(self.ship_grid)
                new_ship_grid[x][y] = Container(UNUSED, 0)
                new_unload_containers = copy.deepcopy(self.unload_containers)
                new_unload_containers.remove([x, y])
                fval = self.step + 1 + time + len(self.load_containers) + len(new_unload_containers)
                children.append(Transfer(
                                    op=UNLOAD,
                                    name=self.ship_grid[x][y].name,
                                    weight=self.ship_grid[x][y].weight,
                                    from_pos=[x, y],
                                    to_pos=TRUCK,
                                    time=time,
                                    prev_grid=self.ship_grid,
                                    ship_grid=new_ship_grid,
                                    load_containers=self.load_containers,
                                    unload_containers=new_unload_containers,
                                    fval=fval,
                                    step=self.step + 1
                                    ))

        for container in self.load_containers:
            free_loc = self.__get_free_location()
            if free_loc:
                time = self.__load_time(free_loc)
                new_ship_grid = copy.deepcopy(self.ship_grid)
                new_ship_grid[free_loc[0]][free_loc[1]] = Container(container.name, container.weight)
                new_load_containers = copy.deepcopy(self.load_containers)
                new_load_containers.pop(0)
                fval = self.step + 1 + time + len(new_load_containers) + len(self.unload_containers)
                children.append(Transfer(
                                    op=LOAD,
                                    name=container.name,
                                    weight=container.weight,
                                    from_pos=TRUCK,
                                    to_pos=free_loc,
                                    time=time,
                                    prev_grid=self.ship_grid,
                                    ship_grid=new_ship_grid,
                                    load_containers=new_load_containers,
                                    unload_containers=self.unload_containers,
                                    fval=fval,
                                    step=self.step + 1
                                    ))

        return children
    
    def __find_top_container(self, source: list) -> list:
        top_x = source[0]
        while top_x < MAX_ROW and self.ship_grid[top_x][source[1]].name != UNUSED:
            if top_x == MAX_ROW - 1:
                return [top_x, source[1]]
            top_x += 1
        return [top_x - 1, source[1]]

    
    def __move_top_container(self, source: list) -> list:
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
    
    def __hash__(self):
        return hash(str(self.from_pos[0]) + str(self.from_pos[1]) + self.name + str(self.weight) + str(self.time) + str(self.to_pos[0]) + str(self.to_pos[1]) + str(len(self.load_containers)) + str(len(self.unload_containers)) + str(self.step))
    
    def __eq__(self, other):
        pos = self.from_pos == other.from_pos
        name = self.name == other.name
        weight = self.weight == other.weight
        time = self.time == other.time
        load = len(self.load_containers)
        unload = len(self.unload_containers)
        step = self.step == other.step
        return pos and name and weight and time and load and unload and step
    

class Balance(Node):
    """
    Class for the balance operation.
    Methods:
    - generate_children: Generate all possible children nodes for the current node.
    - __penalty: Calculate the penalty for the current move.
    - __hash__: Return the hash value of the node.
    - __eq__: Compare the current node with another node.
    """
    def __init__(self, op: str, name: str, weight: int, from_pos: list, to_pos: list, time: int, prev_grid: list, ship_grid: list, fval: int, step: int, weight_diff: int):
        super().__init__(op, name, weight, from_pos, to_pos, time, prev_grid, ship_grid, step)
        self.fval = fval
        self.weight_diff = weight_diff

    def generate_children(self, moves: list) -> list:
        children = []
        for source, dest in moves:
            new_ship_grid = copy.deepcopy(self.ship_grid)
            new_ship_grid[dest[0]][dest[1]] = self.ship_grid[source[0]][source[1]]
            new_ship_grid[source[0]][source[1]] = Container(UNUSED, 0)
            new_balance = get_balance_diff(new_ship_grid)
            time = manhattan_distance(source, dest)
            penaty = self.__penalty(new_ship_grid)
            fval = self.step + 1 + time + abs(new_balance - BALANCE_DIFF) + penaty
            children.append(Balance(
                                op=MOVE,
                                name=self.ship_grid[source[0]][source[1]].name,
                                weight=self.ship_grid[source[0]][source[1]].weight,
                                from_pos=source,
                                to_pos=dest,
                                time=time,
                                prev_grid=self.ship_grid,
                                ship_grid=new_ship_grid,
                                fval=fval,
                                step=self.step + 1,
                                weight_diff=new_balance
                                ))
            
        return children
    
    def __penalty(self, grid: list) -> int:
        """
        Calculate the penalty for the current move.

        Use the weight difference between the left and right side of the ship to calculate the penalty.
        Heavy containers contribute positively if their side is underweight, and negatively if their side is overweight.

        For example, if the left side is overweight as in ShipCase3, the penalty for moving Cat (9041) to the right side will be the lowest,
        because it will be no longer on the left side. However, moving Rat (100) to the right side will have a hight penalty,
        because Cat will contribute to the penalty for moving the light container to the right side and keeping 2 heavy ones (Cat and Ewe) on the left. 
        """

        total_weight = sum(container.weight for row in grid for container in row if (container.name != UNUSED and container.name != NAN))
        left_weight = sum(container.weight for row in grid for container in row[:MAX_COL//2] if (container.name != UNUSED and container.name != NAN))
        right_weight = total_weight - left_weight

        penalty = 0

        for row in grid:
            for container in row[:MAX_COL//2]:
                penalty += container.weight * (1 if left_weight > right_weight else -1)
            for container in row[MAX_COL//2:]:
                penalty += container.weight * (1 if right_weight > left_weight else -1)

        return penalty
    
    def __hash__(self):
        return hash(str(self.from_pos[0]) + str(self.from_pos[1]) + self.name + str(self.weight) + str(self.time) + str(self.to_pos[0]) + str(self.to_pos[1]))
    
    def __eq__(self, other):
        pos = self.from_pos == other.from_pos
        name = self.name == other.name
        weight = self.weight == other.weight
        time = self.time == other.time
        return pos and name and weight and time
    
class Sift(Node):
    """
    Class for the sift operation. Only used to store the operation information.
    """
    def __init__(self, op: str, name: str, weight: int, from_pos: list, to_pos: list, time: int, prev_grid: list, ship_grid: list, step: int, buffer_grid: list, buffer_q: list):
        super().__init__(op, name, weight, from_pos, to_pos, time, prev_grid, ship_grid, step)
        self.buffer_grid = buffer_grid
        self.buffer_q = buffer_q
    
class Ship:
    """
    Class for the ship. Contains the ship grid and the open and closed sets for the A* algorithm.
    Methods:
    - get_transfer_steps: Get the steps for the transfer operation.
    - get_balance_steps: Get the steps for the balance operation.
    - get_sift_steps: Get the steps for the sift operation.
    - has_space: Check if there is enough space for the transfer operation.
    - __buffer_moves: Get the steps to move containers from the ship to the buffer.
    - __sift_moves: Get the steps to move containers from the buffer to the ship in SIFT-like manner.
    - __get_sift_dest: Get the destination in the ship grid for the sift operation.
    - __get_buffer_loc: Get the location in the buffer for the container.
    - __get_possible_moves: Get the possible moves for the balance operation.
    - __get_dest: Get the destination for the container to move within the ship grid.
    - __get_path: Get the path from the start node to the goal node.
    - __get_free_space: Get the current number of free locations in the ship grid.
    """
    
    def __init__(self, ship_grid: list):
        self.ship_grid = ship_grid
        self.open_set = []
        self.closed_set = set()

    def get_transfer_steps(self, load_containers: list, unload_containers: list) -> list:
        if not self.has_space(load_containers, unload_containers):
            return None
        
        start = self.ship_grid
        goal = 0
        came_from = {}

        start_node = Transfer(
            op=START,
            name=NAN,
            weight=0,
            from_pos=TRUCK,
            to_pos=TRUCK,
            time=0,
            prev_grid=start,
            ship_grid=start,
            load_containers=load_containers,
            unload_containers=unload_containers,
            fval=0,
            step=0
        )

        self.open_set.append(start_node)

        while self.open_set:
            self.open_set.sort(key=lambda x: x.fval)
            curr_node = self.open_set.pop(0)
            self.closed_set.add(curr_node)

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
    
    def get_balance_steps(self) -> list:
        start = self.ship_grid
        curr_balance = get_balance_diff(self.ship_grid)
        came_from = {}

        start_node = Balance(
            op=START,
            name=NAN,
            weight=0,
            from_pos=TRUCK,
            to_pos=TRUCK,
            time=0,
            prev_grid=start,
            ship_grid=start,
            fval=0,
            step=0,
            weight_diff=curr_balance
        )

        self.open_set.append(start_node)

        while self.open_set:
            self.open_set.sort(key=lambda x: x.fval)

            # TODO: This is a temporary fix to prevent the algorithm from running indefinitely.
            if len(self.open_set) > 2000:
                break
            
            curr_node = self.open_set.pop(0)

            self.closed_set.add(curr_node)

            if curr_node.weight_diff <= BALANCE_DIFF:
                return self.__get_path(came_from, curr_node)
            
            moves = self.__get_possible_moves(curr_node.ship_grid)
            children = curr_node.generate_children(moves)
            for child in children:
                if child in self.closed_set: 
                    continue
                self.open_set.append(child)
                came_from[child] = curr_node

        return None
    
    def get_sift_steps(self) -> list:
        start_grid = self.ship_grid
        steps = []

        steps += self.__buffer_moves(start_grid)
        steps += self.__sift_moves(steps[-1])

        return steps
    
    def __buffer_moves(self, start_grid: list) -> list:
        start = start_grid
        buffer_grid = [[Container(UNUSED, 0) for _ in range(MAX_COL_BUFFER)] for _ in range(MAX_ROW_BUFFER)]
        steps = []

        start_node = Sift(
            op=START,
            name=NAN,
            weight=0,
            from_pos=TRUCK,
            to_pos=TRUCK,
            time=0,
            prev_grid=start,
            ship_grid=start,
            step=0,
            buffer_grid=buffer_grid,
            buffer_q=[]
        )

        steps.append(start_node)

        for row in range(MAX_ROW - 1, -1, -1):
            for col in range(MAX_COL):
                if start[row][col].name != UNUSED and start[row][col].name != NAN:
                    buffer_loc = self.__get_buffer_loc(steps[-1].buffer_grid, start[row][col].weight)
                    if buffer_loc:
                        time = manhattan_distance([row, col], SHIP_IN_OUT) + SHIP_BUFFER + manhattan_distance(BUFFER_IN_OUT, buffer_loc)
                        new_buffer_grid = copy.deepcopy(steps[-1].buffer_grid)
                        new_buffer_grid[buffer_loc[0]][buffer_loc[1]] = Container(start[row][col].name, start[row][col].weight)
                        new_ship_grid = copy.deepcopy(steps[-1].ship_grid)
                        new_ship_grid[row][col] = Container(UNUSED, 0)
                        new_buffer_q = copy.deepcopy(steps[-1].buffer_q)
                        heapq.heappush(new_buffer_q, (-start[row][col].weight ,buffer_loc))
                        steps.append(Sift(
                            op=BUFFER,
                            name=start[row][col].name,
                            weight=start[row][col].weight,
                            from_pos=[row, col],
                            to_pos=buffer_loc,
                            time=time,
                            prev_grid=steps[-1].ship_grid,
                            ship_grid=new_ship_grid,
                            buffer_grid=new_buffer_grid,
                            buffer_q=new_buffer_q,
                            step=steps[-1].step + 1
                        ))

        return steps[1:]
    
    def __sift_moves(self, start_node: Sift) -> list:
        steps = []
        steps.append(start_node)

        curr_buffer = start_node.buffer_q

        while curr_buffer:
            _, buffer_loc = heapq.heappop(curr_buffer)
            new_dest = self.__get_sift_dest(steps[-1].ship_grid)
            time = manhattan_distance(buffer_loc, BUFFER_IN_OUT) + SHIP_BUFFER + manhattan_distance(SHIP_IN_OUT, new_dest)
            new_buffer_grid = copy.deepcopy(steps[-1].buffer_grid)
            new_buffer_grid[buffer_loc[0]][buffer_loc[1]] = Container(UNUSED, 0)
            new_ship_grid = copy.deepcopy(steps[-1].ship_grid)
            new_ship_grid[new_dest[0]][new_dest[1]] = Container(steps[-1].buffer_grid[buffer_loc[0]][buffer_loc[1]].name, steps[-1].buffer_grid[buffer_loc[0]][buffer_loc[1]].weight)
            steps.append(Sift(
                op=SHIP,
                name=steps[-1].buffer_grid[buffer_loc[0]][buffer_loc[1]].name,
                weight=steps[-1].buffer_grid[buffer_loc[0]][buffer_loc[1]].weight,
                from_pos=buffer_loc,
                to_pos=new_dest,
                time=time,
                prev_grid=steps[-1].ship_grid,
                ship_grid=new_ship_grid,
                buffer_grid=new_buffer_grid,
                buffer_q=curr_buffer,
                step=steps[-1].step + 1
            ))

        return steps[1:]
    
    def __get_sift_dest(self, ship_grid: list) -> list:
        center_start = MAX_COL // 2 - 1
        center_end = MAX_COL // 2
        row = 0

        while row < MAX_ROW:
            while center_start >= 0 and center_end < MAX_COL:
                if ship_grid[row][center_start].name == UNUSED:
                    return [row, center_start]
                elif ship_grid[row][center_end].name == UNUSED:
                    return [row, center_end]
                center_start -= 1
                center_end += 1

        return None

    def __get_buffer_loc(self, buffer_grid: list, weight: int) -> list:
        for col in range(MAX_COL_BUFFER):
            for row in range(MAX_ROW_BUFFER):
                if buffer_grid[row][col].name == UNUSED and (row == 0 or (buffer_grid[row - 1][col].name != UNUSED and buffer_grid[row - 1][col].weight <= weight)):
                    return [row, col]


    
    def __get_possible_moves(self, ship_grid: list) -> list:
        moves = []
        for row in range(MAX_ROW):
            for col in range(MAX_COL):
                if ship_grid[row][col].name != UNUSED and ship_grid[row][col].name != NAN and (row == MAX_ROW - 1 or ship_grid[row+1][col].name == UNUSED):
                    dests = self.__get_dest(ship_grid, [row, col])
                    for dest in dests:
                        moves.append(([row, col], dest))

        return moves
    
    def __get_dest(self, ship_grid: list, source: list) -> list:
        dests = []
        for row in range(MAX_ROW):
            for col in range(MAX_COL):
                if ship_grid[row][col].name == UNUSED and (row == 0 or ship_grid[row - 1][col].name != UNUSED) and ship_grid[row - 1][col].name != ship_grid[source[0]][source[1]].name:
                    dests.append([row, col])
        
        return dests

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