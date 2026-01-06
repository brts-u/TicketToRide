from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/ping', methods=['GET'])
def ping():
    return jsonify({'reply': 'pong'})

@app.route('/api/new-board', methods = ['GET'])
def new_board():
    with open('./static/svg_elements.json', 'r') as f:
        return f.read(), 200, {'Content-Type': 'application/json'}

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