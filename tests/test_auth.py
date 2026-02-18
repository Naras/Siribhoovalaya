import os
import json
import unittest
import sys

# Ensure project root is on sys.path so we can import app
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

import app as app_module  # noqa: E402


class TestAuthEndpoints(unittest.TestCase):
    def setUp(self):
        # Use the real Flask app's test client
        self.app = app_module.app.test_client()

        # Start each test with a clean auth DB
        auth_db_path = app_module.AUTH_DB_PATH
        if os.path.exists(auth_db_path):
            os.remove(auth_db_path)

        # Re-init auth DB for this test
        app_module.init_auth_db()

        self.strong_password = "StrongPass1!"

    def _register(self, email="user@example.com", password=None, role=None):
        if password is None:
            password = self.strong_password

        payload = {"email": email, "password": password}
        if role is not None:
            payload["role"] = role

        response = self.app.post(
            "/api/auth/register",
            data=json.dumps(payload),
            content_type="application/json",
        )
        return response

    def test_register_success_default_role_normal(self):
        response = self._register()
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)

        self.assertIn("id", data)
        self.assertEqual(data["email"], "user@example.com")
        self.assertEqual(data["role"], "Normal")  # default role
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "Bearer")

    def test_register_success_explicit_admin_role(self):
        response = self._register(email="admin@example.com", role="Administrator")
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)

        self.assertEqual(data["role"], "Administrator")
        self.assertIn("access_token", data)

    def test_register_rejects_weak_password(self):
        response = self._register(password="weakpass")
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("error", data)
        self.assertIn("Password must be at least 8 characters long", data["error"])

    def test_register_duplicate_email_fails(self):
        # First registration should succeed
        first = self._register()
        self.assertEqual(first.status_code, 201)

        # Second registration with same email should fail
        second = self._register()
        self.assertEqual(second.status_code, 400)
        data = json.loads(second.data)
        self.assertIn("error", data)

    def test_login_success_after_register(self):
        # Register a user
        reg_response = self._register(email="login@example.com")
        self.assertEqual(reg_response.status_code, 201)

        # Login with the same credentials
        payload = {
            "email": "login@example.com",
            "password": self.strong_password,
        }
        response = self.app.post(
            "/api/auth/login",
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.assertEqual(data["email"], "login@example.com")
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "Bearer")

    def test_login_invalid_password_fails(self):
        # Register user
        reg_response = self._register(email="user2@example.com")
        self.assertEqual(reg_response.status_code, 201)

        # Attempt login with wrong password
        payload = {
            "email": "user2@example.com",
            "password": "WrongPass1!",
        }
        response = self.app.post(
            "/api/auth/login",
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn("error", data)

    def test_admin_can_delete_user(self):
        # Create an administrator
        admin_resp = self._register(email="admin@example.com", role="Administrator")
        self.assertEqual(admin_resp.status_code, 201)
        admin_data = json.loads(admin_resp.data)
        admin_token = admin_data["access_token"]

        # Create a normal user
        user_resp = self._register(email="user_to_delete@example.com")
        self.assertEqual(user_resp.status_code, 201)
        user_data = json.loads(user_resp.data)
        user_id = user_data["id"]

        # Admin deletes the user
        headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json",
        }
        delete_resp = self.app.delete(f"/api/auth/users/{user_id}", headers=headers)
        self.assertEqual(delete_resp.status_code, 200)
        delete_data = json.loads(delete_resp.data)
        self.assertTrue(delete_data["deleted"])
        self.assertEqual(delete_data["id"], user_id)

        # Ensure the user is gone
        # Try logging in, should fail with Invalid email or password
        login_payload = {
            "email": "user_to_delete@example.com",
            "password": self.strong_password,
        }
        login_resp = self.app.post(
            "/api/auth/login",
            data=json.dumps(login_payload),
            content_type="application/json",
        )
        self.assertEqual(login_resp.status_code, 401)


if __name__ == "__main__":
    unittest.main()

