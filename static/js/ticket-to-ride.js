// ======= CONFIGURATION =======
const SCALE = 0.6;
const X_BOARD_SHIFT = 280.0;
const Y_BOARD_SHIFT = 20.0;
const CARD_HEIGHT = 64.333/SCALE;
const CARD_WIDTH = 130/SCALE;

// ========== SETUP ============
const color_map = {
    'CardColor.RED': '#D5291A',
    'CardColor.ORANGE': '#ee8816',
    'CardColor.YELLOW': '#fbe82b',
    'CardColor.GREEN': '#9dc131',
    'CardColor.BLUE': '#029ff6',
    'CardColor.PINK': '#c991c4',
    'CardColor.BLACK': '#2e3144',
    'CardColor.WHITE': '#e6e7f1',
    'CardColor.JOKER': '#9c9c9a'
};

// Extract lobby_id from the URL path  (/game/<lobby_id>)
const lobby_id = window.location.pathname.split('/').pop();

let two = null;

const socket = io();

socket.on('connect', () => {
    // Re-join the socket room for this lobby so the broadcast reaches us.
    // The server already placed every player into the room before redirecting,
    // but a fresh page-load gets a new socket connection, so we rejoin here.
    socket.emit('rejoin_game', { lobby_id });
});

socket.on('game_started', (data) => {
    // data.board contains the full svg_elements JSON (same shape as before)
    createBoard(data.board);
    getCards();
    getInitialTickets('Bartek'); // TODO: replace with actual username
});

// ========= FUNCTIONS ===========

/**
 * Initialise the Two.js canvas and draw the board.
 * @param {Object} board  - Parsed JSON from svg_elements.json
 */
function createBoard(board) {
    console.log('Board bbox', board.bbox);
    const params = {
        type: Two.Types.svg,
        width: (board.bbox[2] - board.bbox[0]) / SCALE,
        height: (board.bbox[3] - board.bbox[1]) / SCALE,
        fullscreen: true
    };
    two = new Two(params).appendTo(document.body);
    drawElements(board.elements);
    two.update();
}

async function getGameState() {
    try {
        const response = await fetch(`/api/get-game-state?game_id=${game_id}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        const data = await response.json();
        console.log('Game state:', data);
        drawCards(data.cards);
        drawTickets(data.tickets);
    } catch (error) {
        console.error('Error fetching game state:', error);
    }
}

function pointsToAnchors(points) {
  return points.map(([x, y]) => new Two.Anchor(X_BOARD_SHIFT + x/SCALE, Y_BOARD_SHIFT + y/SCALE));
}
function drawElements(elements) {
    elements.forEach(element => {
        if (element.type === 'Path') {
            let vertices = [];
            element.bodies.forEach(body => {
                vertices = vertices.concat(pointsToAnchors(body));
            });
            element.holes.forEach(hole => {
                vertices = vertices.concat(pointsToAnchors(hole));
            });
            const path = two.makePath(vertices);
            path.closed = true;
            if (element.attributes.fill) path.fill = element.attributes.fill;
            if (element.attributes.stroke) path.stroke = element.attributes.stroke;
            if (element.attributes.stroke_width) path.linewidth = element.attributes.stroke_width / (2 * SCALE);
        } else if (element.type === 'Ellipse') {
            const ellipse = two.makeEllipse(X_BOARD_SHIFT + element.attributes.centre[0] / SCALE, Y_BOARD_SHIFT + element.attributes.centre[1] / SCALE, element.attributes.radius[0] / SCALE, element.attributes.radius[1] / SCALE);
            ellipse.fill = element.attributes.fill;
            ellipse.stroke = element.attributes.stroke;
            ellipse.linewidth = element.attributes.stroke_width / (2*SCALE);
            two.update();
        }
    });
}

function drawCards(cards) {
    if (cards.length !== 5) {
        console.error('Expected 5 cards, got', cards.length);
        return -1;
    }
    card0 = two.makeRectangle(1550, 2 * Y_BOARD_SHIFT + 3 * CARD_HEIGHT/2, CARD_WIDTH, CARD_HEIGHT)
    card0.fill = color_map[cards[0]]
    card1 = two.makeRectangle(1550, 3 * Y_BOARD_SHIFT + 5 * CARD_HEIGHT/2, CARD_WIDTH, CARD_HEIGHT)
    card1.fill = color_map[cards[1]]
    card2 = two.makeRectangle(1550, 4 * Y_BOARD_SHIFT + 7 * CARD_HEIGHT/2, CARD_WIDTH, CARD_HEIGHT)
    card2.fill = color_map[cards[2]]
    card3 = two.makeRectangle(1550, 5 * Y_BOARD_SHIFT + 9 * CARD_HEIGHT/2, CARD_WIDTH, CARD_HEIGHT)
    card3.fill = color_map[cards[3]]
    card4 = two.makeRectangle(1550, 6 * Y_BOARD_SHIFT + 11 * CARD_HEIGHT/2, CARD_WIDTH, CARD_HEIGHT)
    card4.fill = color_map[cards[4]]
    two.update();
}

function drawTickets(tickets) {
    tickets.forEach((ticket, index) => {
        const x = 1550;
        const y = 2 * Y_BOARD_SHIFT + (index + 1) * 2 * CARD_HEIGHT;
        const line = two.makeLine(x - CARD_WIDTH/2, y - CARD_HEIGHT/2, x + CARD_WIDTH/2, y + CARD_HEIGHT/2);
        line.stroke = '#000000';
        line.linewidth = 2;
        const text = two.makeText(`${ticket.start} -> ${ticket.end} (${ticket.points} pts)`, x, y);
        text.size = 14;
        text.family = 'Arial';
        text.fill = '#000000';
    });
    two.update();
}