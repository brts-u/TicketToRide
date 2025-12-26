from board_state import *
from typing import Dict, List, Tuple

class PlayerColor(Enum):
    RED = 'red'
    BLUE = 'blue'
    GREEN = 'green'
    YELLOW = 'yellow'
    BLACK = 'black'

class Ticket:
    def __init__(self, city1: str, city2: str, points: int):
        self.city1: str = city1
        self.city2: str = city2
        self.points: int = points

class Player:
    def __init__(self, color: PlayerColor):
        self.color: PlayerColor = color
        self.cards: Dict[CardColor, int] = {
            CardColor.RED: 0,
            CardColor.ORANGE: 0,
            CardColor.YELLOW: 0,
            CardColor.GREEN: 0,
            CardColor.BLUE: 0,
            CardColor.PINK: 0,
            CardColor.BLACK: 0,
            CardColor.WHITE: 0,
            CardColor.JOKER: 0
        }
        self.tickets: List[Ticket] = []
        self.score: int = 0

class GameState:
    def __init__(self):
        self.graph: Graph = Graph()
        self.players: Dict[int, Player] = {}
        self.available_tickets: List[Ticket] = []
        self.face_up_cards: Tuple[CardColor, CardColor, CardColor, CardColor, CardColor] = (
            CardColor.random(),
            CardColor.random(),
            CardColor.random(),
            CardColor.random(),
            CardColor.random()
        )

