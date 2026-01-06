from svgelements import *
import json

def subpath_vertices(subpath):
    """Return ordered vertices of a subpath consisting of straight lines."""
    verts = []
    start_point = None

    for seg in subpath:
        # record start of contour
        if isinstance(seg, Move):
            start_point = (seg.end.x, seg.end.y)
            verts.append(start_point)

        # straight line segment
        elif isinstance(seg, Line):
            p = (seg.end.x, seg.end.y)
            # avoid duplicate vertex
            if not verts or verts[-1] != p:
                verts.append(p)

        # explicit close → ensure ring closure
        elif isinstance(seg, Close):
            if start_point and verts and verts[-1] != start_point:
                verts.append(start_point)

    # implicit closure — close if nearly closed
    if len(verts) > 2 and verts[0] != verts[-1]:
        verts.append(verts[0])

    return verts

def signed_area(ring):
    return -sum(
        (x2 - x1) * (y2 + y1)
        for (x1, y1), (x2, y2) in zip(ring, ring[1:])
    )

def extract_svg_elements(svg_path):
    elements_data = []

    drawing = SVG.parse(svg_path)
    bbox = drawing.bbox()

    for element in drawing.elements():
        if type(element) not in [Ellipse, Path]:
            continue
        bodies = []
        holes = []
        attributes = {
            'fill': str(element.fill),
            'stroke': str(element.stroke),
            'stroke_width': float(element.stroke_width)
        }
        if isinstance(element, Ellipse):
            attributes['centre'] = (element.cx, element.cy)
            attributes['radius'] = (element.rx, element.ry)
        elif isinstance(element, Path):
            for sub in element.as_subpaths():
                vertices = subpath_vertices(sub)
                # ignore degenerate paths
                if len(vertices) < 4:  # 3 + closing point
                    continue
                area = signed_area(vertices)

                if area > 0:
                    bodies.append(vertices)
                else:
                    holes.append(vertices)

        element_info = {
            'type': type(element).__name__,
            'id': element.id,
            'bodies': bodies,
            'holes': holes,
            'attributes': attributes
        }
        elements_data.append(element_info)
    return elements_data, bbox

def draw_svg_elements(elements, bbox):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    for element in elements:
        vertices = element['vertices']
        if element['type'] == 'Ellipse':
            centre = element['attributes']['centre']
            centre = (centre[0], bbox[3] - centre[1])
            radius = element['attributes']['radius']
            ellipse = plt.Circle(centre, radius[0], fill=False, edgecolor=element['attributes']['stroke'])
            ax.add_artist(ellipse)
        elif element['type'] == 'Path':
            xs, ys = zip(*vertices)
            ys = [bbox[3] - y for y in ys]
            ax.plot(xs, ys, color=element['attributes']['stroke'])
    ax.set_aspect('equal')
    plt.show()

if __name__ == '__main__':
    svg_path = 'static/europe/svg/board.svg'
    elements, bbox = extract_svg_elements(svg_path)
    data = {
        'bbox': bbox,
        'elements': elements,
    }

    with open('static/europe/svg_elements.json', 'w') as f:
        json.dump(data, f, indent=1)