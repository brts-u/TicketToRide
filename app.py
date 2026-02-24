from flask import Flask, render_template, session, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid
from datetime import datetime
from board_state import *
from game_setup import *

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
socketio = SocketIO(app, cors_allowed_origins="*")

# In-memory storage for lobbies
lobbies = {}
# Track which lobby each player is in
player_lobbies = {}

@app.route('/')
def index():
    return render_template('index.html')

# ============================== LOBBY SYSTEM ==============================

@app.route('/lobby/<lobby_id>')
def lobby_room(lobby_id):
    # Render the same template - JavaScript will handle joining
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    # Generate a unique player ID if they don't have one
    if 'player_id' not in session:
        session['player_id'] = str(uuid.uuid4())
    
    # Send current lobbies to the newly connected player
    lobby_list = get_lobby_list()
    emit('lobby_list_update', {'lobbies': lobby_list})

@socketio.on('disconnect')
def handle_disconnect():
    player_id = session.get('player_id')
    if player_id in player_lobbies:
        lobby_id = player_lobbies[player_id]
        leave_lobby_helper(player_id, lobby_id)

@socketio.on('set_username')
def handle_set_username(data):
    session['username'] = data['username']
    emit('username_set', {'username': data['username']})

@socketio.on('create_lobby')
def handle_create_lobby(data):
    player_id = session.get('player_id')
    username = session.get('username', 'Anonymous')
    
    # Generate unique lobby ID
    lobby_id = str(uuid.uuid4())[:8].upper()
    
    # Create lobby
    lobbies[lobby_id] = {
        'id': lobby_id,
        'name': data.get('name', f"{username}'s Game"),
        'host': player_id,
        'players': [{
            'id': player_id,
            'username': username
        }],
        'max_players': int(data.get('max_players', 4)),
        'created_at': datetime.now().isoformat(),
        'started': False
    }
    
    # Track player's lobby
    player_lobbies[player_id] = lobby_id
    
    # Join the room
    join_room(lobby_id)
    
    # Notify the creator
    emit('lobby_joined', {
        'lobby': lobbies[lobby_id],
        'player_id': player_id
    })
    
    # Broadcast updated lobby list to all clients
    broadcast_lobby_list()

@socketio.on('join_lobby')
def handle_join_lobby(data):
    player_id = session.get('player_id')
    username = session.get('username', 'Anonymous')
    lobby_id = data['lobby_id']
    
    if lobby_id not in lobbies:
        emit('error', {'message': 'Lobby not found'})
        return
    
    lobby = lobbies[lobby_id]
    
    # Check if lobby is full
    if len(lobby['players']) >= lobby['max_players']:
        emit('error', {'message': 'Lobby is full'})
        return
    
    # Check if game already started
    if lobby['started']:
        emit('error', {'message': 'Game already started'})
        return
    
    # Check if player is already in a lobby
    if player_id in player_lobbies:
        emit('error', {'message': 'You are already in a lobby'})
        return
    
    # Add player to lobby
    lobby['players'].append({
        'id': player_id,
        'username': username
    })
    
    player_lobbies[player_id] = lobby_id
    join_room(lobby_id)
    
    # Notify the player
    emit('lobby_joined', {
        'lobby': lobby,
        'player_id': player_id
    })
    
    # Notify others in the lobby
    emit('player_joined', {
        'player': {'id': player_id, 'username': username},
        'lobby': lobby
    }, room=lobby_id, include_self=False)
    
    # Broadcast updated lobby list
    broadcast_lobby_list()

@socketio.on('leave_lobby')
def handle_leave_lobby():
    player_id = session.get('player_id')
    
    if player_id not in player_lobbies:
        return
    
    lobby_id = player_lobbies[player_id]
    leave_lobby_helper(player_id, lobby_id)

