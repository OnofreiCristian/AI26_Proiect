import random
import numpy as np
from .Base import BaseAutomata

class PredatorPreyAutomata(BaseAutomata):
    name = "Predator-Prey"
    EMPTY = 0
    RABBIT = 1
    FOX = 2

    def __init__(
        self,
        rows=50,
        cols=50,
        rabbit_breed_time=4,
        fox_breed_time=8,
        food_value=3,
        initial_fox_energy=5
    ):
        self.rows = rows
        self.cols = cols
        self.rabbit_breed_time = rabbit_breed_time
        self.fox_breed_time = fox_breed_time
        self.food_value = food_value
        self.initial_fox_energy = initial_fox_energy

        self.grid = np.zeros((rows, cols), dtype=int)
        self.fox_energy = np.zeros((rows, cols), dtype=int)
        self.rabbit_timer = np.zeros((rows, cols), dtype=int)
        self.fox_timer = np.zeros((rows, cols), dtype=int)
        self.stable = False

        self.reset()

    def reset(self, **kwargs):
        # Reseteaza gridul cu o populatie random de iepuri si vulpi
        p_rabbit = kwargs.get("p_rabbit", 0.20)
        p_fox = kwargs.get("p_fox", 0.05)
        p_empty = max(0.0, 1.0 - (p_rabbit + p_fox))

        self.grid = np.random.choice(
            [self.EMPTY, self.RABBIT, self.FOX],
            size=(self.rows, self.cols),
            p=[p_empty, p_rabbit, p_fox]
        ).astype(int)

        self.fox_energy = np.zeros((self.rows, self.cols), dtype=int)
        self.fox_energy[self.grid == self.FOX] = self.initial_fox_energy

        self.rabbit_timer = np.zeros((self.rows, self.cols), dtype=int)
        self.fox_timer = np.zeros((self.rows, self.cols), dtype=int)
        self.stable = False

    def get_neighbors(self, r: int, c: int):
        # Returneaza vecinii ortogonali valizi
        neighbors = []
        if r > 0:
            neighbors.append((r - 1, c))
        if r < self.rows - 1:
            neighbors.append((r + 1, c))
        if c > 0:
            neighbors.append((r, c - 1))
        if c < self.cols - 1:
            neighbors.append((r, c + 1))
        return neighbors

    def step(self):
        new_grid = self.grid.copy()

        # Test if automaton is stable (all cells are EMPTY)
        if (new_grid == self.EMPTY).all():
            self.stable = True
            return None

        new_fox_energy = self.fox_energy.copy()
        new_rabbit_timer = self.rabbit_timer.copy()
        new_fox_timer = self.fox_timer.copy()

        moved = np.zeros((self.rows, self.cols), dtype=bool)

        # Foxes
        fox_positions = list(zip(*np.where(self.grid == self.FOX)))
        random.shuffle(fox_positions)

        for r, c in fox_positions:
            if moved[r, c] or new_grid[r, c] != self.FOX:
                continue

            current_energy = new_fox_energy[r, c]
            current_timer = new_fox_timer[r, c]

            neighbors = self.get_neighbors(r, c)
            rabbit_neighbors = [nb for nb in neighbors if new_grid[nb] == self.RABBIT]

            target = None

            if rabbit_neighbors:
                # Mananca un iepure adiacent
                target = random.choice(rabbit_neighbors)
                current_energy += self.food_value
            else:
                # Se muta aleator pe o celula goala
                empty_neighbors = [nb for nb in neighbors if new_grid[nb] == self.EMPTY]
                if empty_neighbors:
                    target = random.choice(empty_neighbors)

            # Energia scade cu 1 la fiecare loop
            current_energy -= 1

            if current_energy <= 0:
                # Vulpea moare de foame
                new_grid[r, c] = self.EMPTY
                new_fox_energy[r, c] = 0
                new_fox_timer[r, c] = 0
            else:
                current_timer += 1
                if target is not None:
                    tr, tc = target
                    # Verificam reproducerea
                    if current_timer >= self.fox_breed_time:
                        new_grid[r, c] = self.FOX
                        new_fox_energy[r, c] = self.initial_fox_energy
                        new_fox_timer[r, c] = 0
                        current_timer = 0
                    else:
                        new_grid[r, c] = self.EMPTY
                        new_fox_energy[r, c] = 0
                        new_fox_timer[r, c] = 0

                    new_grid[tr, tc] = self.FOX
                    new_fox_energy[tr, tc] = current_energy
                    new_fox_timer[tr, tc] = current_timer
                    moved[tr, tc] = True
                else:
                    # Nu s-a putut muta
                    new_grid[r, c] = self.FOX
                    new_fox_energy[r, c] = current_energy
                    new_fox_timer[r, c] = current_timer
                    moved[r, c] = True

        # Rabbits
        rabbit_positions = list(zip(*np.where(new_grid == self.RABBIT)))
        random.shuffle(rabbit_positions)

        for r, c in rabbit_positions:
            if moved[r, c] or new_grid[r, c] != self.RABBIT:
                continue

            current_timer = new_rabbit_timer[r, c] + 1
            neighbors = self.get_neighbors(r, c)
            empty_neighbors = [nb for nb in neighbors if new_grid[nb] == self.EMPTY]

            if empty_neighbors:
                tr, tc = random.choice(empty_neighbors)
                # Dupa n ture, iepurele se reproduce
                if current_timer >= self.rabbit_breed_time:
                    new_grid[r, c] = self.RABBIT
                    new_rabbit_timer[r, c] = 0
                    current_timer = 0
                else:
                    new_grid[r, c] = self.EMPTY
                    new_rabbit_timer[r, c] = 0

                new_grid[tr, tc] = self.RABBIT
                new_rabbit_timer[tr, tc] = current_timer
                moved[tr, tc] = True
            else:
                # Nu are celula goala adiacenta, ramane pe loc
                new_grid[r, c] = self.RABBIT
                new_rabbit_timer[r, c] = current_timer
                moved[r, c] = True

        self.grid = new_grid
        self.fox_energy = new_fox_energy
        self.rabbit_timer = new_rabbit_timer
        self.fox_timer = new_fox_timer

        return self.grid

    def get_grid(self) -> np.ndarray:
        return self.grid

    def save_state(self, filepath: str):
        np.savez(
            filepath,
            grid=self.grid,
            fox_energy=self.fox_energy,
            rabbit_timer=self.rabbit_timer,
            fox_timer=self.fox_timer
        )

    def load_state(self, filepath: str):
        data = np.load(filepath)
        self.grid = data["grid"]
        self.fox_energy = data["fox_energy"]
        self.rabbit_timer = data["rabbit_timer"]
        self.fox_timer = data["fox_timer"]
        self.rows, self.cols = self.grid.shape
