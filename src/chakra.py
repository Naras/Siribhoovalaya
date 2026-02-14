
import pandas as pd
import os
from .transliterate import AKSHARA_MAP, transliterate_text

class Chakra:
    def __init__(self, file_path, sheet_name='Sheet1'):
        self.file_path = file_path
        self.sheet_name = sheet_name
        self.grid = None # 27x27 grid of integers
        self.load_data()

    def load_data(self):
        """
        Loads the 27x27 grid from the Excel file.
        Assumes data is in the specified sheet, starting at row 3 (0-indexed) or physical row 4.
        The block is 27 rows x 27 columns.
        """
        try:
            # Load the sheet with no header to get raw position
            # Use openpyxl engine explicitely for xlsx or default for xls
            engine = 'openpyxl' if self.file_path.endswith('.xlsx') else None
            df = pd.read_excel(self.file_path, sheet_name=self.sheet_name, header=None, engine=engine)
            
            # Extract 27x27 grid
            # Based on inspection: data starts around row 3 (which has index 3 in 0-indexed df if row 1 is 0)
            # Inspection showed:
            #    0    1     2     3  ...
            # 2 NaN        1.0   2.0  ...
            # 3 NaN    1  59.0  23.0  ... <--- This looks like the start of data rows, but col 1 is index?
            # Let's re-examine index 3.
            # "3 NaN 1 59.0 ..." -> Col 2 is 59.0.
            # Row 4 is "4 NaN 2 53.0 ..."
            
            # It seems the grid data (the Akshara numbers) starts at row 3, column 2.
            # and goes for 27 rows and 27 columns.
            
            # Slice: rows 3 to 3+27=30 (exclusive), cols 2 to 2+27=29 (exclusive)
            grid_df = df.iloc[3:30, 2:29]
            
            # Fill NaNs with 0 (though there shouldn't be any in a valid chakra)
            grid_df = grid_df.fillna(0)
            
            # Convert to integers
            self.grid = grid_df.astype(int).values
            
            if self.grid.shape != (27, 27):
                raise ValueError(f"Extracted grid has incorrect shape: {self.grid.shape}. Expected (27, 27).")
                
        except Exception as e:
            print(f"Error loading Chakra data: {e}")
            self.grid = None

    def get_akshara_at(self, row, col):
        """
        Returns the Akshara (Kannada character) at the given 0-indexed row, col.
        Row and Col should be 0-26.
        """
        if self.grid is None:
            return None
            
        if not (0 <= row < 27 and 0 <= col < 27):
            return None
            
        number = self.grid[row][col]
        
        # Map number to Akshara
        if 1 <= number <= 64:
             # AKSHARA_MAP is in Devanagari
             devanagari = AKSHARA_MAP[number]
             return transliterate_text(devanagari, 'kannada')
        return "?"

    def get_number_at(self, row, col):
        if self.grid is None: return None
        if 0 <= row < 27 and 0 <= col < 27:
            return self.grid[row][col]
        return None
