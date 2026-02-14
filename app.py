
from flask import Flask, render_template, jsonify, request
import os
from src.chakra import Chakra
from src.bandha import Bandha

app = Flask(__name__)

# Initialize Chakra
# Ensure path is correct relative to execution
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(BASE_DIR, 'Adhyaya_One_Chakras-clean.xlsx')
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
    points = data.get('points', [])
    
    # Convert list of lists/dicts to tuples if needed, but [r, c] works for our Bandha class?
    # Bandha expects list of tuples or list of lists is fine if we unpack.
    # Our bandha implementation iterates and unpacking (r, c) = point works for [r, c] or (r, c).
    
    bandha = Bandha()
    bandha.set_path(points)
    
    text = bandha.traverse(chakra)
    
    return jsonify({'text': text})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
