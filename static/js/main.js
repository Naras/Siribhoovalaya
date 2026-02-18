
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
                    } else if (displayMode === 'ಅಕ್ಷರಗಳು'){
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
                outputDiv.textContent = data.text;
            })
            .catch(err => {
                outputDiv.textContent = "Error extracting text.";
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
                text: outputDiv.textContent
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

                    cellCountSpan.textContent = pathPoints.length;
                    drawGrid();
                })
                .catch(err => console.error("Load error:", err));
        });
    }

    // Go Button Logic
    const formulaInput = document.getElementById('bandhaFormula');
    const generateBtn = document.getElementById('generateBandhaBtn');

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
            else script = 'devanagari'; console.log("Default script for generation:", script);
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
                    outputDiv.textContent = data.text;
                })
                .catch(err => {
                    outputDiv.textContent = "Error generating bandha.";
                    console.error("Fetch error:", err);
                });
        });
    } else {
        console.error("Generate button not found!");
    }
});
