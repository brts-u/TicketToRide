// Initialize Socket.IO connection
const socket = io();

// State
let currentUsername = '';
let currentLobby = null;
let currentPlayerId = null;
let pendingLobbyId = null; // Store lobby ID to join after username setup

// Check URL for lobby ID on page load
const pathParts = window.location.pathname.split('/');
if (pathParts[1] === 'lobby' && pathParts[2]) {
    pendingLobbyId = pathParts[2];
}

// Screen elements
const usernameScreen = document.getElementById('username-screen');
const lobbyBrowserScreen = document.getElementById('lobby-browser-screen');
const lobbyRoomScreen = document.getElementById('lobby-room-screen');
const gameScreen = document.getElementById('game-screen');

// Username setup
const usernameInput = document.getElementById('username-input');
const setUsernameBtn = document.getElementById('set-username-btn');

// Lobby browser
const createLobbyBtn = document.getElementById('create-lobby-btn');
const refreshLobbiesBtn = document.getElementById('refresh-lobbies-btn');
const lobbyList = document.getElementById('lobby-list');
const currentUsernameSpan = document.getElementById('current-username');

// Create lobby modal
const createLobbyModal = document.getElementById('create-lobby-modal');
const closeCreateModal = document.getElementById('close-create-modal');
const cancelCreateBtn = document.getElementById('cancel-create-btn');
const confirmCreateBtn = document.getElementById('confirm-create-btn');
const lobbyNameInput = document.getElementById('lobby-name');
const maxPlayersSelect = document.getElementById('max-players');

// Lobby room
const lobbyRoomName = document.getElementById('lobby-room-name');
const lobbyCode = document.getElementById('lobby-code');
const lobbyPlayerCount = document.getElementById('lobby-player-count');
const playersList = document.getElementById('players-list');
const copyLinkBtn = document.getElementById('copy-link-btn');
const leaveLobbyBtn = document.getElementById('leave-lobby-btn');
const startGameBtn = document.getElementById('start-game-btn');
const waitingMessage = document.getElementById('waiting-message');

// Game
const backToLobbyBtn = document.getElementById('back-to-lobby-btn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Auto-focus username input
    usernameInput.focus();
    
    // Enable Enter key for username
    usernameInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            setUsername();
        }
    });
});

// Username setup
setUsernameBtn.addEventListener('click', setUsername);

function setUsername() {
    const username = usernameInput.value.trim();
    if (username.length < 2) {
        showNotification('Username must be at least 2 characters', 'error');
        return;
    }
    
    currentUsername = username;
    socket.emit('set_username', { username });
}

// Socket.IO event handlers
socket.on('username_set', (data) => {
    currentUsernameSpan.textContent = data.username;
    switchScreen(lobbyBrowserScreen);
    
    // If URL contains lobby ID, auto-join after username setup
    if (pendingLobbyId) {
        socket.emit('join_lobby', { lobby_id: pendingLobbyId });
        pendingLobbyId = null; // Clear after attempting to join
    }
});

socket.on('lobby_list_update', (data) => {
    renderLobbyList(data.lobbies);
});

socket.on('lobby_created', (data) => {
    closeModal(createLobbyModal);
    showNotification('Lobby created successfully!', 'success');
});

socket.on('lobby_joined', (data) => {
    currentLobby = data.lobby;
    currentPlayerId = data.player_id;
    renderLobbyRoom(data.lobby);
    switchScreen(lobbyRoomScreen);
    
    // Update URL to reflect lobby ID
    window.history.pushState({}, '', `/lobby/${data.lobby.id}`);
});

socket.on('player_joined', (data) => {
    currentLobby = data.lobby;
    renderLobbyRoom(data.lobby);
    showNotification(`${data.player.username} joined the lobby`, 'success');
});

socket.on('player_left', (data) => {
    currentLobby = data.lobby;
    renderLobbyRoom(data.lobby);
    showNotification('A player left the lobby', 'error');
});

socket.on('new_host', (data) => {
    if (data.host_id === currentPlayerId) {
        showNotification('You are now the host!', 'success');
    }
});

socket.on('left_lobby', () => {
    currentLobby = null;
    switchScreen(lobbyBrowserScreen);
    showNotification('Left the lobby', 'success');
    
    // Reset URL to home
    window.history.pushState({}, '', '/');
});

socket.on('game_started', (data) => {
    window.location.href = `/game/${data.lobby.id}`;
});

socket.on('error', (data) => {
    showNotification(data.message, 'error');
});

// Lobby browser actions
createLobbyBtn.addEventListener('click', () => {
    openModal(createLobbyModal);
});

refreshLobbiesBtn.addEventListener('click', () => {
    socket.emit('get_lobby_list');
    showNotification('Refreshing lobbies...', 'success');
});

