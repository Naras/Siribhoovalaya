# Siribhoovalaya Visualizer

## Introduction

**Siribhoovalaya** (Kannada: ಸಿರಿಭೂವಲಯ) is a unique multilingual literary work written by the 9th-century Jain monk **Kumudendu Muni**. Its most distinctive feature is that it is composed entirely of Kannada numerals (1-64) rather than alphabets, arranged in a 729-cell grid (27x27 squares) called a **Chakra**.

This numerical system is capable of encoding nearly 18 scripts and over 700 languages, including Kannada, Sanskrit, Telugu, Tamil, Prakrit, and Apabhransha. The text is deciphered by applying specific patterns or paths, known as **Bandhas**, to the grid. By tracing these paths, the sequence of numbers yields meaningful text in the target language. The work is renowned not only for its linguistic complexity but also for purportedly encoding vast knowledge spanning philosophy, science, medicine, and history.

## Project Realization

This application is a digital realization of the Siribhoovalaya system. It serves as a tool for researchers and enthusiasts to:
1.  **Visualize** the 27x27 Chakra grid.
2.  **Interact** with the grid by drawing or defining Bandhas (paths).
3.  **Extract** and **Transliterate** the encoded text dynamically.

The application is built as a web-based tool to ensure accessibility and visual interactivity. It faithfully loads the grid data from the original manuscript source (digitalized in Excel) and uses a custom transliteration engine to map the ancient numerical codes to modern Kannada script.

### Technical Architecture

The project follows a modular client-server architecture:
*   **Backend**: Python 3 & Flask. Handles data loading, business logic, and text transliteration.
*   **Frontend**: HTML5 Canvas & JavaScript. Handles grid rendering, user interaction, and path capturing.

### Module Structure

```
Siribhoovalaya/
├── app.py                 # Flask Server & API Entry Point
├── Adhyaya_One_Chakras.xls # Core Data Source (The Chakra Grid)
├── src/
│   ├── chakra.py          # Data Model: Manages the 27x27 grid
│   ├── bandha.py          # Logic: Handles path traversal mechanics
│   └── transliterate.py   # Utility: Maps numbers (1-64) to Kannada characters
├── static/
│   ├── css/style.css      # Styling (Clean, modern UI)
│   └── js/main.js         # Frontend Logic (Canvas drawing, API calls)
├── templates/
│   └── index.html         # Main User Interface
└── tests/
    └── test_integration.py # Automated verification suite
```

### Module Functions

#### Backend
1.  **`app.py`**: Initializes the Flask app, loads the `Chakra` object at startup, and exposes REST endpoints.
2.  **`src/chakra.py`**: 
    *   Reads `Adhyaya_One_Chakras.xls` (specifically sheet `Chakra1-1-1`).
    *   Extracts the 27x27 numeric grid.
    *   Provides accessors to get numbers or Aksharas at specific coordinates.
3.  **`src/transliterate.py`**: 
    *   Contains the `AKSHARA_MAP` which links numbers 1-64 to Devanagari characters.
    *   Implements logic to transliterate Devanagari to Kannada Unicode.
4.  **`src/bandha.py`**: 
    *   Accepts a list of coordinates.
    *   Traverses the `Chakra` grid.
    *   Aggregates the characters to form the result string.

#### Frontend
1.  **`index.html`**: Host page. Loads fonts (Tiro Kannada) and structure.
2.  **`main.js`**: 
    *   Fetches grid data on load.
    *   Renders the 27x27 grid on an HTML5 Canvas.
    *   Handles mouse clicks/drags to define a path.
    *   Sends path coordinates to the backend for extraction.
    *   Displays the result.

### REST API Description

The frontend and backend communicate via JSON-based REST APIs:

#### 1. Get Grid Data
*   **Endpoint**: `GET /api/grid`
*   **Description**: Retrieves the full numeric and character representation of the 27x27 grid.
*   **Response**:
    ```json
    [
      [
        {"num": 59, "char": "ಸ್"}, 
        {"num": 23, "char": "ಓ"}, 
        ...
      ],
      ...
    ]
    ```

#### 2. Traverse Bandha
*   **Endpoint**: `POST /api/traverse`
*   **Description**: Submits a path (sequence of coordinates) to extract text.
*   **Request**:
    ```json
    {
      "points": [[0, 0], [0, 1], [1, 1]]
    }
    ```
*   **Response**:
    ```json
    {
      "text": "ಸಓ..." 
    }
    ```

## Running the Application

1.  **Setup Environment**:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install pandas xlrd openpyxl flask
    ```

2.  **Start Server**:
    ```bash
    python3 app.py
    ```

3.  **Access**: Open `http://127.0.0.1:5000` in your browser.
