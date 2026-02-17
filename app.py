
from flask import Flask, render_template, jsonify, request
import os
from src.chakra import Chakra
from src.bandha import Bandha

app = Flask(__name__)

# Initialize Chakra
# Ensure path is correct relative to execution
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(BASE_DIR, 'Adhyaya_One_Chakras.xlsx')
chakra = Chakra(EXCEL_PATH, sheet_name='Chakra1-1-1')

@app.route('/')
def index():
    return render_template('index.html')

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
    app.run(debug=True, host='0.0.0.0', port=5000)
