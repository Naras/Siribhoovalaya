
document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('chakraCanvas');
    const ctx = canvas.getContext('2d');
    const cellCountSpan = document.getElementById('cellCount');
    const extractBtn = document.getElementById('extractTextBtn');
    const clearBtn = document.getElementById('clearPathBtn');
    const outputDiv = document.getElementById('extractedText');
    const tooltip = document.getElementById('tooltip');

    // Config
    const GRID_SIZE = 27;
    const CELL_SIZE = 30; // 810 / 27 = 30px per cell

    let gridData = [];
    let pathPoints = []; // List of {r, c} objects
    let isDrawing = false;
    let displayMode = 'number';

    // Display mode toggle
    document.querySelectorAll('input[name="displayMode"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            displayMode = e.target.value;
            drawGrid();
        });
    });

    // Fetch grid data
    fetch('/api/grid')
        .then(response => response.json())
        .then(data => {
            gridData = data;
            drawGrid();
        })
        .catch(err => {
            console.error("Failed to load grid:", err);
            outputDiv.textContent = "Error loading grid data. Please check console.";
        });

    // Drawing function
    function drawGrid() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw cells and content
        ctx.font = '14px "Tiro Kannada"';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        for (let r = 0; r < GRID_SIZE; r++) {
            for (let c = 0; c < GRID_SIZE; c++) {
                const x = c * CELL_SIZE;
                const y = r * CELL_SIZE;

                // Draw cell background if in path
                const pathIndex = pathPoints.findIndex(p => p.r === r && p.c === c);
                if (pathIndex !== -1) {
                    ctx.fillStyle = 'rgba(74, 144, 226, 0.3)';
                    ctx.fillRect(x, y, CELL_SIZE, CELL_SIZE);

                    // Optional: Draw order number
                    ctx.fillStyle = '#e74c3c';
                    ctx.font = '10px sans-serif';
                    ctx.fillText(pathIndex + 1, x + 5, y + 10);
                    ctx.font = '14px "Tiro Kannada"'; // reset font
                } else {
                    ctx.fillStyle = '#fff'; // Default bg
                }

                // Draw border
                ctx.strokeStyle = '#ddd';
                ctx.strokeRect(x, y, CELL_SIZE, CELL_SIZE);

                // Draw number/char
                if (gridData[r] && gridData[r][c]) {
                    const cell = gridData[r][c];
                    ctx.fillStyle = '#333';

                    let textToDraw = "";
                    if (displayMode === 'number') {
                        textToDraw = cell.num;
                        ctx.font = '14px "Tiro Kannada"'; // Standard font for nums
                    } else {
                        textToDraw = cell.char || "?";
                        ctx.font = '20px "Tiro Kannada"'; // Larger for Aksharas
                    }

                    ctx.fillText(textToDraw, x + CELL_SIZE / 2, y + CELL_SIZE / 2);
                }
            }
        }

        // Draw connecting lines for path
        if (pathPoints.length > 1) {
            ctx.beginPath();
            ctx.strokeStyle = '#e74c3c';
            ctx.lineWidth = 2;
            const start = pathPoints[0];
            ctx.moveTo(start.c * CELL_SIZE + CELL_SIZE / 2, start.r * CELL_SIZE + CELL_SIZE / 2);

            for (let i = 1; i < pathPoints.length; i++) {
                const p = pathPoints[i];
                ctx.lineTo(p.c * CELL_SIZE + CELL_SIZE / 2, p.r * CELL_SIZE + CELL_SIZE / 2);
            }
            ctx.stroke();
        }
    }

    // Interaction
    canvas.addEventListener('click', (e) => {
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const c = Math.floor(x / CELL_SIZE);
        const r = Math.floor(y / CELL_SIZE);

        if (r >= 0 && r < GRID_SIZE && c >= 0 && c < GRID_SIZE) {
            togglePoint(r, c);
        }
    });

    // Tooltip logic
    canvas.addEventListener('mousemove', (e) => {
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const c = Math.floor(x / CELL_SIZE);
        const r = Math.floor(y / CELL_SIZE);

        if (r >= 0 && r < GRID_SIZE && c >= 0 && c < GRID_SIZE && gridData[r] && gridData[r][c]) {
            const cell = gridData[r][c];
            tooltip.style.opacity = 1;
            tooltip.style.left = (e.pageX + 10) + 'px';
            tooltip.style.top = (e.pageY + 10) + 'px';
            tooltip.textContent = `(${r}, ${c}): ${cell.num} - ${cell.char}`;
        } else {
            tooltip.style.opacity = 0;
        }
    });

    canvas.addEventListener('mouseleave', () => {
        tooltip.style.opacity = 0;
    });

    function togglePoint(r, c) {
        // Simple toggle mode: if last point is this, remove it. Else add it.
        // Actually, for drawing a path, usually we append.
        // If we click an existing point, maybe we cut the path there?
        // Let's just append for now to be simple.

        pathPoints.push({ r, c });
        drawGrid();
        cellCountSpan.textContent = pathPoints.length;
    }

    const undoBtn = document.getElementById('undoBtn');

    undoBtn.addEventListener('click', () => {
        if (pathPoints.length > 0) {
            pathPoints.pop();
            drawGrid();
            cellCountSpan.textContent = pathPoints.length;
        }
    });

    clearBtn.addEventListener('click', () => {
        pathPoints = [];
        drawGrid();
        cellCountSpan.textContent = 0;
        outputDiv.textContent = '...';
    });

    extractBtn.addEventListener('click', () => {
        if (pathPoints.length === 0) return;

        // Prepare payload: just list of [r, c]
        const points = pathPoints.map(p => [p.r, p.c]);

        fetch('/api/traverse', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ points })
        })
            .then(res => res.json())
            .then(data => {
                outputDiv.textContent = data.text;
            })
            .catch(err => {
                outputDiv.textContent = "Error extracting text.";
                console.error(err);
            });
    });
});
