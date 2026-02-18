
import unittest
import json
import sys
import os
import shutil

# Add parent directory to path to import src and app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as app_module
from app import PATHS_DIR


class TestPathPersistence(unittest.TestCase):
    def setUp(self):
        self.app = app_module.app.test_client()

        # Ensure a clean auth DB and create a real Administrator via the API,
        # so tokens are generated and validated exactly as in production.
        auth_db_path = app_module.AUTH_DB_PATH
        if os.path.exists(auth_db_path):
            os.remove(auth_db_path)
        app_module.init_auth_db()

        admin_payload = {
            "email": "paths-admin@example.com",
            "password": "StrongPass1!",
            "role": "Administrator",
        }
        admin_resp = self.app.post(
            "/api/auth/register",
            data=json.dumps(admin_payload),
            content_type="application/json",
        )
        # If this fails, tests depending on admin auth cannot proceed.
        assert admin_resp.status_code == 201, admin_resp.data
        admin_data = json.loads(admin_resp.data)
        self.auth_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {admin_data['access_token']}",
        }

        # Use a temporary directory for tests to avoid cluttering specific saved_paths
        self.original_paths_dir = PATHS_DIR
        self.test_dir = os.path.join(os.path.dirname(PATHS_DIR), 'test_saved_paths')
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)
            
        # Monkey patch the app's PATHS_DIR for the test context.
        # app.py uses the global PATHS_DIR variable from its module, so we
        # update it directly on the imported app_module.
        app_module.PATHS_DIR = self.test_dir

    def tearDown(self):
        # Clean up
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        
        # Restore original path
        app_module.PATHS_DIR = self.original_paths_dir

    def test_save_and_load_path(self):
        """Test saving a path and then loading it back."""
        
        payload = {
            'name': 'Test Path 1',
            'points': [[0, 0], [1, 1], [2, 2]],
            'formula': 'x',
            'text': 'Test Output'
        }
        
        # 1. Save Path (requires Administrator token)
        response = self.app.post(
            '/api/paths',
            data=json.dumps(payload),
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['name'], 'Test Path 1')
        
        # 2. List Paths
        response = self.app.get('/api/paths')
        self.assertEqual(response.status_code, 200)
        files = json.loads(response.data)
        self.assertIn('Test Path 1', files)
        
        # 3. Load Path
        response = self.app.get('/api/paths/Test Path 1')
        self.assertEqual(response.status_code, 200)
        loaded_data = json.loads(response.data)
        
        self.assertEqual(loaded_data['name'], payload['name'])
        self.assertEqual(loaded_data['points'], payload['points'])
        self.assertEqual(loaded_data['formula'], payload['formula'])
        self.assertEqual(loaded_data['text'], payload['text'])

    def test_save_invalid_name(self):
        """Test saving without a name."""
        payload = {
            'points': []
        }
        response = self.app.post(
            '/api/paths',
            data=json.dumps(payload),
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, 400)

    def test_load_nonexistent_path(self):
        """Test loading a path that doesn't exist."""
        response = self.app.get('/api/paths/NonExistent')
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
