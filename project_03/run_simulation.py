from collections import deque

# Author: <Daði Már Alfreðsson>
# Date: <30.03.26>
# Project: <Vöruhúsavélmenni>

class AutonomousRover:
    def __init__(self, rover_id):
        self.rover_id = rover_id
        self.state = "IDLE"
        self.current_path = []

    def get_action(self, env_state):
        grid = env_state['grid_map']
        battery = env_state['battery_level']
        task = env_state['current_task']
        bumped = env_state['bumped']
        other_rovers = env_state['other_rovers']
        pos = env_state['current_pos']

        # Uppfæra ástand
        self.update_state(battery, grid, pos, task)

        # Ef við erum á hleðslustöð og þurfum hleðslu
        if self.state == "CHARGING":
            if battery >= 100:
                self.state = "IDLE"
            else:
                return "WAIT"

        # Ef við erum á verkefni
        if pos == task and task is not None:
            return "INTERACT"

        # Ef ekkert verkefni
        if task is None:
            return "WAIT"

        # Reikna leið ef engin leið er til eða við lentum í árekstri
        if not self.current_path or bumped:
            if self.state == "MOVING_TO_CHARGER":
                charger = self.find_charger(grid)
                self.current_path = self.find_path(grid, pos, charger, other_rovers)
            else:
                self.current_path = self.find_path(grid, pos, task, other_rovers)

        # Fylgja leiðinni
        if self.current_path:
            next_pos = self.current_path.pop(0)
            return self.path_to_action(pos, next_pos)

        return "WAIT"

    def find_path(self, grid, start, goal, other_rovers):
        queue = deque([[start]])
        visited = {start}

        while queue:
            path = queue.popleft()
            current = path[-1]

            if current == goal:
                return path

            for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
                next_pos = (current[0]+dx, current[1]+dy)
                x, y = next_pos

                if (0 <= x < len(grid[0]) and
                    0 <= y < len(grid) and
                    grid[y][x] != 1 and
                    next_pos not in visited and
                    next_pos not in other_rovers.values()):

                    visited.add(next_pos)
                    queue.append(path + [next_pos])

        return []

    def path_to_action(self, pos, next_pos):
        dx = next_pos[0] - pos[0]
        dy = next_pos[1] - pos[1]

        if dx == 1: return "RIGHT"
        if dx == -1: return "LEFT"
        if dy == 1: return "DOWN"
        if dy == -1: return "UP"

        return "WAIT"

    def find_charger(self, grid):
        for y in range(len(grid)):
            for x in range(len(grid[y])):
                if grid[y][x] == 2:
                    return (x, y)
        return None

    def needs_charging(self, battery, grid, pos):
        charger_pos = self.find_charger(grid)
        if charger_pos is None:
            return False
        distance = abs(pos[0]-charger_pos[0]) + abs(pos[1]-charger_pos[1])
        return battery < distance + 10

    def update_state(self, battery, grid, pos, task):
        if self.needs_charging(battery, grid, pos):
            self.state = "MOVING_TO_CHARGER"
        elif grid[pos[1]][pos[0]] == 2 and battery < 100:
            self.state = "CHARGING"
        elif task and pos != task:
            self.state = "MOVING_TO_TASK"
        elif pos == task:
            self.state = "IDLE"

    def __str__(self):
        return f"{self.rover_id}"