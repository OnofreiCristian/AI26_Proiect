from abc import ABC, abstractmethod
import numpy as np

class BaseAutomata(ABC):
    @abstractmethod
    def reset(self, **kwargs):
        """Reset or reinitialize the grid."""
        pass

    @abstractmethod
    def step(self):
        """Execute one simulation tick."""
        pass

    @abstractmethod
    def get_grid(self) -> np.ndarray:
        """Return the current 2D numpy matrix for visualization."""
        pass

    @abstractmethod
    def save_state(self, filepath: str):
        pass

    @abstractmethod
    def load_state(self, filepath: str):
        pass