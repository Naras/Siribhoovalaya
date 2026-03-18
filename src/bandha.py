
from typing import List, Tuple
import sys
import os

# Add the src directory to the Python path to import required modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sandhi_simple import Sandhi
from transliterate import transliterate_text

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

    def traverse(self, chakra, script='kannada') -> Tuple[str, str]:
        """
        Traverses the given Chakra object following the path and returns extracted text.
        Returns a tuple: (text_without_sandhi, text_with_sandhi)
        """
        result_text = ""
        for r, c in self.path_points:
            # Check bounds
            if 0 <= r < 27 and 0 <= c < 27:
                akshara = chakra.get_akshara_at(r, c, script)
                if akshara:
                    if script == 'kannada': result_text += akshara[0]
                    else: result_text += akshara[1]
            else:
                 # What to do on out of bounds? Ignore or mark?
                 # Ignoring for now.
                 pass
        
        # Apply Sandhi conversion to get Sandhi version
        try:
            if script == 'kannada':
                # For Kannada: transliterate to Devanagari, apply Sandhi, then transliterate back
                devanagari_text = transliterate_text(result_text, 'devanagari')
                sandhi_devanagari = Sandhi(devanagari_text)
                sandhi_text = transliterate_text(sandhi_devanagari, 'kannada')
            else:
                # For Devanagari: apply Sandhi directly
                sandhi_text = Sandhi(result_text)
        except Exception as e:
            # If Sandhi conversion fails, use the original text
            print(f"Sandhi conversion error: {e}")
            sandhi_text = result_text
            
        return result_text, sandhi_text
        
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
    
    def horizontal_zigzag(self, start_row, start_col, length):
        """
        Creates a horizontal zig-zag path pattern.
        Pattern: moves right, then up/down alternating, then right again.
        
        Args:
            start_row (int): Starting row coordinate (0-26)
            start_col (int): Starting column coordinate (0-26)
            length (int): Number of cells to include in the path
        
        Returns:
            List[Tuple[int, int]]: List of (row, col) coordinates
        """
        points = []
        current_row, current_col = start_row, start_col
        direction_up = True  # Alternates between up and down
        
        for i in range(length):
            if 0 <= current_row < 27 and 0 <= current_col < 27:
                points.append((current_row, current_col))
            else:
                break
            
            # Move to next position
            if i % 2 == 0:  # Even step: move right
                current_col += 1
            else:  # Odd step: move up or down
                if direction_up:
                    current_row -= 1
                else:
                    current_row += 1
                direction_up = not direction_up
        
        self.path_points = points
        return points
    
    def vertical_zigzag(self, start_row, start_col, length):
        """
        Creates a vertical zig-zag path pattern.
        Pattern: moves down, then left/right alternating, then down again.
        
        Args:
            start_row (int): Starting row coordinate (0-26)
            start_col (int): Starting column coordinate (0-26)
            length (int): Number of cells to include in the path
        
        Returns:
            List[Tuple[int, int]]: List of (row, col) coordinates
        """
        points = []
        current_row, current_col = start_row, start_col
        direction_right = True  # Alternates between right and left
        
        for i in range(length):
            if 0 <= current_row < 27 and 0 <= current_col < 27:
                points.append((current_row, current_col))
            else:
                break
            
            # Move to next position
            if i % 2 == 0:  # Even step: move down
                current_row += 1
            else:  # Odd step: move left or right
                if direction_right:
                    current_col += 1
                else:
                    current_col -= 1
                direction_right = not direction_right
        
        self.path_points = points
        return points
    
    def chess_knight_moves(self, start_row, start_col, num_jumps, constraints=None):
        """
        Creates a path using chess knight moves (L-shaped: 2+1 squares).
        
        Args:
            start_row (int): Starting row coordinate (0-26)
            start_col (int): Starting column coordinate (0-26)
            num_jumps (int): Number of knight jumps to make
            constraints (dict): Optional constraints to control movement:
                - 'preferred_directions': List of preferred directions ['up', 'down', 'left', 'right']
                - 'avoid_edges': Boolean to avoid getting too close to edges
                - 'random_seed': Integer for reproducible random paths
        
        Returns:
            List[Tuple[int, int]]: List of (row, col) coordinates
        """
        import random
        
        if constraints is None:
            constraints = {}
        
        # Set random seed if provided
        if 'random_seed' in constraints:
            random.seed(constraints['random_seed'])
        
        points = []
        current_row, current_col = start_row, start_col
        
        # All possible knight moves (row_offset, col_offset)
        knight_moves = [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1)
        ]
        
        # Filter moves based on preferred directions if specified
        if 'preferred_directions' in constraints:
            preferred_dirs = constraints['preferred_directions']
            filtered_moves = []
            
            for dr, dc in knight_moves:
                move_directions = []
                
                # Determine the primary directions of this move
                if dr < 0:
                    move_directions.append('up')
                elif dr > 0:
                    move_directions.append('down')
                
                if dc < 0:
                    move_directions.append('left')
                elif dc > 0:
                    move_directions.append('right')
                
                # Keep move if any of its directions are preferred
                if any(dir in preferred_dirs for dir in move_directions):
                    filtered_moves.append((dr, dc))
            
            # Use filtered moves if any match, otherwise use all moves
            if filtered_moves:
                knight_moves = filtered_moves
        
        # Add starting position
        if 0 <= current_row < 27 and 0 <= current_col < 27:
            points.append((current_row, current_col))
        
        for jump in range(num_jumps):
            valid_moves = []
            
            # Find all valid moves within bounds
            for dr, dc in knight_moves:
                new_row = current_row + dr
                new_col = current_col + dc
                
                # Check bounds
                if 0 <= new_row < 27 and 0 <= new_col < 27:
                    # Check edge avoidance constraint
                    if constraints.get('avoid_edges', False):
                        margin = 2  # Stay at least 2 cells from edge
                        if (margin <= new_row < 27 - margin and 
                            margin <= new_col < 27 - margin):
                            valid_moves.append((new_row, new_col))
                    else:
                        valid_moves.append((new_row, new_col))
            
            if not valid_moves:
                break  # No valid moves available
            
            # Choose next position (randomly for variety)
            next_row, next_col = random.choice(valid_moves)
            points.append((next_row, next_col))
            
            current_row, current_col = next_row, next_col
        
        self.path_points = points
        return points
