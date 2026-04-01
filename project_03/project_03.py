from collections import deque

class AutonomousRover:
    def __init__(self, rover_id):
        self.rover_id = rover_id
        self.state = "IDLE"  # IDLE, MOVING_TO_TASK, MOVING_TO_CHARGER, CHARGING
        self.stuck_counter = 0
        self.last_pos = None

    def __str__(self):
        return f"AutonomousRover(id={self.rover_id}, state={self.state})"

    def pos_to_action(self, current, nxt):
        dx = nxt[0] - current[0]
        dy = nxt[1] - current[1]

        if dy == -1:
            return 'UP'
        if dy == 1:
            return 'DOWN'
        if dx == -1:
            return 'LEFT'
        if dx == 1:
            return 'RIGHT'
        return 'WAIT'

    def find_path(self, grid, start, goal, blocked):
        rows = len(grid)
        cols = len(grid[0])

        avoid = blocked - {goal}

        queue = deque([[start]])
        visited = {start}

        while queue:
            path = queue.popleft()
            x, y = path[-1]

            if (x, y) == goal:
                return path[1:]

            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                nx = x + dx
                ny = y + dy

                if (0 <= nx < cols and 0 <= ny < rows
                    and grid[ny][nx] != 1
                    and (nx, ny) not in visited
                    and (nx, ny) not in avoid):

                    visited.add((nx, ny))
                    queue.append(path + [(nx, ny)])

        return []

    def find_all_chargers(self, grid):
        chargers = []
        for y, row in enumerate(grid):
            for x, value in enumerate(row):
                if value == 2:
                    chargers.append((x, y))
        return chargers

    def find_best_charger(self, grid, pos, blocked):
        chargers = self.find_all_chargers(grid)

        best_charger = None
        best_path = []
        best_length = float("inf")

        for charger in chargers:
            if pos == charger:
                return charger, []

            path = self.find_path(grid, pos, charger, blocked)
            if path and len(path) < best_length:
                best_charger = charger
                best_path = path
                best_length = len(path)

        return best_charger, best_path

    def move_towards(self, grid, pos, goal, blocked):
        rows = len(grid)
        cols = len(grid[0])

        def is_contested(cell):
            count = 0
            for ox, oy in blocked:
                if abs(ox - cell[0]) + abs(oy - cell[1]) == 1:
                    count += 1
            return count > 0

        # Different rover ids prefer different tie-break orders.
        if self.rover_id % 2 == 0:
            directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]
        else:
            directions = [(0, 1), (-1, 0), (0, -1), (1, 0)]

        best_choice = None
        best_score = float("inf")
        best_path = []
        best_contested = False

        for dx, dy in directions:
            nx = pos[0] + dx
            ny = pos[1] + dy
            nxt = (nx, ny)

            if not (0 <= nx < cols and 0 <= ny < rows):
                continue
            if grid[ny][nx] == 1:
                continue
            if nxt in blocked:
                continue

            remaining_blocked = blocked - {nxt}
            path_after_step = self.find_path(grid, nxt, goal, remaining_blocked)

            if nxt == goal:
                score = 0
                candidate_path = []
            elif path_after_step:
                score = len(path_after_step)
                candidate_path = path_after_step
            else:
                continue

            contested = is_contested(nxt)

            # Strongly avoid instant oscillation.
            if self.last_pos is not None and nxt == self.last_pos:
                score += 100

            if score < best_score:
                best_score = score
                best_choice = nxt
                best_path = candidate_path
                best_contested = contested

        if best_choice is not None:
            # If both rovers want the same middle square in a corridor,
            # make one rover yield deterministically instead of both taking
            # symmetric detours forever.
            if best_contested and self.rover_id % 2 == 0:
                self.stuck_counter += 1
                if self.stuck_counter <= 2:
                    return 'WAIT'

            self.stuck_counter = 0
            self.last_pos = pos
            return self.pos_to_action(pos, best_choice)

        self.stuck_counter += 1

        # Deterministic yielding to break deadlocks.
        if self.rover_id % 2 == 0 and self.stuck_counter <= 2:
            return 'WAIT'

        if self.last_pos is not None:
            lx, ly = self.last_pos
            if (0 <= lx < cols and 0 <= ly < rows
                and grid[ly][lx] != 1
                and self.last_pos not in blocked):
                old_pos = self.last_pos
                self.last_pos = pos
                return self.pos_to_action(pos, old_pos)

        return 'WAIT'

    def get_action(self, env_state):
        grid = env_state['grid_map']
        battery = env_state['battery_level']
        pos = env_state['current_pos']
        task = env_state['current_task']
        others = env_state['other_rovers']
        bumped = env_state['bumped']

        blocked = set(others.values()) - {pos}

        if bumped:
            self.stuck_counter += 1

        charger, path_to_charger = self.find_best_charger(grid, pos, blocked)
        steps_to_charger = float("inf")

        if charger is not None:
            if pos == charger:
                steps_to_charger = 0
            elif path_to_charger:
                steps_to_charger = len(path_to_charger)

        steps_to_task = float("inf")
        steps_task_to_charger = float("inf")

        if task is not None:
            path_to_task = self.find_path(grid, pos, task, blocked)
            if pos == task:
                steps_to_task = 0
            elif path_to_task:
                steps_to_task = len(path_to_task)

            if charger is not None:
                path_task_to_charger = self.find_path(grid, task, charger, set())
                if task == charger:
                    steps_task_to_charger = 0
                elif path_task_to_charger:
                    steps_task_to_charger = len(path_task_to_charger)

        MOVE_BUFFER = 12
        TASK_CYCLE_BUFFER = 12

        enough_for_task_cycle = (
            task is None
            or battery >= steps_to_task + steps_task_to_charger + TASK_CYCLE_BUFFER
        )

        need_charge = (
            charger is not None and (
                battery <= steps_to_charger + MOVE_BUFFER
                or not enough_for_task_cycle
                or self.state == "MOVING_TO_CHARGER"
                or self.state == "CHARGING"
            )
        )

        if need_charge:
            if pos == charger:
                if battery < 100:
                    self.state = "CHARGING"
                    return 'WAIT'
                self.state = "IDLE"

            elif path_to_charger:
                self.state = "MOVING_TO_CHARGER"
                return self.move_towards(grid, pos, charger, blocked)

            else:
                self.state = "IDLE"
                return 'WAIT'

        if task is None:
            self.state = "IDLE"
            self.last_pos = None
            return 'WAIT'

        if pos == task:
            self.state = "IDLE"
            self.last_pos = None
            return 'INTERACT'

        self.state = "MOVING_TO_TASK"
        return self.move_towards(grid, pos, task, blocked)
