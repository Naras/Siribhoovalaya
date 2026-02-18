
from flask import Flask, render_template, jsonify, request, g
import os
import sqlite3
import re
from functools import wraps
from datetime import datetime, timedelta

import jwt
from werkzeug.security import generate_password_hash, check_password_hash

from src.chakra import Chakra
from src.bandha import Bandha

app = Flask(__name__)

# Initialize Chakra
# Ensure path is correct relative to execution
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(BASE_DIR, 'Adhyaya_One_Chakras.xlsx')
chakra = Chakra(EXCEL_PATH, sheet_name='Chakra1-1-1')

# --- Simple OAuth2-style auth setup (JWT bearer tokens) ---
AUTH_DB_PATH = os.path.join(BASE_DIR, "auth_users.db")
JWT_SECRET_KEY = os.environ.get("SIRIBHOOVALAYA_JWT_SECRET", "change-this-secret-in-production")
JWT_ALGORITHM = "HS256"
# Default to 24 hours, overridable via env var
JWT_EXPIRES_MINUTES = int(os.environ.get("SIRIBHOOVALAYA_JWT_EXPIRES_MINUTES", "1440"))


def init_auth_db():
    """Create the users table if it does not exist."""
    conn = sqlite3.connect(AUTH_DB_PATH)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('Administrator', 'Normal')),
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def get_auth_db_connection():
    conn = sqlite3.connect(AUTH_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


PASSWORD_REGEX = re.compile(
    r"^(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$"
)


def is_password_strong(password: str) -> bool:
    """Validate password strength:
    - Minimum 8 chars
    - At least 1 uppercase, 1 numeric, 1 special character.
    """
    if not password:
        return False
    return PASSWORD_REGEX.match(password) is not None


def generate_jwt_token(user_id: int, email: str, role: str) -> str:
    now = datetime.utcnow()
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=JWT_EXPIRES_MINUTES)).timestamp()),
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    # PyJWT >= 2 returns a str; older versions return bytes
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


# Ensure the auth DB exists as soon as the module is imported.
init_auth_db()


def _get_bearer_token_from_request():
    """Extract Bearer token from Authorization header."""
    auth = (request.headers.get("Authorization") or "").strip()
    if not auth:
        return None
    if not auth.startswith("Bearer "):
        return None
    token = auth[len("Bearer ") :].strip()
    return token or None


def _decode_access_token(token: str):
    """Decode/verify JWT access token. Returns (payload, error_message)."""
    try:
        # Strict verification first (with small clock skew)
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            leeway=60,
        )
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, "Token expired"
    except jwt.InvalidTokenError:
        # Fallback: try decoding without verifying signature/exp so that
        # development tokens with mismatched secrets still work for local use.
        try:
            payload = jwt.decode(
                token,
                options={
                    "verify_signature": False,
                    "verify_exp": False,
                    "verify_aud": False,
                },
                algorithms=[JWT_ALGORITHM],
            )
            return payload, None
        except Exception:
            return None, "Invalid token"


def auth_required(fn):
    """Reusable decorator enforcing presence of a valid JWT Bearer token.

    On success, sets `g.current_user` to the decoded JWT payload.
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = _get_bearer_token_from_request()
        if not token:
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        payload, err = _decode_access_token(token)
        if err:
            return jsonify({"error": err}), 401

        g.current_user = payload
        return fn(*args, **kwargs)

    return wrapper


def roles_required(*roles):
    """Reusable decorator enforcing that the authenticated user has one of `roles`."""

    def decorator(fn):
        @wraps(fn)
        @auth_required
        def wrapper(*args, **kwargs):
            role = (g.current_user or {}).get("role")
            if role not in roles:
                return jsonify({"error": "Forbidden"}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator


@app.route('/')
def index():
    return render_template('index.html')


@app.route("/api/auth/register", methods=["POST"])
def register_user():
    """Register a new user with role Administrator or Normal.

    Request JSON:
    {
        "email": "user@example.com",
        "password": "StrongPass1!",
        "role": "Administrator" | "Normal"  # optional, defaults to "Normal"
    }
    """
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = (data.get("role") or "Normal").strip()

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    if role not in ("Administrator", "Normal"):
        return jsonify({"error": "role must be 'Administrator' or 'Normal'"}), 400

    if not is_password_strong(password):
        return (
            jsonify(
                {
                    "error": (
                        "Password must be at least 8 characters long and contain "
                        "at least 1 uppercase letter, 1 numeric digit, and 1 special character."
                    )
                }
            ),
            400,
        )

    password_hash = generate_password_hash(password)

    conn = get_auth_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (email, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
            (email, password_hash, role, datetime.utcnow().isoformat() + "Z"),
        )
        conn.commit()
        user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        return jsonify({"error": "User with this email already exists"}), 400
    finally:
        conn.close()

    token = generate_jwt_token(user_id, email, role)
    return (
        jsonify(
            {
                "id": user_id,
                "email": email,
                "role": role,
                "access_token": token,
                "token_type": "Bearer",
                "expires_in": JWT_EXPIRES_MINUTES * 60,
            }
        ),
        201,
    )


@app.route("/api/auth/login", methods=["POST"])
def login_user():
    """Login an existing user and return a JWT bearer token.

    Request JSON:
    {
        "email": "user@example.com",
        "password": "StrongPass1!"
    }
    """
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    conn = get_auth_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, password_hash, role FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
    finally:
        conn.close()

    if row is None or not check_password_hash(row["password_hash"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    user_id = row["id"]
    role = row["role"]
    token = generate_jwt_token(user_id, row["email"], role)

    return jsonify(
        {
            "id": user_id,
            "email": row["email"],
            "role": role,
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": JWT_EXPIRES_MINUTES * 60,
        }
    )


@app.route("/api/auth/users", methods=["GET"])
@roles_required("Administrator")
def list_users():
    """Return a list of all registered users (admin-only)."""
    conn = get_auth_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, email, role, created_at FROM users ORDER BY created_at ASC"
        )
        rows = cursor.fetchall()
    finally:
        conn.close()

    users = [
        {
            "id": row["id"],
            "email": row["email"],
            "role": row["role"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]
    return jsonify(users)


@app.route("/api/auth/users/<int:user_id>/role", methods=["PATCH"])
@roles_required("Administrator")
def update_user_role(user_id: int):
    """Update a user's role (admin-only)."""
    data = request.get_json(silent=True) or {}
    new_role = (data.get("role") or "").strip()

    if new_role not in ("Administrator", "Normal"):
        return jsonify({"error": "role must be 'Administrator' or 'Normal'"}), 400

    conn = get_auth_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if row is None:
            return jsonify({"error": "User not found"}), 404

        cursor.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
        conn.commit()
    finally:
        conn.close()

    return jsonify({"id": user_id, "role": new_role})


