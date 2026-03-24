
document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('chakraCanvas');
    const ctx = canvas.getContext('2d');
    const cellCountSpan = document.getElementById('cellCount');
    const extractBtn = document.getElementById('extractTextBtn');
    const clearBtn = document.getElementById('clearPathBtn');
    const outputDiv = document.getElementById('extractedText');
    const outputDivSandhi = document.getElementById('extractedTextSandhi');
    const tooltip = document.getElementById('tooltip');

    // Config
    const GRID_SIZE = 27;
    const CELL_SIZE = 30; // 810 / 27 = 30px per cell

    let gridData = [];
    let pathPoints = []; // List of {r, c} objects
    let isDrawing = false;
    let displayMode = 'number';

    // Simple auth state (stored in-memory and in localStorage)
    let authState = {
        accessToken: null,
        email: null,
        role: null,
    };

    function loadAuthState() {
        try {
            const raw = localStorage.getItem('sb_auth');
            if (!raw) return;
            const parsed = JSON.parse(raw);
            if (parsed && parsed.accessToken && parsed.email && parsed.role) {
                authState = parsed;
            }
        } catch (e) {
            console.warn('Failed to load auth from localStorage', e);
        }
    }

    function saveAuthState() {
        try {
            if (authState && authState.accessToken) {
                localStorage.setItem('sb_auth', JSON.stringify(authState));
            } else {
                localStorage.removeItem('sb_auth');
            }
        } catch (e) {
            console.warn('Failed to save auth to localStorage', e);
        }
    }

    function clearAuthState() {
        authState = { accessToken: null, email: null, role: null };
        saveAuthState();
        renderAuthBar();
    }

    function getAuthHeaders(baseHeaders = {}) {
        const headers = { ...baseHeaders };
        if (authState.accessToken) {
            headers['Authorization'] = `Bearer ${authState.accessToken}`;
        }
        return headers;
    }

    function renderAuthBar() {
        let authBar = document.getElementById('authBar');
        if (!authBar) {
            const header = document.querySelector('header');
            if (!header) {
                return;
            }
            authBar = document.createElement('div');
            authBar.id = 'authBar';
            authBar.style.display = 'flex';
            authBar.style.justifyContent = 'flex-end';
            authBar.style.gap = '8px';
            authBar.style.alignItems = 'center';
            header.appendChild(authBar);
        }

        authBar.innerHTML = '';

        if (!authState.accessToken) {
            // Not logged in: show Register / Login
            const registerBtn = document.createElement('button');
            registerBtn.textContent = 'Register';
            registerBtn.addEventListener('click', handleRegisterClick);

            const loginBtn = document.createElement('button');
            loginBtn.textContent = 'Login';
            loginBtn.addEventListener('click', handleLoginClick);

            authBar.appendChild(registerBtn);
            authBar.appendChild(loginBtn);
        } else {
            // Logged in
            const infoSpan = document.createElement('span');
            infoSpan.textContent = `${authState.email} (${authState.role})`;
            infoSpan.style.marginRight = '8px';

            const logoutBtn = document.createElement('button');
            logoutBtn.textContent = 'Logout';
            logoutBtn.addEventListener('click', () => {
                clearAuthState();
                alert('Logged out.');
            });

            authBar.appendChild(infoSpan);

            if (authState.role === 'Administrator') {
                const usersBtn = document.createElement('button');
                usersBtn.textContent = 'View Users';
                usersBtn.addEventListener('click', handleViewUsersClick);
                authBar.appendChild(usersBtn);
            }

            authBar.appendChild(logoutBtn);
        }
    }

    function handleRegisterClick() {
        const email = window.prompt('Enter email to register:');
        if (!email) return;
        const password = window.prompt('Enter password (min 8, 1 upper, 1 digit, 1 special):');
        if (!password) return;

        // Normal users self-register; do not allow self-setting Administrator here.
        const payload = { email, password };

        fetch('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        })
            .then(res => res.json().then(data => ({ status: res.status, data })))
            .then(({ status, data }) => {
                if (status !== 201) {
                    alert(data.error || 'Registration failed.');
                    return;
                }
                authState = {
                    accessToken: data.access_token,
                    email: data.email,
                    role: data.role,
                };
                saveAuthState();
                renderAuthBar();
                alert('Registration successful.');
            })
            .catch(err => {
                console.error('Register error', err);
                alert('Registration error, please check console.');
            });
    }

    function handleLoginClick() {
        const email = window.prompt('Enter email:');
        if (!email) return;
        const password = window.prompt('Enter password:');
        if (!password) return;

        const payload = { email, password };

        fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        })
            .then(res => res.json().then(data => ({ status: res.status, data })))
            .then(({ status, data }) => {
                if (status !== 200) {
                    alert(data.error || 'Login failed.');
                    return;
                }
                authState = {
                    accessToken: data.access_token,
                    email: data.email,
                    role: data.role,
                };
                saveAuthState();
                renderAuthBar();
                alert('Login successful.');
            })
            .catch(err => {
                console.error('Login error', err);
                alert('Login error, please check console.');
            });
    }

    function handleViewUsersClick() {
        fetch('/api/auth/users', {
            method: 'GET',
            headers: getAuthHeaders(),
        })
            .then(res => res.json().then(data => ({ status: res.status, data })))
            .then(({ status, data }) => {
                if (status !== 200) {
                    alert((data && data.error) || 'Failed to load users.');
                    return;
                }
                if (!Array.isArray(data) || data.length === 0) {
                    alert('No users found.');
                    return;
                }
                const lines = data.map(
                    u => `${u.id}: ${u.email} [${u.role}]`
                );
                alert('Registered users:\n\n' + lines.join('\n'));

                // Simple admin actions: promote or delete a user.
                const action = window.prompt(
                    'Admin actions:\n' +
                    'P <id>  - Promote user to Administrator\n' +
                    'D <id>  - Delete user\n\n' +
                    'Example: "P 2" or "D 3". Leave blank to cancel.'
                );
                if (!action) {
                    return;
                }

                const parts = action.trim().split(/\s+/);
                if (parts.length !== 2) {
                    alert('Invalid command. Use "P <id>" or "D <id>".');
                    return;
                }

                const cmd = parts[0].toUpperCase();
                const idStr = parts[1];
                const userId = parseInt(idStr, 10);
                if (Number.isNaN(userId)) {
                    alert('Invalid user ID.');
                    return;
                }

                if (cmd === 'P') {
                    // Promote to Administrator
                    fetch(`/api/auth/users/${userId}/role`, {
                        method: 'PATCH',
                        headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
                        body: JSON.stringify({ role: 'Administrator' }),
                    })
                        .then(res => res.json().then(respData => ({ status: res.status, data: respData })))
                        .then(({ status, data }) => {
                            if (status !== 200) {
                                alert((data && data.error) || 'Failed to update user role.');
                                return;
                            }
                            alert(`User ${userId} promoted to Administrator.`);
                        })
                        .catch(err => {
                            console.error('Promote user error', err);
                            alert('Error promoting user, please check console.');
                        });
                } else if (cmd === 'D') {
                    // Delete user
                    const confirmed = window.confirm(
                        `Are you sure you want to delete user ${userId}? This cannot be undone.`
                    );
                    if (!confirmed) {
                        return;
                    }

                    fetch(`/api/auth/users/${userId}`, {
                        method: 'DELETE',
                        headers: getAuthHeaders(),
                    })
                        .then(res => res.json().then(respData => ({ status: res.status, data: respData })))
                        .then(({ status, data }) => {
                            if (status !== 200) {
                                alert((data && data.error) || 'Failed to delete user.');
                                return;
                            }
                            alert(`User ${userId} deleted.`);
                        })
                        .catch(err => {
                            console.error('Delete user error', err);
                            alert('Error deleting user, please check console.');
                        });
                } else {
                    alert('Unknown command. Use "P <id>" or "D <id>".');
                }
            })
            .catch(err => {
                console.error('View users error', err);
                alert('Error loading users, please check console.');
            });
    }

    // Display mode toggle
    document.querySelectorAll('input[name="displayMode"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            displayMode = e.target.value;
            drawGrid();
        });
    });

    // Load auth state and render navbar
    loadAuthState();
    renderAuthBar();

    // Fetch grid data
    loadGrid();

    function loadGrid() {
        fetch('/api/grid')
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    outputDiv.textContent = data.error;
                    return;
                }
                gridData = data;
                drawGrid();
            })
            .catch(err => {
                console.error("Failed to load grid:", err);
                outputDiv.textContent = "Error loading grid data. Please check console.";
            });
    }

    // Upload Logic
    const uploadBtn = document.getElementById('uploadBtn');
    const fileInput = document.getElementById('chakraFile');

    if (uploadBtn) {
        uploadBtn.addEventListener('click', () => {
            const file = fileInput.files[0];
            if (!file) {
                alert("Please select a file first.");
                return;
            }

            const formData = new FormData();
            formData.append('file', file);

            outputDiv.textContent = "Uploading...";

            fetch('/api/upload', {
                method: 'POST',
                body: formData
            })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        outputDiv.textContent = "Grid loaded successfully!";
                        loadGrid(); // Reload grid data
                    } else {
                        outputDiv.textContent = "Error: " + data.error;
                    }
                })
                .catch(err => {
                    console.error("Upload error:", err);
                    outputDiv.textContent = "Upload failed.";
                });
        });
    }

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
                    // console.log(`Drawing cell (${r}, ${c}):`, cell);
                    ctx.fillStyle = '#333';

                    let textToDraw = "";
                    if (displayMode === 'number') {
                        textToDraw = cell.num;
                        ctx.font = '14px "Tiro Kannada"'; // Standard font for nums
                    } else if (displayMode === 'ಅಕ್ಷರಗಳು') {
                        textToDraw = cell.char[0] || "?";
                        ctx.font = '16px "Tiro Kannada"'; // Larger for ಅಕ್ಷರಗಳು
                    }
                    else {
                        textToDraw = cell.char[1] || "?";
                        ctx.font = '16px "Tiro Devanagari Hindi"'; // Larger for अक्षराणी
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
            // Show the starting cell coordinates that would lead to this cell
            // For Shreni Bandha, if tooltip shows (r,c), algorithm should start from (r+1,c-1)
            const startRow = r + 1;
            const startCol = c - 1;
            tooltip.textContent = `(${startRow}, ${startCol}): ${cell.num} - ${cell.char}`;
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
        outputDivSandhi.textContent = '...';
    });

    extractBtn.addEventListener('click', () => {
        if (pathPoints.length === 0) return;

        // Prepare payload: just list of [r, c]
        const points = pathPoints.map(p => [p.r, p.c]);
        if (displayMode === 'ಅಕ್ಷರಗಳು') script = 'kannada';
        else script = 'devanagari';
        // console.log("Extract text for:", JSON.stringify({ points, script }));

        fetch('/api/traverse', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ points, script })
        })
            .then(res => res.json())
            .then(data => {
                outputDiv.textContent = data.text_without_sandhi || '...';
                outputDivSandhi.textContent = data.text_with_sandhi || '...';
            })
            .catch(err => {
                outputDiv.textContent = "Error extracting text.";
                outputDivSandhi.textContent = "Error extracting text.";
                console.error(err);
            });
    });

    // Save/Load Logic
    const savePathBtn = document.getElementById('savePathBtn');
    const loadPathBtn = document.getElementById('loadPathBtn');
    const pathNameInput = document.getElementById('pathNameInput');
    const savedPathsSelect = document.getElementById('savedPathsSelect');

    function updateSavedPathsList() {
        fetch('/api/paths')
            .then(res => res.json())
            .then(names => {
                savedPathsSelect.innerHTML = '<option value="">-- Select Saved Path --</option>';
                names.forEach(name => {
                    const option = document.createElement('option');
                    option.value = name;
                    option.textContent = name;
                    savedPathsSelect.appendChild(option);
                });
            })
            .catch(err => console.error("Error fetching paths:", err));
    }

    // Load paths on startup
    updateSavedPathsList();

    if (savePathBtn) {
        savePathBtn.addEventListener('click', () => {
            const name = pathNameInput.value.trim();
            if (!name) {
                alert("Please enter a name for the path.");
                return;
            }
            if (pathPoints.length === 0 && !formulaInput.value.trim()) {
                alert("Nothing to save (no points or formula).");
                return;
            }

            const payload = {
                name: name,
                points: pathPoints.map(p => [p.r, p.c]),
                formula: formulaInput.value.trim(),
                text: outputDiv.textContent,
                text_with_sandhi: outputDivSandhi.textContent
            };

            if (!authState.accessToken || authState.role !== 'Administrator') {
                alert('Only logged-in administrators can save paths.');
                return;
            }

            fetch('/api/paths', {
                method: 'POST',
                headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
                body: JSON.stringify(payload)
            })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        alert("Path saved successfully!");
                        pathNameInput.value = '';
                        updateSavedPathsList();
                    } else {
                        alert("Error saving: " + data.error);
                    }
                })
                .catch(err => console.error("Save error:", err));
        });
    }

    if (loadPathBtn) {
        loadPathBtn.addEventListener('click', () => {
            const name = savedPathsSelect.value;
            if (!name) {
                alert("Please select a path to load.");
                return;
            }

            fetch(`/api/paths/${name}`)
                .then(res => res.json())
                .then(data => {
                    if (data.error) {
                        alert("Error loading: " + data.error);
                        return;
                    }

                    // Restore state
                    if (data.points) {
                        pathPoints = data.points.map(p => ({ r: p[0], c: p[1] }));
                    } else {
                        pathPoints = [];
                    }

                    if (data.formula) {
                        formulaInput.value = data.formula;
                    } else {
                        formulaInput.value = '';
                    }

                    if (data.text) {
                        outputDiv.textContent = data.text;
                    }
                    
                    if (data.text_with_sandhi) {
                        outputDivSandhi.textContent = data.text_with_sandhi;
                    }

                    cellCountSpan.textContent = pathPoints.length;
                    drawGrid();
                })
                .catch(err => console.error("Load error:", err));
        });
    }

    // Go Button Logic
    const formulaInput = document.getElementById('bandhaFormula');
    const generateBtn = document.getElementById('generateBandhaBtn');

    // Bandha Pattern Controls
    const patternTypeSelect = document.getElementById('patternType');
    const patternParamsDiv = document.getElementById('patternParams');
    const patternSearchBtn = document.getElementById('patternSearchBtn');
    let currentPatternGenerateBtn = null;

    // Pattern parameter templates
    const patternTemplates = {
        horizontal_zigzag: `
            <h4>Horizontal Zig-Zag</h4>
            <div class="param-row">
                <label>Start Row:</label>
                <input type="number" id="hzStartRow" value="13" min="0" max="26">
                <label>Start Col:</label>
                <input type="number" id="hzStartCol" value="10" min="0" max="26">
                <label>Length:</label>
                <input type="number" id="hzLength" value="12" min="1" max="50">
                <button id="generatePatternBtn">Generate</button>
            </div>
        `,
        vertical_zigzag: `
            <h4>Vertical Zig-Zag</h4>
            <div class="param-row">
                <label>Start Row:</label>
                <input type="number" id="vzStartRow" value="10" min="0" max="26">
                <label>Start Col:</label>
                <input type="number" id="vzStartCol" value="13" min="0" max="26">
                <label>Length:</label>
                <input type="number" id="vzLength" value="12" min="1" max="50">
                <button id="generatePatternBtn">Generate</button>
            </div>
        `,
        chess_knight: `
            <h4>Chess Knight Moves</h4>
            <div class="param-row">
                <label>Start Row:</label>
                <input type="number" id="knightStartRow" value="13" min="0" max="26">
                <label>Start Col:</label>
                <input type="number" id="knightStartCol" value="13" min="0" max="26">
                <label>Jumps:</label>
                <input type="number" id="knightJumps" value="6" min="1" max="20">
                <button id="generatePatternBtn">Generate</button>
            </div>
            <div class="param-options">
                <label>
                    <input type="checkbox" id="knightAvoidEdges"> Avoid Edges
                </label>
                <label style="margin-left: 10px;">
                    Random Seed:
                    <input type="number" id="knightSeed" value="42" min="0" max="9999" style="width: 60px;">
                </label>
                <div style="margin-top: 5px;">
                    <label style="font-size: 12px;">Preferred Directions:</label>
                    <label style="font-size: 12px;">
                        <input type="checkbox" name="knightDir" value="up"> Up
                    </label>
                    <label style="font-size: 12px;">
                        <input type="checkbox" name="knightDir" value="down"> Down
                    </label>
                    <label style="font-size: 12px;">
                        <input type="checkbox" name="knightDir" value="left"> Left
                    </label>
                    <label style="font-size: 12px;">
                        <input type="checkbox" name="knightDir" value="right"> Right
                    </label>
                </div>
            </div>
        `,
        shreni_bandha: `
            <h4>Shreni Bandha (Diagonal Fold)</h4>
            <div class="param-row">
                <label>Start Row:</label>
                <input type="number" id="shreniStartRow" value="1" min="0" max="26">
                <label>Start Col:</label>
                <input type="number" id="shreniStartCol" value="12" min="0" max="26">
                <label>Steps:</label>
                <input type="number" id="shreniSteps" value="12" min="1" max="50">
                <button id="generatePatternBtn">Generate</button>
            </div>
            <div class="param-options">
                <label style="font-size: 12px;">Direction:</label>
                <label style="font-size: 12px;">
                    <input type="radio" name="shreniDirection" value="up" checked> Up-Right
                </label>
                <label style="font-size: 12px;">
                    <input type="radio" name="shreniDirection" value="down"> Down-Left
                </label>
            </div>
        `
    };

    // Pattern type change handler
    if (patternTypeSelect) {
        patternTypeSelect.addEventListener('change', (e) => {
            const patternType = e.target.value;
            
            // Clear previous parameters and button event
            if (currentPatternGenerateBtn) {
                currentPatternGenerateBtn.removeEventListener('click', handlePatternGeneration);
            }
            
            if (patternType && patternTemplates[patternType]) {
                patternParamsDiv.innerHTML = patternTemplates[patternType];
                currentPatternGenerateBtn = document.getElementById('generatePatternBtn');
                
                if (currentPatternGenerateBtn) {
                    currentPatternGenerateBtn.addEventListener('click', handlePatternGeneration);
                }
            } else {
                patternParamsDiv.innerHTML = '<div style="color: #666; font-size: 12px; padding: 10px;">Select a pattern to see parameters</div>';
                currentPatternGenerateBtn = null;
            }
        });
    }

    // Unified pattern generation handler
    function handlePatternGeneration() {
        const patternType = patternTypeSelect.value;
        const script = getCurrentScript();
        const use_sandhi = getCurrentUseSandhi();
        
        if (!patternType) return;
        
        let endpoint, requestData;
        
        switch (patternType) {
            case 'horizontal_zigzag':
                endpoint = '/api/bandha/horizontal_zigzag';
                requestData = {
                    start_row: parseInt(document.getElementById('hzStartRow').value),
                    start_col: parseInt(document.getElementById('hzStartCol').value),
                    length: parseInt(document.getElementById('hzLength').value),
                    script,
                    use_sandhi
                };
                break;
                
            case 'vertical_zigzag':
                endpoint = '/api/bandha/vertical_zigzag';
                requestData = {
                    start_row: parseInt(document.getElementById('vzStartRow').value),
                    start_col: parseInt(document.getElementById('vzStartCol').value),
                    length: parseInt(document.getElementById('vzLength').value),
                    script,
                    use_sandhi
                };
                break;
                
            case 'chess_knight':
                endpoint = '/api/bandha/chess_knight';
                const constraints = {};
                if (document.getElementById('knightAvoidEdges').checked) {
                    constraints.avoid_edges = true;
                }
                const seedValue = document.getElementById('knightSeed').value;
                if (seedValue) {
                    constraints.random_seed = parseInt(seedValue);
                }
                const preferredDirections = [];
                document.querySelectorAll('input[name="knightDir"]:checked').forEach(checkbox => {
                    preferredDirections.push(checkbox.value);
                });
                if (preferredDirections.length > 0) {
                    constraints.preferred_directions = preferredDirections;
                }
                
                requestData = {
                    start_row: parseInt(document.getElementById('knightStartRow').value),
                    start_col: parseInt(document.getElementById('knightStartCol').value),
                    num_jumps: parseInt(document.getElementById('knightJumps').value),
                    constraints,
                    script,
                    use_sandhi
                };
                break;
                
            case 'shreni_bandha':
                endpoint = '/api/bandha/shreni_bandha';
                requestData = {
                    start_row: parseInt(document.getElementById('shreniStartRow').value),
                    start_col: parseInt(document.getElementById('shreniStartCol').value),
                    num_steps: parseInt(document.getElementById('shreniSteps').value),
                    direction: document.querySelector('input[name="shreniDirection"]:checked').value,
                    script,
                    use_sandhi
                };
                break;
                
            default:
                return;
        }
        
        fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        })
            .then(res => res.json())
            .then(data => {
                pathPoints = data.points.map(p => ({ r: p[0], c: p[1] }));
                cellCountSpan.textContent = pathPoints.length;
                outputDiv.textContent = data.text_without_sandhi;
                outputDivSandhi.textContent = data.text_with_sandhi;
                drawGrid();
            })
            .catch(err => {
                console.error("Pattern generation error:", err);
                outputDiv.textContent = `Failed to generate ${patternType} pattern.`;
            });
    }

    // Initialize with empty state
    if (patternParamsDiv) {
        patternParamsDiv.innerHTML = '<div style="color: #666; font-size: 12px; padding: 10px;">Select a pattern to see parameters</div>';
    }

    if (generateBtn) {
        generateBtn.addEventListener('click', () => {
            console.log("Go button clicked");
            const formula = formulaInput.value.trim();
            // console.log("Formula:", formula);

            if (!formula) {
                console.warn("Empty formula");
                return;
            }

            if (displayMode === 'ಅಕ್ಷರಗಳು') script = 'kannada';
            else script = 'devanagari'; // console.log("Default script for generation:", script);
            // console.log("Sending request to /api/traverse");
            fetch('/api/traverse', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ formula, script })
            })
                .then(res => {
                    console.log("Response status:", res.status);
                    return res.json();
                })
                .then(data => {
                    // console.log("Data received:", data);
                    if (data.points) {
                        pathPoints = data.points.map(p => ({ r: p[0], c: p[1] }));
                        cellCountSpan.textContent = pathPoints.length;
                        drawGrid();
                    }
                    outputDiv.textContent = data.text_without_sandhi || '...';
                    outputDivSandhi.textContent = data.text_with_sandhi || '...';
                })
                .catch(err => {
                    outputDiv.textContent = "Error generating bandha.";
                    outputDivSandhi.textContent = "Error generating bandha.";
                    console.error("Fetch error:", err);
                });
        });
    } else {
        console.error("Generate button not found!");
    }

    // Search Logic
    const searchInput = document.getElementById('searchInput');
    const searchMeasure = document.getElementById('searchMeasure');
    const searchMaxDist = document.getElementById('searchMaxDist');
    const useSandhiCheckbox = document.getElementById('useSandhi');
    const searchBtn = document.getElementById('searchBtn');

    // Target Strings Dropdown
    const targetStringsDropdown = document.getElementById('targetStringsDropdown');
    const refreshStringsBtn = document.getElementById('refreshStringsBtn');

    // Debug: Check if elements are found
    console.log('Target strings dropdown element:', targetStringsDropdown);
    console.log('Refresh button element:', refreshStringsBtn);

    // Load target strings from server
    async function loadTargetStrings() {
        console.log('Loading target strings...');
        
        if (!targetStringsDropdown) {
            console.error('Target strings dropdown not found!');
            return;
        }
        
        try {
            const response = await fetch('/api/target_strings');
            console.log('Response status:', response.status);
            
            if (!response.ok) {
                console.warn('Failed to load target strings:', response.statusText);
                return;
            }
            const data = await response.json();
            console.log('Received data:', data);
            
            const strings = data.strings || [];
            console.log('Strings count:', strings.length);
            
            // Clear existing options except the first one
            targetStringsDropdown.innerHTML = '<option value="">-- Select Target String --</option>';
            
            // Add new options with language info
            strings.forEach(str => {
                const option = document.createElement('option');
                option.value = str;
                const language = detectLanguage(str);
                option.textContent = `${str} [${language}]`;
                option.setAttribute('data-language', language);
                targetStringsDropdown.appendChild(option);
                console.log(`Added option: ${str} [${language}]`);
            });
            
            console.log('Dropdown population complete');
        } catch (error) {
            console.error('Error loading target strings:', error);
        }
    }

    // Detect language (Kannada or Devanagari) based on Unicode ranges
    function detectLanguage(text) {
        if (!text) return 'Unknown';
        
        // Unicode ranges for Kannada (ಅ to ೡ): 0xC85 to 0xCF2
        // Unicode ranges for Devanagari (अ to ॡ): 0x905 to 0x97F
        let kannadaCount = 0;
        let devanagariCount = 0;
        
        for (let char of text) {
            const code = char.charCodeAt(0);
            if ((code >= 0xC85 && code <= 0xCF2) || (code >= 0xCE6 && code <= 0xCEF)) {
                kannadaCount++;
            } else if ((code >= 0x905 && code <= 0x97F) || (code >= 0x966 && code <= 0x96F)) {
                devanagariCount++;
            }
        }
        
        if (kannadaCount > devanagariCount) return 'Kannada';
        if (devanagariCount > kannadaCount) return 'Devanagari';
        return 'Mixed/Unknown';
    }

    // Set script mode based on detected language
    function setScriptMode(language) {
        const scriptRadios = document.querySelectorAll('input[name="displayMode"]');
        let targetValue = 'number'; // default
        
        if (language === 'Kannada') {
            targetValue = 'ಅಕ್ಷರಗಳು';
        } else if (language === 'Devanagari') {
            targetValue = 'अक्षराणी';
        }
        
        scriptRadios.forEach(radio => {
            if (radio.value === targetValue) {
                radio.checked = true;
                displayMode = targetValue;
                // Trigger change event to update display
                radio.dispatchEvent(new Event('change'));
            }
        });
    }

    // Handle dropdown selection
    if (targetStringsDropdown) {
        targetStringsDropdown.addEventListener('change', (e) => {
            const selectedOption = e.target.options[e.target.selectedIndex];
            const selectedString = e.target.value;
            const detectedLanguage = selectedOption.getAttribute('data-language');
            
            if (selectedString) {
                searchInput.value = selectedString;
                
                // Automatically set script mode based on detected language
                if (detectedLanguage && detectedLanguage !== 'Mixed/Unknown') {
                    setScriptMode(detectedLanguage);
                    console.log(`Language detected: ${detectedLanguage}, script mode set accordingly`);
                }
            }
        });
    }

    // Handle refresh button
    if (refreshStringsBtn) {
        refreshStringsBtn.addEventListener('click', loadTargetStrings);
    }

    // Load target strings on page load with a small delay to ensure DOM is ready
    setTimeout(() => {
        console.log('Attempting to load target strings after timeout...');
        loadTargetStrings();
    }, 100);

    if (searchBtn) {
        searchBtn.addEventListener('click', () => {
            const target = searchInput.value.trim();
            if (!target) {
                alert("Please enter target text to search.");
                return;
            }

            const measure = searchMeasure.value;
            const max_distance = parseInt(searchMaxDist.value) || 0;
            const use_sandhi = useSandhiCheckbox.checked;
            let script = (displayMode === 'ಅಕ್ಷರಗಳು') ? 'kannada' : 'devanagari';

            outputDiv.textContent = "Searching...";

            fetch('/api/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ target, measure, max_distance, script, use_sandhi })
            })
                .then(res => res.json())
                .then(data => {
                    if (data.matches && data.matches.length > 0) {
                        const match = data.matches[0];
                        pathPoints = match.path.map(p => ({ r: p[0], c: p[1] }));
                        cellCountSpan.textContent = pathPoints.length;
                        
                        let resultText = `Found (${data.matches.length} results). Best match dist: ${match.distance}.`;
                        resultText += `\nRaw extracted: ${match.extracted_text}`;
                        if (match.sandhi_converted_text) {
                            resultText += `\nSandhi converted: ${match.sandhi_converted_text}`;
                        }
                        
                        outputDiv.textContent = resultText;
                        drawGrid();
                    } else {
                        outputDiv.textContent = "No matches found.";
                        pathPoints = [];
                        cellCountSpan.textContent = 0;
                        drawGrid();
                    }
                })
                .catch(err => {
                    outputDiv.textContent = "Search error.";
                    console.error("Search error:", err);
                });
        });
    }

    // Bandha Pattern Functions
    function getCurrentScript() {
        return (displayMode === 'ಅಕ್ಷರಗಳು') ? 'kannada' : 'devanagari';
    }

    function getCurrentUseSandhi() {
        return useSandhiCheckbox ? useSandhiCheckbox.checked : false;
    }

    
    // Pattern Search Handler
    if (patternSearchBtn) {
        patternSearchBtn.addEventListener('click', () => {
            const target = searchInput.value.trim();
            if (!target) {
                alert("Please enter target text to search.");
                return;
            }

            const patternType = document.getElementById('patternSearchType').value;
            if (!patternType) {
                alert("Please select a pattern type for pattern search.");
                return;
            }

            const measure = searchMeasure.value;
            const max_distance = parseInt(searchMaxDist.value) || 0;
            const script = getCurrentScript();
            const use_sandhi = getCurrentUseSandhi();
            const tryAllPatterns = document.getElementById('tryAllPatterns').checked;
            const searchAllStartPositions = document.getElementById('searchAllVariants').checked;

            outputDiv.textContent = "Searching with pattern...";

            if (tryAllPatterns) {
                // Try all pattern types
                const allPatternTypes = ['horizontal_zigzag', 'vertical_zigzag', 'chess_knight', 'shreni_bandha'];
                let allResults = [];
                let completed = 0;
                
                allPatternTypes.forEach(patternType => {
                    fetch('/api/search/all_pattern_variants', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ target, pattern_type: patternType, measure, max_distance, script, use_sandhi })
                    })
                    .then(res => res.json())
                    .then(data => {
                        // Validate and filter results
                        const validResults = (Array.isArray(data) ? data : []).filter(result => 
                            result && typeof result === 'object' && 
                            typeof result.distance !== 'undefined'
                        );
                        allResults = allResults.concat(validResults);
                        completed++;
                        if (completed === allPatternTypes.length) {
                            // Sort and display all results
                            allResults.sort((a, b) => {
                                // Sort by distance first
                                if (a.distance !== b.distance) return a.distance - b.distance;
                                
                                // Sort by path length (handle undefined paths)
                                const aPathLength = a.path ? a.path.length : 0;
                                const bPathLength = b.path ? b.path.length : 0;
                                if (aPathLength !== bPathLength) return aPathLength - bPathLength;
                                
                                // Sort by position (handle undefined pattern_params)
                                const aStartRow = a.pattern_params && a.pattern_params.start_row !== undefined ? a.pattern_params.start_row : 999;
                                const bStartRow = b.pattern_params && b.pattern_params.start_row !== undefined ? b.pattern_params.start_row : 999;
                                if (aStartRow !== bStartRow) return aStartRow - bStartRow;
                                
                                const aStartCol = a.pattern_params && a.pattern_params.start_col !== undefined ? a.pattern_params.start_col : 999;
                                const bStartCol = b.pattern_params && b.pattern_params.start_col !== undefined ? b.pattern_params.start_col : 999;
                                return aStartCol - bStartCol;
                            });
                            handlePatternSearchResults(allResults, target);
                        }
                    })
                    .catch(err => {
                        console.error("Pattern search error:", err);
                        outputDiv.textContent = "Pattern search failed. See console for details.";
                    });
                });
            } else if (searchAllStartPositions) {
                // Try all starting positions for selected pattern type
                // console.log('Trying all starting positions for pattern:', patternType);
                
                const allPatternTypes = [patternType]; // Only the selected pattern
                let allResults = [];
                let completed = 0;
                
                allPatternTypes.forEach(pType => {
                    // Generate all possible starting positions and parameters
                    const startPositions = [];
                    
                    if (pType === 'shreni_bandha') {
                        // Generate all Shreni Bandha starting positions
                        for (let direction of ['up', 'down']) {
                            for (let startRow = 0; startRow < 27; startRow++) {
                                for (let startCol = 0; startCol < 27; startCol++) {
                                    startPositions.push({
                                        pattern_type: pType,
                                        pattern_params: {
                                            start_row: startRow,
                                            start_col: startCol,
                                            num_steps: target.length + 3, // Allow some extra length
                                            direction: direction
                                        }
                                    });
                                }
                            }
                        }
                    } else if (pType === 'horizontal_zigzag' || pType === 'vertical_zigzag') {
                        // Generate all starting positions for zigzag patterns
                        for (let startRow = 0; startRow < 27; startRow++) {
                            for (let startCol = 0; startCol < 27; startCol++) {
                                startPositions.push({
                                    pattern_type: pType,
                                    pattern_params: {
                                        start_row: startRow,
                                        start_col: startCol,
                                        length: target.length
                                    }
                                });
                            }
                        }
                    } else if (pType === 'chess_knight') {
                        // Generate all starting positions for chess knight
                        for (let startRow = 0; startRow < 27; startRow++) {
                            for (let startCol = 0; startCol < 27; startCol++) {
                                startPositions.push({
                                    pattern_type: pType,
                                    pattern_params: {
                                        start_row: startRow,
                                        start_col: startCol,
                                        num_jumps: target.length - 1,
                                        constraints: { random_seed: 42 }
                                    }
                                });
                            }
                        }
                    }
                    
                    // console.log(`Generated ${startPositions.length} starting positions for ${pType}`);
                    
                    // Process positions in batches to avoid overwhelming the server
                    const batchSize = 10; // Reduced from 50
                    let processed = 0;
                    
                    function processBatch() {
                        const batch = startPositions.slice(processed, processed + batchSize);
                        if (batch.length === 0) {
                            // All done for this pattern type
                            completed++;
                            if (completed === allPatternTypes.length) {
                                // Sort and display all results
                                allResults.sort((a, b) => {
                                    if (a.distance !== b.distance) return a.distance - b.distance;
                                    const aPathLength = a.path ? a.path.length : 0;
                                    const bPathLength = b.path ? b.path.length : 0;
                                    if (aPathLength !== bPathLength) return aPathLength - bPathLength;
                                    const aStartRow = a.pattern_params && a.pattern_params.start_row !== undefined ? a.pattern_params.start_row : 999;
                                    const bStartRow = b.pattern_params && b.pattern_params.start_row !== undefined ? b.pattern_params.start_row : 999;
                                    if (aStartRow !== bStartRow) return aStartRow - bStartRow;
                                    const aStartCol = a.pattern_params && a.pattern_params.start_col !== undefined ? a.pattern_params.start_col : 999;
                                    const bStartCol = b.pattern_params && b.pattern_params.start_col !== undefined ? b.pattern_params.start_col : 999;
                                    return aStartCol - bStartCol;
                                });
                                // console.log(`Final results: ${allResults.length} matches`);
                                handlePatternSearchResults({ matches: allResults }, target);
                            }
                            return;
                        }
                        
                        // Process this batch
                        let batchCompleted = 0;
                        batch.forEach(pos => {
                            const requestBody = { target, pattern_type: pos.pattern_type, pattern_params: pos.pattern_params, measure, max_distance, script, use_sandhi };
                            // console.log(`Request for position (${pos.pattern_params.start_row}, ${pos.pattern_params.start_col}):`, requestBody);
                            fetch('/api/search/bandha_pattern', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ target, pattern_type: pos.pattern_type, pattern_params: pos.pattern_params, measure, max_distance, script, use_sandhi })
                            })
                            .then(res => res.json())
                            .then(data => {
                                // console.log(`API response for position (${pos.pattern_params.start_row}, ${pos.pattern_params.start_col}):`, data);
                                if (data.matches && data.matches.length > 0) {
                                    console.log(`Found ${data.matches.length} matches!`);
                                    allResults = allResults.concat(data.matches);
                                }
                                batchCompleted++;
                                if (batchCompleted === batch.length) {
                                    processed += batchSize;
                                    setTimeout(processBatch, 100); // Increased delay from 10ms to 100ms
                                }
                            })
                            .catch(err => {
                                console.error("Pattern search error:", err);
                                batchCompleted++;
                                if (batchCompleted === batch.length) {
                                    processed += batchSize;
                                    setTimeout(processBatch, 100); // Increased delay from 10ms to 100ms
                                }
                            });
                        });
                    }
                    
                    processBatch();
                });
            } else {
                // Search with specific UI parameters
                // console.log('Searching with specific UI parameters for pattern:', patternType);
                
                // Get parameters from UI
                let patternParams = {};
                
                if (patternType === 'horizontal_zigzag') {
                    const hzStartRow = document.getElementById('hzStartRow');
                    const hzStartCol = document.getElementById('hzStartCol');
                    const hzLength = document.getElementById('hzLength');
                    
                    if (!hzStartRow || !hzStartCol || !hzLength) {
                        alert("Horizontal Zigzag parameters not available. Please select the pattern type first.");
                        return;
                    }
                    
                    patternParams = {
                        start_row: parseInt(hzStartRow.value),
                        start_col: parseInt(hzStartCol.value),
                        length: parseInt(hzLength.value)
                    };
                } else if (patternType === 'vertical_zigzag') {
                    const vzStartRow = document.getElementById('vzStartRow');
                    const vzStartCol = document.getElementById('vzStartCol');
                    const vzLength = document.getElementById('vzLength');
                    
                    if (!vzStartRow || !vzStartCol || !vzLength) {
                        alert("Vertical Zigzag parameters not available. Please select the pattern type first.");
                        return;
                    }
                    
                    patternParams = {
                        start_row: parseInt(vzStartRow.value),
                        start_col: parseInt(vzStartCol.value),
                        length: parseInt(vzLength.value)
                    };
                } else if (patternType === 'chess_knight') {
                    const knightStartRow = document.getElementById('knightStartRow');
                    const knightStartCol = document.getElementById('knightStartCol');
                    const knightJumps = document.getElementById('knightJumps');
                    const knightAvoidEdges = document.getElementById('knightAvoidEdges');
                    const knightSeed = document.getElementById('knightSeed');
                    
                    if (!knightStartRow || !knightStartCol || !knightJumps) {
                        alert("Chess Knight parameters not available. Please select the pattern type first.");
                        return;
                    }
                    
                    const constraints = {};
                    if (knightAvoidEdges.checked) {
                        constraints.avoid_edges = true;
                    }
                    const seedValue = knightSeed.value;
                    if (seedValue) {
                        constraints.random_seed = parseInt(seedValue);
                    }
                    const preferredDirections = [];
                    document.querySelectorAll('input[name="knightDir"]:checked').forEach(checkbox => {
                        preferredDirections.push(checkbox.value);
                    });
                    if (preferredDirections.length > 0) {
                        constraints.preferred_directions = preferredDirections;
                    }
                    
                    patternParams = {
                        start_row: parseInt(knightStartRow.value),
                        start_col: parseInt(knightStartCol.value),
                        num_jumps: parseInt(knightJumps.value),
                        constraints
                    };
                } else if (patternType === 'shreni_bandha') {
                    const shreniStartRow = document.getElementById('shreniStartRow');
                    const shreniStartCol = document.getElementById('shreniStartCol');
                    const shreniSteps = document.getElementById('shreniSteps');
                    const shreniDirection = document.querySelector('input[name="shreniDirection"]:checked');
                    
                    if (!shreniStartRow || !shreniStartCol || !shreniSteps || !shreniDirection) {
                        alert("Shreni Bandha parameters not available. Please select the pattern type first.");
                        return;
                    }
                    
                    patternParams = {
                        start_row: parseInt(shreniStartRow.value),
                        start_col: parseInt(shreniStartCol.value),
                        num_steps: parseInt(shreniSteps.value),
                        direction: shreniDirection.value
                    };
                }

                // console.log('Pattern params:', patternParams);
                fetch('/api/search/bandha_pattern', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ target, pattern_type: patternType, pattern_params: patternParams, measure, max_distance, script, use_sandhi })
                })
                    .then(res => res.json())
                    .then(data => {
                        // console.log('Response from bandha_pattern:', data);
                        handlePatternSearchResults(data, target);
                    })
                    .catch(err => {
                        console.error("Pattern search error:", err);
                        outputDiv.textContent = "Pattern search failed. See console for details.";
                    });
            }
        });
    }

    function handlePatternSearchResults(data, target) {
        if (data.matches && data.matches.length > 0) {
            const match = data.matches[0];
            pathPoints = match.path.map(p => ({ r: p[0], c: p[1] }));
            cellCountSpan.textContent = pathPoints.length;
            
            let resultText = `Pattern search found (${data.matches.length} results). Best match dist: ${match.distance}.`;
            resultText += `\nPattern: ${match.pattern_type || 'Unknown'}`;
            resultText += `\nRaw extracted: ${match.extracted_text}`;
            if (match.sandhi_converted_text) {
                resultText += `\nSandhi converted: ${match.sandhi_converted_text}`;
            }
            
            outputDiv.textContent = resultText;
            drawGrid();
        } else {
            outputDiv.textContent = "No pattern matches found.";
            pathPoints = [];
            cellCountSpan.textContent = 0;
            drawGrid();
        }
    }
});
