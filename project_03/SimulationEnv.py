# KT
# 21.03.2026
# Simulation Environment
# Ekki þarf að skila þessari skrá inn í Gradescope.

import copy

class SimulationEnv:
    def __init__(self, grid_map, max_ticks=1000):
        """
        grid_map: 2D list (0=free, 1=wall, 2=charger)
        """
        self.grid_map = grid_map
        self.max_ticks = max_ticks
        self.current_tick = 0
        
        self.rovers = {}       # rover_id
        self.rover_states = {} # rover_id -> dict: pos, battery, task, bumped

        self.bumped_last_tick = {}
        
        self.tasks_completed = 0
        self.crashes = 0
        self.dead_batteries = 0

    def add_rover(self, rover_instance, start_pos, initial_battery=100.0, task=None):
        rid = rover_instance.rover_id
        self.rovers[rid] = rover_instance
        self.rover_states[rid] = {
            "pos": start_pos,
            "battery": initial_battery,
            "task": task
        }
        self.bumped_last_tick[rid] = False

    def generate_env_state_for_rover(self, target_rid):
        """Builds the limited 'world view' passed to the student's code."""
        other_rovers = {
            rid: state["pos"] 
            for rid, state in self.rover_states.items() if rid != target_rid
        }
        
        return {
            "grid_map": self.grid_map,
            "current_pos": self.rover_states[target_rid]["pos"],
            "bumped": self.bumped_last_tick[target_rid],
            "battery_level": self.rover_states[target_rid]["battery"],
            "current_task": self.rover_states[target_rid]["task"],
            "other_rovers": other_rovers
        }

    def run_simulation(self):
        """Aðal lykkjan sem keyrir hermunina."""
        while self.current_tick < self.max_ticks:
            print('')
            print('--- Tick Start ---')
            print(f"Tick: {self.current_tick}")

            # Prenta út kort og stöðu vélmenna í hvert skipti til að auðvelda ykkur
            # að fylgjast með og aflúsa kóðann ykkar.
            print('Rover States:')
            for state in self.rover_states.items():
                print(state)
            print('Map:')
            for y in range(len(self.grid_map)):
                row = ""
                for x in range(len(self.grid_map[0])):
                    cell = self.grid_map[y][x]
                    rover_here = False
                    for rid, state in self.rover_states.items():
                        if state["pos"] == (x, y):
                            row += f"R{rid:<2}" # Vélmenni
                            rover_here = True
                            break
                        if state["task"] == (x, y):
                            row += f"T{rid:<2}" # Verkefni
                            rover_here = True
                            break
                    if not rover_here:
                        if cell == 0:
                            row += ".  " # Free space
                        elif cell == 1:
                            row += "#  " # Wall
                        elif cell == 2:
                            row += "C  " # Charger
                print(row)
            print("\n")

            actions_this_tick = {}
            
            # 1. Spyrja hvert vélmenni um aðgerð fyrir þetta tímaskref
            for rid, rover in self.rovers.items():
                if self.rover_states[rid]["battery"] <= 0:
                    continue # Dead rovers don't get a turn
                
                # Afritum env_state fyrir hvert vélmenni í hvert skipti.
                # Þá geta vélmenni ekki breytt umhverfinu.
                env_state = copy.deepcopy(self.generate_env_state_for_rover(rid))
                try:
                    # Ef villa kemur upp í get_action, þá prentum við hana og látum vélmennið bíða.
                    actions_this_tick[rid] = rover.get_action(env_state)
                except Exception as e:
                    print(f'Villa í get_action fyrir Rover {rid}. Vélmennið mun bíða þetta tímaskref. Villan var:')
                    print(e)
                    actions_this_tick[rid] = "WAIT"

                print(f"Rover {rid} action: {actions_this_tick[rid]}")

                # Athuga hvort get_action hafi skilað gildi sem er ekki leyfilegt. Ef svo er, þá prentum við viðvörun og látum vélmennið bíða.
                if actions_this_tick[rid] not in ['UP', 'DOWN', 'LEFT', 'RIGHT', 'WAIT', 'INTERACT']:
                    print(f"Rover {rid} skilaði óleyfilegri aðgerð '{actions_this_tick[rid]}'. Vélmennið mun bíða þetta tímaskref.")
                    actions_this_tick[rid] = "WAIT"
                    
            # 2. Uppfæra stöðu vélmenna, athuga fyrir árekstra, og meðhöndla rafmagnsnotkun og hleðslu
            self._apply_physics(actions_this_tick)
            
            # 3. Athuga hvort öll verkefni eru kláruð
            if self._all_tasks_complete():
                break
                
            self.current_tick += 1

            print('--- Tick End ---')
            
        return self._get_final_score()

    def _apply_physics(self, actions):
        """Uppfæra stöðu vélmenna, athuga fyrir árekstra, og meðhöndla rafmagnsnotkun og hleðslu."""
        new_positions = {}

        # Endurstillum bump sensor fyrir hvert vélmenni í byrjun hvers ticks
        for rid in self.rovers:
            self.bumped_last_tick[rid] = False
        
        for rid, action in actions.items():
            state = self.rover_states[rid]
            x, y = state["pos"]
            
            # Hreyfingar
            # Athuga hnitakerfið - x er dálkur, y er röð í grid_map
            if action == 'UP': y -= 1
            elif action == 'DOWN': y += 1
            elif action == 'LEFT': x -= 1
            elif action == 'RIGHT': x += 1
            
            # Rafmagnsnotkun og hleðsla
            if action in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
                state["battery"] -= 1.0  # Kostar 1% að hreyfa sig
            elif action == 'WAIT':
                if self.grid_map[y][x] == 2: # Á hleðslustöð
                    state["battery"] = min(100.0, state["battery"] + 10.0)
                else:
                    if state["task"] is not None: # Vélmenni sem er ekki með verkefni og bíður notar ekki rafmagn
                        state["battery"] -= 0.1  # Vélmenni sem bíða notar 0.1% rafmagn
            
            state["battery"] = round(state["battery"], 1) # Rúnum í 1 aukastaf fyrir læsileika
                    
            # Klára verkefnið
            if action == 'INTERACT' and state["task"] == (x, y):
                self.tasks_completed += 1
                state["task"] = None # Task done!
            elif action == 'INTERACT' and state["task"] != (x, y):
                print(f"Rover {rid} reyndi að gera INTERACT en er ekki á verkefninu! Engin aðgerð tekin.")
                # Við leyfum þessu að gerast, en það er í raun villa í kóðanum. Vélmennið mun bara bíða í þessu tilfelli.

            # Athuga veggi og hillur
            if action in ['UP', 'DOWN', 'LEFT', 'RIGHT'] and self.grid_map[y][x] == 1:
                self.crashes += 1
                new_positions[rid] = state["pos"] # Förum til baka
                self.bumped_last_tick[rid] = True
                print(f"Rover {rid} reyndi að fara í gegnum vegg eða hillu! Engin aðgerð tekin.")
            else:
                new_positions[rid] = (x, y)

            # Athuga hvort vélmennið fór út fyrir kortið
            if x < 0 or x >= len(self.grid_map[0]) or y < 0 or y >= len(self.grid_map):
                self.crashes += 1
                new_positions[rid] = state["pos"] # Revert position
                self.bumped_last_tick[rid] = True # Trigger bump sensor
                print(f"Rover {rid} reyndi að fara út fyrir kortið! Engin aðgerð tekin.")
                
            if state["battery"] <= 0:
                self.dead_batteries += 1
                print(f"Rover {rid} hefur dauða rafhlöðu og getur ekki gert neitt meira.")

        # Árekstrar milli vélmenna
        pos_counts = {}
        for rid, pos in new_positions.items():
            pos_counts[pos] = pos_counts.get(pos, 0) + 1 # Teljum hversu mörg vélmenni eru að fara í hvern reit
            
        for rid, pos in new_positions.items():
            if pos_counts[pos] > 1:
                self.crashes += 1
                self.bumped_last_tick[rid] = True
                print(f"Rover {rid} reyndi að fara í reit sem annað vélmenni er líka að fara í! Engin aðgerð tekin.")
            else:
                self.rover_states[rid]["pos"] = pos # Uppfæra stöðu ef enginn árekstur var

    def _all_tasks_complete(self):
        return all(state["task"] is None for state in self.rover_states.values())

    def _get_final_score(self):
        return {
            "ticks_used": self.current_tick,
            "tasks_completed": self.tasks_completed,
            "crashes": self.crashes,
            "dead_batteries": self.dead_batteries
        }