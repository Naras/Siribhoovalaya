
from typing import List, Tuple

class Bandha:
    def __init__(self, name="Custom Bandha"):
        self.name = name
        self.path_points: List[Tuple[int, int]] = [] # List of (row, col) tuples

    def set_path(self, points: List[Tuple[int, int]]):
        """
        Sets the path directly from a list of coordinates.
        Coordinates are 0-indexed (row, col).
        """
        self.path_points = points

    def add_point(self, row, col):
        self.path_points.append((row, col))

    def traverse(self, chakra) -> str:
        """
        Traverses the given Chakra object following the path and returns the extracted text.
        """
        result_text = ""
        for r, c in self.path_points:
            # Check bounds
            if 0 <= r < 27 and 0 <= c < 27:
                akshara = chakra.get_akshara_at(r, c)
                if akshara:
                    result_text += akshara
            else:
                 # What to do on out of bounds? Ignore or mark?
                 # Ignoring for now.
                 pass
        return result_text
        
    def get_coordinates(self):
        return self.path_points
