let board = null;
let two = null;
let SCALE = 0.6;
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
}

function pointsToAnchors(points) {
  return points.map(([x, y]) => new Two.Anchor(x/SCALE, y/SCALE));
}

function drawElements(elements) {
    elements.forEach(element => {
        if (element.type === 'Path') {
            console.log('Drawing path:', element.id);
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
            console.log('Drawing ellipse:', element.id);
            const ellipse = two.makeEllipse(element.attributes.centre[0] / SCALE, element.attributes.centre[1] / SCALE, element.attributes.radius[0] / SCALE, element.attributes.radius[1] / SCALE);
            ellipse.fill = element.attributes.fill;
            ellipse.stroke = element.attributes.stroke;
            ellipse.linewidth = element.attributes.stroke_width / (2*SCALE);
            two.update();
            ellipse._renderer.elem.addEventListener('click', ping);
        }
    });
}
