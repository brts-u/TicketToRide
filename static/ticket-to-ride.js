// ======= CONFIGURATION =======
const SCALE = 0.6;
const X_SHIFT = 30.0;
const Y_SHIFT = 20.0;

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
let board = null;
let two = null;
createBoard();

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
    getCards()
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
        card0 = two.makeRectangle(1300, 120, 240, 120)
        card0.fill = color_map[cards[0]]
        card1 = two.makeRectangle(1300, 270, 240, 120)
        card1.fill = color_map[cards[1]]
        card2 = two.makeRectangle(1300, 420, 240, 120)
        card2.fill = color_map[cards[2]]
        card3 = two.makeRectangle(1300, 570, 240, 120)
        card3.fill = color_map[cards[3]]
        card4 = two.makeRectangle(1300, 720, 240, 120)
        card4.fill = color_map[cards[4]]
        two.update();
    } catch (error) {
        console.error('Error getting cards:', error)
    }
}

function pointsToAnchors(points) {
  return points.map(([x, y]) => new Two.Anchor(X_SHIFT + x/SCALE, Y_SHIFT + y/SCALE));
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
            const ellipse = two.makeEllipse(X_SHIFT + element.attributes.centre[0] / SCALE, Y_SHIFT + element.attributes.centre[1] / SCALE, element.attributes.radius[0] / SCALE, element.attributes.radius[1] / SCALE);
            ellipse.fill = element.attributes.fill;
            ellipse.stroke = element.attributes.stroke;
            ellipse.linewidth = element.attributes.stroke_width / (2*SCALE);
            two.update();
            ellipse._renderer.elem.addEventListener('click', ping);
        }
    });
}