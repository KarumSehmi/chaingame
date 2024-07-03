import os
import django
import re
import unicodedata
import json

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "player_chain.settings")
django.setup()

from playergame.models import Player

def read_player_data(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        content = file.read()
    players = re.findall(r"Player Name: .+?(?=\nPlayer Name: |\Z)", content, re.DOTALL)
    player_data = {}
    for player in players:
        details = re.search(r"Player Name: (.+?)\nWikipedia URL: (.+?)\n(.+)", player, re.DOTALL)
        original_name = details.group(1).strip()
        normalized_name = normalize_name(original_name)
        wiki_url = details.group(2).strip()
        full_record = details.group(3).strip()
        club_career = parse_career(full_record, "Club Career")
        intl_career = parse_career(full_record, "International/Managerial Career")
        player_data[normalized_name] = {
            'original_name': original_name,
            'wiki_url': wiki_url,
            'full_record': full_record,
            'club_career': json.dumps(list(club_career)),  # Convert set to JSON list
            'intl_career': json.dumps(list(intl_career))   # Convert set to JSON list
        }
    return player_data

def normalize_name(name):
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')
    return name.lower().replace(" ", "")

def parse_career(record, section_header):
    section_found = False
    career = set()
    for line in record.split("\n"):
        line = line.strip()
        if line == section_header:
            section_found = True
            continue
        if section_found:
            if line and "Season" not in line and "Squad" not in line:
                parts = line.rsplit(' ', 1)
                if len(parts) == 2:
                    season = parts[0].strip()
                    squad = parts[1].strip()
                    career.add((season, squad))
            elif not line:
                break
    return career

def populate_database(player_data):
    # Clear the existing data
    Player.objects.all().delete()

    for normalized_name, data in player_data.items():
        try:
            Player.objects.create(
                normalized_name=normalized_name,
                original_name=data['original_name'],
                wiki_url=data['wiki_url'],
                full_record=data['full_record'],
                club_career=data['club_career'],
                intl_career=data['intl_career']
            )
        except Exception as e:
            print(f"Error saving player {data['original_name']}: {e}")

if __name__ == "__main__":
    filename = "D:/CHAIN/game/ALLPLAYERSCLEANupdating.txt"
    player_data = read_player_data(filename)
    populate_database(player_data)
    print("Database population complete.")
