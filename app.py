from flask import Flask, render_template, request, jsonify
from board_state import *
from game_setup import *

app = Flask(__name__)
game_state: GameState | None = None
@app.route('/')
def index():
    return render_template('index.html')

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
    app.run(debug=True)