@socketio.on('start_game')
def handle_start_game(data):
    player_id = session.get('player_id')
    lobby_id = data.get('lobby_id')
    
    if lobby_id not in lobbies:
        emit('error', {'message': 'Lobby not found'})
        return
    
    lobby = lobbies[lobby_id]
    
    # Check if player is the host
    if lobby['host'] != player_id:
        emit('error', {'message': 'Only the host can start the game'})
        return
    
    # Mark game as started
    lobby['started'] = True
    
    # Notify all players in the lobby
    emit('game_started', {'lobby': lobby}, room=lobby_id)
    
    # Update lobby list
    broadcast_lobby_list()

@socketio.on('get_lobby_list')
def handle_get_lobby_list():
    lobby_list = get_lobby_list()
    emit('lobby_list_update', {'lobbies': lobby_list})

def leave_lobby_helper(player_id, lobby_id):
    if lobby_id not in lobbies:
        return
    
    lobby = lobbies[lobby_id]
    
    # Remove player from lobby
    lobby['players'] = [p for p in lobby['players'] if p['id'] != player_id]
    
    # Remove from tracking
    del player_lobbies[player_id]
    leave_room(lobby_id)
    
    # If lobby is empty, delete it
    if len(lobby['players']) == 0:
        del lobbies[lobby_id]
    else:
        # If host left, assign new host
        if lobby['host'] == player_id:
            lobby['host'] = lobby['players'][0]['id']
            emit('new_host', {'host_id': lobby['host']}, room=lobby_id)
        
        # Notify others in the lobby
        emit('player_left', {
            'player_id': player_id,
            'lobby': lobby
        }, room=lobby_id)
    
    # Notify the player who left
    emit('left_lobby')
    
    # Broadcast updated lobby list
    broadcast_lobby_list()

def get_lobby_list():
    """Get list of available lobbies (not started)"""
    return [
        {
            'id': lobby['id'],
            'name': lobby['name'],
            'host': lobby['players'][0]['username'] if lobby['players'] else 'Unknown',
            'player_count': len(lobby['players']),
            'max_players': lobby['max_players'],
            'started': lobby['started']
        }
        for lobby in lobbies.values()
        if not lobby['started']  # Only show lobbies that haven't started
    ]

def broadcast_lobby_list():
    """Broadcast updated lobby list to all connected clients"""
    lobby_list = get_lobby_list()
    socketio.emit('lobby_list_update', {'lobbies': lobby_list})

# ============================== GAME API ==============================

game_state: GameState | None = None

# In app.py
@app.route('/game/<lobby_id>')
def game(lobby_id):
    return render_template('ticket-to-ride.html', lobby_id=lobby_id)

@app.route('/api/ping', methods=['GET'])
def ping():
    return jsonify({'reply': 'pong'})

@app.route('/api/new-board', methods = ['GET'])
def new_board():
    cities_file = "static/europe/cities.txt"
    connections_file = "static/europe/connections.txt"
    tickets_file = "static/europe/tickets.txt"
    player_info = [("Bartek", PlayerColor.RED)]  # , ("Alicja", PlayerColor.BLUE)]
    global game_state
    game_state = setup_game(cities_file, connections_file, tickets_file, player_info)

    with open('static/europe/svg_elements.json', 'r') as f:
        return f.read(), 200, {'Content-Type': 'application/json'}

@app.route('/api/get-cards', methods=['GET'])
def get_cards():
    if not game_state:
        return jsonify({'error': -1, 'message': "Game doesn't exist"})
    cards = [str(card) for card in game_state.face_up_cards]
    return jsonify(cards)

@app.route('/api/get-initial-tickets', methods=['POST']) # TODO: ZWRACA NONE TYPE, also zmien na GET
def get_initial_tickets():
    if not game_state:
        return jsonify({'error': -1, 'message': "Game doesn't exist"})
    data = request.get_json()
    player_name = data['player']
    player = game_state.players[player_name]
    tickets = game_state.get_initial_tickets(player)
    return jsonify(tickets)

@app.route('/api/handle-click', methods=['POST'])
def handle_click():
    # Your Python code here
    data = request.get_json()

    # Example: Do something with the data
    result = {
        'message': 'Python code executed!',
        'received': data
    }

    return jsonify(result)



if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
