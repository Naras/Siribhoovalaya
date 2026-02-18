
import unittest
import json
import sys
import os

# Add parent directory to path to import src and app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.bandha import Bandha
from app import app, chakra

class TestFunctionalBandha(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.bandha = Bandha()

    def test_linear_function(self):
        """Test simple y = x equation"""
        points = self.bandha.generate_from_function("x")
        # Should generate (0,0), (1,1) ... (26,26)
        self.assertEqual(len(points), 27)
        self.assertEqual(points[0], (0, 0)) # row=y=0, col=x=0
        self.assertEqual(points[1], (1, 1))
        self.assertEqual(points[26], (26, 26))

    def test_quadratic_function(self):
        """Test y = x^2 (power operator replacement)"""
        # x^2: 
        # x=0 -> y=0 (0,0)
        # x=1 -> y=1 (1,1)
        # x=2 -> y=4 (4,2)
        # x=3 -> y=9 (9,3)
        # x=4 -> y=16 (16,4)
        # x=5 -> y=25 (25,5)
        # x=6 -> y=36 (out of bounds)
        points = self.bandha.generate_from_function("x^2")
        
        expected_points = [(0,0), (1,1), (4,2), (9,3), (16,4), (25,5)]
        self.assertEqual(points, expected_points)

    def test_trig_function(self):
        """Test usage of math functions (sin)"""
        # y = sin(x) * 10 + 13
        # x=0 -> sin(0)=0 -> y=13
        points = self.bandha.generate_from_function("sin(x)*10 + 13")
        
        # Check first point
        self.assertEqual(points[0], (13, 0))
        
        # Ensure points are within grid
        for r, c in points:
            self.assertTrue(0 <= r < 27)
            self.assertTrue(0 <= c < 27)

    def test_api_endpoint(self):
        """Test the /api/traverse endpoint with formula"""
        response = self.app.post('/api/traverse', 
                               data=json.dumps({'formula': 'x', 'script':'kannada'}),
                               content_type='application/json')
        
        data = json.loads(response.data)
        
        # Check that points are returned
        self.assertIn('points', data)
        self.assertEqual(len(data['points']), 27)
        self.assertEqual(data['points'][0], [0, 0]) # JSON serializes tuples as lists
        
        # Check text is returned (string)
        self.assertIn('text', data)
        self.assertIsInstance(data['text'], str)

if __name__ == '__main__':
    unittest.main()
