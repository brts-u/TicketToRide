from __future__ import annotations

import json

from pydantic.fields import defaultdict
from typing import List, Tuple, TYPE_CHECKING
from enum import Enum
from board_state import Graph, Node, Edge, ColoredEdge, FerryEdge, CardColor, parse_graph
import random

if TYPE_CHECKING:
    from board_state import *

class PlayerColor(Enum):
    RED = 'red'
    BLUE = 'blue'
    GREEN = 'green'
    YELLOW = 'yellow'
    BLACK = 'black'

class Ticket:
    def __init__(self, city1: Node, city2: Node, points: int):
        self.city1: Node = city1
        self.city2: Node = city2
        self.points: int = points

    def __repr__(self):
        return f"Ticket from {self.city1.name} to {self.city2.name} for {self.points} points"

    def jsonify(self):
        return {
            'from': self.city1.name,
            'to': self.city2.name,
            'points': self.points
        }

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
        self.trains_left: int = 45
        self.tickets: List[Ticket] = []
        self.score: int = 0

    def check_can_claim_route(self, edge: Edge) -> bool:
        if edge.occupied_by is not None:
            return False
        if self.trains_left < edge.length:
            return False
        if isinstance(edge, ColoredEdge):
            color_needed = edge.color
            cards_needed = edge.length
            available_cards = self.cards[color_needed] + self.cards[CardColor.JOKER]
            if available_cards < cards_needed:
                return False
        if isinstance(edge, FerryEdge):
            cards_needed = edge.length
            joker_needed = edge.joker_cost
            non_joker_needed = cards_needed - joker_needed
            non_joker_cards = [card_count for card_color, card_count in self.cards.items() if card_color != CardColor.JOKER]
            available_non_joker = max(non_joker_cards)
            available_non_joker += self.cards[CardColor.JOKER] - joker_needed
            available_joker = self.cards[CardColor.JOKER]
            if available_non_joker < non_joker_needed or available_joker < joker_needed:
                return False
        return True

class AIPlayer(Player):
    def __init__(self, color: PlayerColor):
        super().__init__(color)
        # TODO: Additional AI-specific attributes to be added here

class Station:
    def __init__(self, connection: Tuple[Node, Edge], player: Player):
        self.node: Node = connection[0]
        self.edge: Edge = connection[1]
        self.player: Player = player