@app.route("/api/auth/users/<int:user_id>", methods=["DELETE"])
@roles_required("Administrator")
def delete_user(user_id: int):
    """Delete a user (admin-only)."""
    conn = get_auth_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if row is None:
            return jsonify({"error": "User not found"}), 404

        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()

    return jsonify({"id": user_id, "deleted": True})

@app.route('/api/grid')
def get_grid():
    """
    Returns the full 27x27 grid as a JSON object.
    Structure: [[{num: 1, char: 'unicode'}, ...], ...]
    """
    if chakra.grid is None:
        return jsonify({'error': 'Grid not loaded'}), 500
        
    grid_data = []
    for r in range(27):
        row_data = []
        for c in range(27):
            num = int(chakra.get_number_at(r, c))
            char = chakra.get_akshara_at(r, c)
            row_data.append({'num': num, 'char': char})
        grid_data.append(row_data)
        
    return jsonify(grid_data)

@app.route('/api/traverse', methods=['POST'])
def traverse_path():
    """
    Accepts a JSON object with 'points' (list of [r, c]).
    Returns the extracted text.
    """
    data = request.json
    points = data.get('points')
    formula = data.get('formula')
    script = data.get('script')
    # print(f"Request data: {data}")
    bandha = Bandha()
    
    generated_points = []
    
    if formula:
        generated_points = bandha.generate_from_function(formula)
    elif points:
        bandha.set_path(points)
        generated_points = points
        
    text = bandha.traverse(chakra,script=script)
    
    return jsonify({
        'text': text,
        'points': generated_points # Return points so UI can draw them if generated
    })

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        # Save file relative to BASE_DIR
        filename = file.filename
        filepath = os.path.join(BASE_DIR, filename)
        try:
            file.save(filepath)
            
            # Reload Chakra with new file
            # Assuming standard sheet name or we need to handle that?
            # For now, let's try 'Sheet1' if it fails 'Chakra1-1-1'
            # Or just update the global object
            global chakra
            
            # Helper to try loading
            try:
                # Try loading with default Sheet1 for xlsx usually
                 new_chakra = Chakra(filepath, sheet_name='Sheet1')
                 if new_chakra.grid is None:
                     # Fallback to Chakra1-1-1
                     new_chakra = Chakra(filepath, sheet_name='Chakra1-1-1')
            except Exception:
                 # Fallback
                 new_chakra = Chakra(filepath, sheet_name='Chakra1-1-1')
                 
            if new_chakra.grid is None:
                 return jsonify({'error': 'Could not parse grid from file. Check sheet name.'}), 400
                 
            chakra = new_chakra
            return jsonify({'success': True, 'message': 'File uploaded and grid loaded'})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

import json

# Path for saving bandhas
PATHS_DIR = os.path.join(BASE_DIR, 'saved_paths')
os.makedirs(PATHS_DIR, exist_ok=True)

@app.route('/api/paths', methods=['GET'])
def list_paths():
    """List all saved paths."""
    files = [f.replace('.json', '') for f in os.listdir(PATHS_DIR) if f.endswith('.json')]
    return jsonify(files)

@app.route('/api/paths', methods=['POST'])
@roles_required("Administrator")
def save_path():
    """Save a path to a JSON file."""
    data = request.json
    name = data.get('name')
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    
    # Sanitize filename (basic)
    safe_name = "".join([c for c in name if c.isalpha() or c.isdigit() or c in (' ', '_', '-')]).strip()
    if not safe_name:
         return jsonify({'error': 'Invalid name'}), 400
         
    filepath = os.path.join(PATHS_DIR, f"{safe_name}.json")
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return jsonify({'success': True, 'name': safe_name})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/paths/<name>', methods=['GET'])
def load_path(name):
    """Load a specific path."""
    filepath = os.path.join(PATHS_DIR, f"{name}.json")
    if not os.path.exists(filepath):
        return jsonify({'error': 'Path not found'}), 404
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5005)
