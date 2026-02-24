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
let two = null;
let game_id = '-1';
createBoard();


// ========= FUNCTIONS ===========
async function ping() {
    try {
        const response = await fetch('/api/ping', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        const data = await response.json();
        console.log('Response from server:', data);

        alert(data.reply);
    } catch (error) {
        console.error('Error pinging server:', error);
    }
}

async function createBoard() {
    try {
        const response = await fetch('/api/new-board', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        board = await response.json();
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
    } catch (error) {
        console.error('Error creating new board:', error);
    }
    getCards();
    getInitalTickets('Bartek');
}

async function getCards() {
    try {
        const response = await fetch('/api/get-cards', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        cards = await response.json();
        console.log('Cards:', cards)
        card_rand = two.makeRectangle(1550, Y_BOARD_SHIFT + CARD_HEIGHT/2, CARD_WIDTH, CARD_HEIGHT)
        card_rand.fill = '#000000'
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
    } catch (error) {
        console.error('Error getting cards:', error)
    }
}

async function getInitalTickets(player){
    try {
        const response = await fetch('/api/get-initial-tickets', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({player: player})
        })
        tickets = await response.json()
        console.log('Tickets:', tickets)
    } catch (error) {
        console.error('Error getting tickets:', error)
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
            ellipse._renderer.elem.addEventListener('click', ping);
        }
    });
}