class GameState:
    def __init__(self):
        self.graph: Graph = Graph()
        self.players: Dict[str, Player] = {} # Holds player order as well
        self.available_tickets: List[Ticket] = []
        self.long_tickets: List[Ticket] = []
        self.face_up_cards: List[CardColor] = [CardColor.random() for _ in range(5)] # 5 Initial face-up cards
        self.current_player_turn: str | None = None

    def parse_tickets(self, tickets_file: str):
        with open(tickets_file, 'r') as f:
            tickets = f.read().splitlines()
        for line in tickets:
            parts = line.split(' ')
            if len(parts) == 4 and parts[3] == 'LONG':
                city1_name, city2_name, points_str, _ = parts
                points = int(points_str)
                try:
                    city1 = self.graph.get_node(city1_name)
                    city2 = self.graph.get_node(city2_name)
                except KeyError:
                    warnings.warn(f"Ticket cities {city1_name} or {city2_name} not found in graph. Skipping ticket.")
                    continue
                ticket = Ticket(city1, city2, points)
                self.long_tickets.append(ticket)
            else:
                city1_name, city2_name, points_str = parts
                points = int(points_str)
                try:
                    city1 = self.graph.get_node(city1_name)
                    city2 = self.graph.get_node(city2_name)
                except KeyError:
                    warnings.warn(f"Ticket cities {city1_name} or {city2_name} not found in graph. Skipping ticket.")
                    continue
                ticket = Ticket(city1, city2, points)
                self.available_tickets.append(ticket)

    def add_player(self, player_name: str, color: PlayerColor):
        if player_name in self.players:
            warnings.warn("Player name already exists.")
        elif color in [p.color for p in self.players.values()]:
            warnings.warn("Player color already taken.")
        else:
            self.players[player_name] = Player(color)

    def advance_turn(self):
        if not self.players:
            return
        player_names = list(self.players.keys())
        if self.current_player_turn is None:
            self.current_player_turn = player_names[0]
        else:
            current_index = player_names.index(self.current_player_turn)
            next_index = (current_index + 1) % len(player_names)
            self.current_player_turn = player_names[next_index]

    def prompt_player_action(self, player_name: str) -> str:
        return f"Player {player_name}, it's your turn! Choose an action: DRAW_CARDS, CLAIM_ROUTE, DRAW_TICKETS."

    def draw_cards(self, player: Player) -> None:
        for _ in range(2):
            while True:
                print("Pick a card to draw (1-5 for face-up cards, 6 for random): ")
                choice = input().strip()
                if choice in ['1', '2', '3', '4', '5', '6']:
                    break
                else:
                    print("Invalid choice. Please try again.")
            choice = int(choice) - 1
            if choice == 5:
                drawn_card = CardColor.random()
                player.cards[drawn_card] += 1
                print(f"You drew a random card: {drawn_card.name}")
            else:
                drawn_card = self.face_up_cards[choice]
                player.cards[drawn_card] += 1
                print(f"You drew a face-up card: {drawn_card.name}")
                # Replace the drawn face-up card with a new random card
                self.face_up_cards[choice] = CardColor.random()

    def draw_tickets(self, player: Player):
        tickets = random.sample(self.available_tickets, 3)
        print("You have drawn the following tickets:")
        for idx, ticket in enumerate(tickets):
            print(f"{idx + 1}: {ticket}")
        print("Select tickets to keep (e.g., 1 3 to keep tickets 1 and 3): ")
        while True:
            choices = input().strip().split()
            if all(choice in ['1', '2', '3'] for choice in choices):
                break
            else:
                print("Invalid choices. Please try again.")
        for choice in choices:
            index = int(choice) - 1
            if 0 <= index < len(tickets):
                player.tickets.append(tickets[index])
                self.available_tickets.remove(tickets[index])

    def get_initial_tickets(self, player: Player):
        short_tickets = random.sample(self.available_tickets, 3)
        long_ticket = random.sample(self.long_tickets, 1)
        tickets = short_tickets + long_ticket
        player.tickets = player.tickets + tickets
        for ticket in short_tickets:
            self.available_tickets.remove(ticket)
        self.long_tickets.remove(long_ticket[0])
        return [ticket.jsonify() for ticket in tickets]

    def claim_route(self, player: Player):
        while True:
            print("Enter the two cities of the route you want to claim (e.g., CityA CityB): ")
            route_input = input().strip().split()
            if len(route_input) == 2:
                city1_name, city2_name = route_input
                edge = self.graph.get_edge(city1_name, city2_name)
                if not edge:
                    print("Invalid route. Please try again.")
                elif not player.check_can_claim_route(edge):
                    print("You cannot claim this route. Please try again.")
                else:
                    break
            else:
                print("Invalid input format. Please try again.")
        print("Select cards to use for claiming the route (e.g., red red joker):")
        while True:
            selected_cards = input().strip().split()
            selected_cards = [CardColor(card.lower()) for card in selected_cards]
            selected_cards_counts = defaultdict(int)
            for card in selected_cards:
                selected_cards_counts[card] += 1

            for card, count in selected_cards_counts.items():
                if player.cards[card] < count:
                    print(f"You do not have enough {card.name} cards. Please try again.")
                    break
            else:
                break
        # Deduct cards and update game state
        for card in selected_cards:
            player.cards[card] -= 1
        edge.occupied_by = player

    def build_station(self, player: Player):
        pass

    def begin_game(self):
        print("Game has begun!")
        print("Initial face-up cards: ", [card.name for card in self.face_up_cards])
        while any(player.trains_left > 2 for player in self.players.values()):
            print(self.prompt_player_action(self.current_player_turn))
            while True:
                turn = input().strip().upper()
                player = self.players[self.current_player_turn]
                print(f"Your cards: {player.cards}")
                print(f"Face-up cards to choose: {self.face_up_cards}")
                if turn == "DRAW_CARDS":
                    self.draw_cards(player)
                    break
                elif turn == "CLAIM_ROUTE":
                    self.claim_route(player)
                    break
                elif turn == "DRAW_TICKETS":
                    self.draw_tickets(player)
                    break
                else:
                    print("Invalid action. Please try again.")
            self.advance_turn()
        print("Game over! Calculating final scores...")

    def to_dict(self):
        data = {
            # public
            'graph': {
                'nodes': list(self.graph.nodes.keys()),
                'edges': [
                    {
                        'node1': edge.node1.name,
                        'node2': edge.node2.name,
                        'length': edge.length,
                        'color': edge.color.name if isinstance(edge, ColoredEdge) else None,
                        'joker_cost': edge.joker_cost if isinstance(edge, FerryEdge) else None,
                        'tunnel': edge.tunnel
                    }
                    for edge in self.graph.edges.values()
                ]
            },
            'players': {
                player_name: {
                    # public
                    'color': player.color.value,
                    # player specific private
                    'cards': {card_color.name: count for card_color, count in player.cards.items()},
                    # public
                    'trains_left': player.trains_left,
                    # player specific private
                    'tickets': [ticket.jsonify() for ticket in player.tickets],
                    # public
                    'score': player.score
                }
                for player_name, player in self.players.items()
            },
            # private
            'available_tickets': [ticket.jsonify() for ticket in self.available_tickets],
            'long_tickets': [ticket.jsonify() for ticket in self.long_tickets],
            # public
            'face_up_cards': [card.name for card in self.face_up_cards],
            'current_player_turn': self.current_player_turn
        }
        return data

def setup_game(cities_file: str, connections_file: str, tickets_file: str, player_info: List[Tuple[str, PlayerColor]]) -> GameState:
    game_state = GameState()
    game_state.graph = parse_graph(cities_file, connections_file)
    game_state.parse_tickets(tickets_file)
    for player_name, color in player_info:
        game_state.add_player(player_name, color)
        player = game_state.players[player_name]
        for _ in range(4):
            card = CardColor.random()
            player.cards[card] += 1
    if player_info:
        game_state.current_player_turn = player_info[0][0]
    return game_state

#
# if __name__ == "__main__":
#     # Example setup
#     cities_file = "static/europe/cities.txt"
#     connections_file = "static/europe/connections.txt"
#     tickets_file = "static/europe/tickets.txt"
#     player_info = [("Bartek", PlayerColor.RED)]#, ("Alicja", PlayerColor.BLUE)]
#     game_state = setup_game(cities_file, connections_file, tickets_file, player_info)
#     print("Game setup complete. Players:")
#     for player_name, player in game_state.players.items():
#         print(f"{player_name} ({player.color.name}) - Cards: {player.cards}, Trains left: {player.trains_left}")
#     game_state.begin_game()