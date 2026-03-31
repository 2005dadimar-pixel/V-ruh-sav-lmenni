# Author: <Daði Már Alfreðsson>
# Date: <30.03.26>
# Project: <Vöruhúsavélmenni>
# Acknowledgements: <ef þú þáðir eða veittir aðstoð þá á það>
#                   <að vera tekið fram hér>

class AutonomousRover:
    def __init__(self, rover_id):
        """
        Upphafsstillið vélmennið.
        Bætið við breytum sem þarfa til að halda utan um ástand og hegðun vélmannsins.
        """
        self.rover_id = rover_id
        
        # Halda þarf utan um hvað vélmennið er að gera.
        # Hugmyndir: "IDLE", "MOVING_TO_TASK", "MOVING_TO_CHARGER", "CHARGING"
        self.state = "IDLE"
        self.moving_to_task = "Moving to task"
        self.moving_to_charger = "Moving to charger"
        self.charging = ""
        
        # Það getur verið gagnlegt að halda utan um leiðina sem vélmennið er að fylgja.
        # Ekki er nauðsynlegt að gera það. En athugið að ef leiðin er reiknuð í hvert skipti sem kallið er í get_action,
        # þá má útreikningurinn ekki taka of langan tíma. Öll prófin í Gradescope þurfa að klárast á innan við 10 mín í Gradescope
        # annars munu þau falla á tímamörkum og þið fáið "timeout" villu í Gradescope.
        self.current_path = []

    def get_action(self, env_state):
        """
        Kallað er á þetta fall í hverju tímaskrefi til að spyrja vélmennið hvað það vill gera.
        
        Stikar:
        env_state (dict): Gefur upplýsingar um umhverfið og ástand vélmannsins.
            - 'grid_map': 2D list sem lýsir kortinu (0=free, 1=shelf, 2=charger)
            - 'battery_level': float (0.0 to 100.0)
            - 'current_task': Túpla (x, y) eða None.
            - 'current_pos': Túpla (x, y) - Staðsetning vélmannsins.
            - 'bumped': boolean - Satt ef vélmennið lenti í árekstri í síðasta skrefi.
            - 'other_rovers': Uppflettitafla þar sem lyklar eru rover_ids og gögnin (x, y) staðsetningar.
            
        Skilagildi:
        Fallið á að skila einum af eftirfarandi sem streng:
        - 'UP', 'DOWN', 'LEFT', 'RIGHT' til að hreyfa sig í þá átt.
        - 'WAIT' til að bíða (t.d. til að hlaða sig eða forðast árekstra).
        - 'INTERACT' til að klára verkefni þegar vélmennið er á sama reit og verkefnið.
        """
        
        # Breytur úr env_state
        grid = env_state['grid_map']
        battery = env_state['battery_level']
        task = env_state['current_task']
        bumped = env_state['bumped']
        other_rovers = env_state['other_rovers']
        pos = env_state['current_pos']

        # TODO: Útfærið ákvörðunartöku fyrir vélmennið.
        
        # Ef vélmennið er ekki með verkefni, þá bíðum við bara. 
        if task is None: # (Má eyða þessu ef þetta er útfæra annars staðar í kóðanum)
            return "WAIT"
            
        # Ef við eru kominn á sama reit og verkefnið, þá klárum við það.
        if pos == task: # (Má eyða þessu ef þetta er útfæra annars staðar í kóðanum)
            return "INTERACT"
        
        # ... útfærið leiðsögn og aðra hegðun hér ...

        # Sjálfgefið skilagildi
        return "WAIT"
    
    # ----------------------------------------------------------------------
    # Bætið við __str__ fallinu. Það þarf að skila streng sem inniheldur rover_id.
    # ----------------------------------------------------------------------
    def __str__(self):
        return f"{self.rover_id}"

    # ----------------------------------------------------------------------
    # Önnur föll
    # Þið þurfið að skilgreina að minnsta kosti tvö önnur föll.
    # ----------------------------------------------------------------------
    def needs_charging(self, battery, grid, pos):
    # Finnur staðsetningu hleðslustöðvar
        for y in range(len(grid)):
            for x in range(len(grid[y])):
                if grid[y][x] == 2:
                 charger_pos = (x, y)
    
    # Reiknar fjarlægð að hleðslustöð
        distance = abs(pos[0]-charger_pos[0]) + abs(pos[1]-charger_pos[1])
    
    # Fer í hleðslu ef rafhlaðan er of lítil
        return battery < distance + 10
from collections import deque

  

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
    
    return []  # Engin leið fannst