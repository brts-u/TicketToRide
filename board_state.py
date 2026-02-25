from __future__ import annotations
from typing import Dict, Set, TYPE_CHECKING
from enum import Enum
import random
import warnings

if TYPE_CHECKING:
    from game_setup import Player, Station

class CardColor(Enum):
    RED = 'red'
    ORANGE = 'orange'
    YELLOW = 'yellow'
    GREEN = 'green'
    BLUE = 'blue'
    PINK = 'pink'
    BLACK = 'black'
    WHITE = 'white'
    JOKER = 'joker'
    def __repr__(self):
        return self.name
    @classmethod
    def random(cls):
        return random.choices(list(cls), weights=(6,6,6,6,6,6,6,6,7), k=1)[0]

EDGE_SCORES: Dict[int, int] = {
    1: 1,
    2: 2,
    3: 4,
    4: 7,
    6: 15,
    8: 21
}

class Node:
    def __init__(self, name):
        self.name: str = name
        self.edges: Set[Edge] = set()
        self.occupied_by: Station | None = None

class Edge:
    def __init__(self, node1: Node, node2: Node, length: int, /, tunnel: bool = False):
        self.node1: Node = node1
        self.node2: Node = node2
        self.length: int = length
        self.score: int = EDGE_SCORES[length]
        self.tunnel: bool = tunnel
        self.occupied_by: Player | None = None

class ColoredEdge(Edge):
    def __init__(self, node1: Node, node2: Node, length: int, color: CardColor, /, tunnel = False):
        super().__init__(node1, node2, length, tunnel=tunnel)
        self.color: CardColor = color

class FerryEdge(Edge):
    def __init__(self, node1: Node, node2: Node, length: int, joker_cost: int):
        super().__init__(node1, node2, length, tunnel = False)
        self.joker_cost: int = joker_cost

class Graph:
    def __init__(self):
        self.nodes = {}
        self.edges = {}

    def add_node(self, name: str) -> Node:
        if name not in self.nodes:
            self.nodes[name] = Node(name)
        return self.nodes[name]

    def add_edge(self, node1_name: str, node2_name: str, /, edge: Edge) -> None:
        node1 = self.add_node(node1_name)
        node2 = self.add_node(node2_name)
        # Replace placeholder nodes in the edge with the real graph nodes
        edge.node1 = node1
        edge.node2 = node2
        node1.edges.add(edge)
        node2.edges.add(edge)
        self.edges[f"{node1_name} {node2_name}"] = edge

    def get_edge(self, node1_name: str, node2_name: str) -> Edge:
        return self.edges.get(f"{node1_name} {node2_name}") or self.edges.get(f"{node2_name} {node1_name}")

    def get_node(self, name: str) -> Node:
        return self.nodes.get(name)

def parse_graph(cities_file: str, connections_file: str) -> Graph:
    with open(cities_file, "r") as f:
        cities = f.read().splitlines()
    with open(connections_file, "r") as f:
        connections = f.read().splitlines()

    edges_list = []
    for connection in connections:
        parts = connection.split()
        city1, city2 = parts[0], parts[1]
        length = int(parts[2])
        n = len(parts)
        if n > 3:
            if parts[3] == "FERRY":
                joker_cost = int(parts[4])
                edge = FerryEdge(Node(city1), Node(city2), length, joker_cost)
            elif parts[3] == "TUNNEL":
                edge = Edge(Node(city1), Node(city2), length, tunnel=True)
            else:
                color = CardColor(parts[3].lower())
                if n > 4 and parts[4] == "TUNNEL":
                    edge = ColoredEdge(Node(city1), Node(city2), length, color, tunnel=True)
                else:
                    edge = ColoredEdge(Node(city1), Node(city2), length, color)
        else:
            edge = Edge(Node(city1), Node(city2), length)
        edges_list.append((city1, city2, edge))

    graph = Graph()
    for city in cities:
        graph.add_node(city)
    for city1, city2, edge in edges_list:
        if city1 not in cities or city2 not in cities:
            warnings.warn(f"One of the cities {city1} or {city2} is not in the list of cities.")
        graph.add_edge(city1, city2, edge)

    return graph

if __name__ == "__main__":
    graph = parse_graph("static/europe/cities.txt", "static/europe/connections.txt")

    import networkx as nx
    import matplotlib.pyplot as plt
    G = nx.MultiGraph()
    for node_name, node in graph.nodes.items():
        G.add_node(node_name)
    for edge_key, edge in graph.edges.items():
        node_names = list(edge_key.split())
        G.add_edge(node_names[0], node_names[1])
    fixed_pos = {"Cadiz": [0, 0], "Edinburgh": [0, 3], "Petrograd": [5, 3], "Erzurum": [5, 0], "Palermo": [1.5, 0], "Brest": [0, 2]}
    pos = nx.spring_layout(G, 1/4, pos=fixed_pos, fixed=fixed_pos.keys())
    nx.draw(G, pos, with_labels=False, node_size=50)
    nx.draw_networkx_labels(G, pos, font_size=8, bbox=dict(facecolor="white", edgecolor="black", boxstyle="round,pad=0.3"))
    plt.show()

