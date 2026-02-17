
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
    def generate_from_function(self, formula_str: str):
        """
        Generates path points based on y = f(x).
        x iterates from 0 to 26 (representing columns).
        y is calculated, rounded, and checked for bounds (representing rows).
        """
        import math
        
        # Prepare safe context
        allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
        
        # Sanitize and prepare formula
        # Replace ^ with ** for power
        expression = formula_str.replace('^', '**')
        
        points = []
        for x in range(27):
            try:
                # Add x to context
                context = allowed_names.copy()
                context['x'] = x
                
                # Evaluate
                y_val = eval(expression, {"__builtins__": None}, context)
                
                # Round to nearest integer
                y = round(y_val)
                
                # Check bounds (0-26)
                if 0 <= y < 27:
                    # In our grid implementation:
                    # traverse uses (r, c).
                    # We mapped x -> col, y -> row.
                    # So point is (y, x)
                    points.append((int(y), int(x)))
            except Exception:
                # Ignore errors for specific x (e.g. log(0), div by zero)
                continue
                
        self.path_points = points
        return points
