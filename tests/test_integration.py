
import unittest
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))

from src.chakra import Chakra
from src.bandha import Bandha
from src.transliterate import get_kannada_for_number, AKSHARA_MAP

class TestSiribhoovalaya(unittest.TestCase):
    def setUp(self):
        # Assuming run from root
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.excel_path = os.path.join(self.base_dir, 'Adhyaya_One_Chakras.xls')
        
    def test_grid_loads(self):
        # We need to test the actual loading if the file exists
        if os.path.exists(self.excel_path):
            chakra = Chakra(self.excel_path, sheet_name='Chakra1-1-1')
            self.assertIsNotNone(chakra.grid)
            self.assertEqual(chakra.grid.shape, (27, 27))
            
            # Test specific value at (0,0) which was 59 per inspection
            self.assertEqual(int(chakra.get_number_at(0,0)), 59)
            
    def test_transliteration(self):
        # Map 1 -> 'अ' -> Kannada 'ಅ'
        # Unicode for Kannada Letter A is \u0c85
        # Let's verify 'अ' first
        self.assertEqual(AKSHARA_MAP[1], 'अ')
        
        # Test mapping
        kannada_char = get_kannada_for_number(1)
        # Verify it's a valid kannada char (e.g. ord in range) or specific value
        # \u0c85 is independent A.
        self.assertEqual(kannada_char, '\u0c85')

if __name__ == '__main__':
    unittest.main()
