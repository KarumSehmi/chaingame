import os
import unicodedata

def normalize_name(name):
    return unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII').lower().replace(" ", "")

def load_player_names():
    file_path = os.path.join(os.path.dirname(__file__), 'top_500_football_players_names.txt')
    with open(file_path, 'r', encoding='utf-8') as file:
        player_names = {normalize_name(line.strip()): line.strip() for line in file.readlines()}
    return player_names

player_names = load_player_names()