// Modal actions
closeCreateModal.addEventListener('click', () => {
    closeModal(createLobbyModal);
});

cancelCreateBtn.addEventListener('click', () => {
    closeModal(createLobbyModal);
});

confirmCreateBtn.addEventListener('click', () => {
    const name = lobbyNameInput.value.trim() || `${currentUsername}'s Game`;
    const maxPlayers = maxPlayersSelect.value;
    
    socket.emit('create_lobby', {
        name,
        max_players: maxPlayers
    });
});

// Lobby room actions
copyLinkBtn.addEventListener('click', () => {
    if (currentLobby) {
        const lobbyUrl = `${window.location.origin}/lobby/${currentLobby.id}`;
        navigator.clipboard.writeText(lobbyUrl).then(() => {
            showNotification('Lobby link copied to clipboard!', 'success');
        }).catch(() => {
            // Fallback for older browsers
            showNotification(`Share this link: ${lobbyUrl}`, 'success');
        });
    }
});

leaveLobbyBtn.addEventListener('click', () => {
    socket.emit('leave_lobby');
});

startGameBtn.addEventListener('click', () => {
    if (currentLobby) {
        socket.emit('start_game', { lobby_id: currentLobby.id });
    }
});

backToLobbyBtn.addEventListener('click', () => {
    // In a real game, you'd handle this differently
    // For demo purposes, we'll go back to lobby browser
    socket.emit('leave_lobby');
    switchScreen(lobbyBrowserScreen);
    socket.emit('get_lobby_list');
    
    // Reset URL to home
    window.history.pushState({}, '', '/');
});

// Render functions
function renderLobbyList(lobbies) {
    if (lobbies.length === 0) {
        lobbyList.innerHTML = `
            <div class="empty-state">
                <p>No lobbies available. Create one to get started!</p>
            </div>
        `;
        return;
    }
    
    lobbyList.innerHTML = lobbies.map(lobby => `
        <div class="lobby-item">
            <div class="lobby-info-section">
                <div class="lobby-name">${escapeHtml(lobby.name)}</div>
                <div class="lobby-meta">
                    <span>🎮 Host: ${escapeHtml(lobby.host)}</span>
                    <span>👥 ${lobby.player_count}/${lobby.max_players}</span>
                    <span>🆔 ${lobby.id}</span>
                </div>
            </div>
            <div class="lobby-actions">
                ${lobby.player_count < lobby.max_players ? 
                    `<button class="btn btn-primary join-lobby-btn" data-lobby-id="${lobby.id}">Join</button>` :
                    `<span class="badge badge-danger">Full</span>`
                }
            </div>
        </div>
    `).join('');
    
    // Add event listeners to join buttons
    document.querySelectorAll('.join-lobby-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const lobbyId = e.target.getAttribute('data-lobby-id');
            socket.emit('join_lobby', { lobby_id: lobbyId });
        });
    });
}

function renderLobbyRoom(lobby) {
    lobbyRoomName.textContent = lobby.name;
    lobbyCode.textContent = `Lobby Code: ${lobby.id}`;
    lobbyPlayerCount.textContent = `Players: ${lobby.players.length}/${lobby.max_players}`;
    
    // Render players
    playersList.innerHTML = lobby.players.map(player => `
        <div class="player-card ${player.id === lobby.host ? 'is-host' : ''}">
            <div class="player-name">${escapeHtml(player.username)}</div>
        </div>
    `).join('');
    
    // Show/hide start button based on if current player is host
    if (lobby.host === currentPlayerId) {
        startGameBtn.style.display = 'block';
        waitingMessage.style.display = 'none';
    } else {
        startGameBtn.style.display = 'none';
        waitingMessage.style.display = 'block';
    }
}

// Utility functions
function switchScreen(screen) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    screen.classList.add('active');
}

function openModal(modal) {
    modal.classList.add('active');
}

function closeModal(modal) {
    modal.classList.remove('active');
    // Reset form inputs
    lobbyNameInput.value = '';
    maxPlayersSelect.value = '4';
}

function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type} show`;
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Close modals when clicking outside
window.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        closeModal(e.target);
    }
});

// Handle browser back/forward buttons
window.addEventListener('popstate', (e) => {
    const pathParts = window.location.pathname.split('/');
    
    if (pathParts[1] === 'lobby' && pathParts[2]) {
        // User navigated back to a lobby URL
        const lobbyId = pathParts[2];
        if (currentLobby && currentLobby.id === lobbyId) {
            // Already in this lobby, just show the screen
            switchScreen(lobbyRoomScreen);
        } else {
            // Try to join this lobby
            socket.emit('join_lobby', { lobby_id: lobbyId });
        }
    } else {
        // User navigated back to home
        if (currentLobby) {
            socket.emit('leave_lobby');
        }
        switchScreen(lobbyBrowserScreen);
    }
});
