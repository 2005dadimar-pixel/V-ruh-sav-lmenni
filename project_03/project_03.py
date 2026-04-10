from collections import deque

# Þetta forrit útfærir sjálfvirkt vélmenni (rover) sem finnur leiðir, forðast árekstra
# og sér um rafhlöðu með því að fara í hleðslustöð þegar þarf.

class AutonomousRover:
    def __init__(self, rover_id):
        self.rover_id = rover_id
        self.state = "IDLE"  # IDLE, MOVING_TO_TASK, MOVING_TO_CHARGER, CHARGING
        self.stuck_counter = 0
        self.last_pos = None

    def __str__(self):
        return f"AutonomousRover(id={self.rover_id}, state={self.state})"

    def pos_to_action(self, current, nxt):
        # Reiknum breytingu í x og y til að ákvarða hreyfingu
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
        # BFS (Breadth-First Search) til að finna stystu leið frá start að goal
        rows = len(grid)
        cols = len(grid[0])

        # Forðumst blokkeraða reiti nema markmið (goal)
        avoid = blocked - {goal}

        # Búum til biðröð af slóðum (hver slóð er listi af hnitum)
        queue = deque([[start]])
        visited = {start}

        # Förum í gegnum alla mögulega stíga þar til við finnum goal
        while queue:
            path = queue.popleft()
            x, y = path[-1]

            if (x, y) == goal:
                return path[1:]

            # Prófum alla nágranna (upp, niður, vinstri, hægri)
            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                nx = x + dx
                ny = y + dy

                # Athugum að reitur sé innan marka, ekki veggur og ekki þegar heimsóttur
                if (0 <= nx < cols and 0 <= ny < rows
                    and grid[ny][nx] != 1
                    and (nx, ny) not in visited
                    and (nx, ny) not in avoid):

                    visited.add((nx, ny))
                    queue.append(path + [(nx, ny)])

        return []

    def find_all_chargers(self, grid):
        # Finnur alla hleðslustöðvar (gildi 2 í grid)
        chargers = []
        for y, row in enumerate(grid):
            for x, value in enumerate(row):
                if value == 2:
                    chargers.append((x, y))
        return chargers

    def find_best_charger(self, grid, pos, blocked):
        # Velur bestu (stystu) hleðslustöðina miðað við núverandi staðsetningu
        chargers = self.find_all_chargers(grid)

        best_charger = None
        best_path = []
        best_length = float("inf")

        # Prófum allar stöðvar og veljum þá með stystu leið
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
        # Velur næsta skref í átt að markmiði með því að meta mögulegar hreyfingar
        rows = len(grid)
        cols = len(grid[0])

        # Athugar hvort reitur sé nálægt öðrum vélmennum (árekstrarhætta)
        def is_contested(cell):
            count = 0
            for ox, oy in blocked:
                if abs(ox - cell[0]) + abs(oy - cell[1]) == 1:
                    count += 1
            return count > 0

        # Mismunandi forgangsröð eftir rover_id til að brjóta samhverfu
        if self.rover_id % 2 == 0:
            directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]
        else:
            directions = [(0, 1), (-1, 0), (0, -1), (1, 0)]

        # Geymum bestu hreyfingu og skor hennar
        best_choice = None
        best_score = float("inf")
        best_path = []
        best_contested = False

        # Prófum allar mögulegar hreyfingar
        for dx, dy in directions:
            nx = pos[0] + dx
            ny = pos[1] + dy
            nxt = (nx, ny)

            # Sleppum ef utan marka, veggur eða annar rover
            if not (0 <= nx < cols and 0 <= ny < rows):
                continue
            if grid[ny][nx] == 1:
                continue
            if nxt in blocked:
                continue

            remaining_blocked = blocked - {nxt}
            # Finna leið eftir að við tökum þetta skref
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

            # Forðumst að fara til baka í síðustu stöðu (sveiflur)
            if self.last_pos is not None and nxt == self.last_pos:
                score += 100

            # Uppfærum bestu hreyfingu ef skor er betra
            if score < best_score:
                best_score = score
                best_choice = nxt
                best_path = candidate_path
                best_contested = contested

        if best_choice is not None:
            # Ef árekstrarhætta, láta sum vélmenni bíða til að forðast deadlock
            if best_contested and self.rover_id % 2 == 0:
                self.stuck_counter += 1
                if self.stuck_counter <= 2:
                    return 'WAIT'

            self.stuck_counter = 0
            self.last_pos = pos
            return self.pos_to_action(pos, best_choice)

        # Ef engin góð hreyfing fannst, teljum okkur fast
        self.stuck_counter += 1

        # Sum vélmenni bíða til að leysa pattstöðu
        if self.rover_id % 2 == 0 and self.stuck_counter <= 2:
            return 'WAIT'

        # Reynum að fara aftur á síðustu stöðu ef hægt
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
        # Aðalfall sem ákveður hvaða aðgerð á að framkvæma í þessu skrefi
        grid = env_state['grid_map']
        battery = env_state['battery_level']
        pos = env_state['current_pos']
        task = env_state['current_task']
        others = env_state['other_rovers']
        bumped = env_state['bumped']

        # Staðsetningar annarra vélmenna sem þarf að forðast
        blocked = set(others.values()) - {pos}

        # Ef við lentum í árekstri, aukum stuck_counter
        if bumped:
            self.stuck_counter += 1

        # Finna bestu hleðslustöð og fjarlægð að henni
        charger, path_to_charger = self.find_best_charger(grid, pos, blocked)
        steps_to_charger = float("inf")

        if charger is not None:
            if pos == charger:
                steps_to_charger = 0
            elif path_to_charger:
                steps_to_charger = len(path_to_charger)

        # Reiknum fjarlægð að verkefni og frá verkefni í hleðslu
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

        # Öryggismörk til að tryggja að rafhlaðan klárist ekki
        MOVE_BUFFER = 12
        TASK_CYCLE_BUFFER = 12

        # Athugum hvort rafhlaðan dugi fyrir verkefni + leið í hleðslu
        enough_for_task_cycle = (
            task is None
            or battery >= steps_to_task + steps_task_to_charger + TASK_CYCLE_BUFFER
        )

        # Ákveðum hvort við eigum að fara í hleðslu
        need_charge = (
            charger is not None and (
                battery <= steps_to_charger + MOVE_BUFFER
                or not enough_for_task_cycle
                or self.state == "MOVING_TO_CHARGER"
                or self.state == "CHARGING"
            )
        )

        # Ef þarf að hlaða, förum í hleðslustöð eða bíðum þar
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

        # Ef ekkert verkefni, bíðum
        if task is None:
            self.state = "IDLE"
            self.last_pos = None
            return 'WAIT'

        # Ef við erum komin á verkefni, klárum það
        if pos == task:
            self.state = "IDLE"
            self.last_pos = None
            return 'INTERACT'

        # Annars hreyfumst í átt að verkefni
        self.state = "MOVING_TO_TASK"
        return self.move_towards(grid, pos, task, blocked)
