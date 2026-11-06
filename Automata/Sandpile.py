from .Base import BaseAutomata
import numpy as np

class SandpileAutomata(BaseAutomata):
    name = "Sandpile Model"

    def __init__(self, rows=50, cols=50):
        self.rows = rows
        self.cols = cols
        self.grid = np.zeros((rows, cols), dtype=int)
        self.stable = False
        self.reset()

    def reset(self, **kwargs):
        if "center_grains" in kwargs:
            self.grid = np.zeros((self.rows, self.cols), dtype=int)
            self.grid[self.rows // 2, self.cols // 2] = kwargs["center_grains"]
        else:
            # Pentru Sandpile, celulele au nevoie de cel putin 4 graunte (>= 4) pentru a se prabusi (topple).
            # [0, 20] cu probabilitatea p=[0.8, 0.2] plaseaza 20 graunte pe 20% din celule conform originalului.
            high_val = kwargs.get("high_val", 20)
            p = kwargs.get("p", [0.8, 0.2])
            self.grid = np.random.choice([0, high_val], size=(self.rows, self.cols), p=p)
        self.stable = False

    def step(self):
        current_grid = self.grid
        next_grid = np.copy(current_grid)
        stable = True
        for row in range(0, current_grid.shape[0]):
            for col in range(0, current_grid.shape[1]):
                if (current_grid[row][col] >= 4):
                    next_grid[row][col] -= 4
                    if row > 0:
                        next_grid[row - 1][col] += 1
                    if row < current_grid.shape[0] - 1:
                        next_grid[row + 1][col] += 1
                    if col > 0:
                        next_grid[row][col - 1] += 1
                    if col < current_grid.shape[1] - 1:
                        next_grid[row][col + 1] += 1
                    stable = False

        self.grid = next_grid
        self.stable = stable
        return next_grid

    def get_grid(self):
        return self.grid

    def save_state(self, filepath):
        np.save(filepath, self.grid)

    def load_state(self, filepath):
        self.grid = np.load(filepath)
        self.rows, self.cols = self.grid.shape
