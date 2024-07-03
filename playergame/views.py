from django.shortcuts import render
from django.http import JsonResponse
from .models import Player
import difflib
from collections import defaultdict
from .load_players import player_names
import unicodedata
import json
import heapq
import time
import random
import re

def normalize_name(name):
    return unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII').lower().replace(" ", "")

def index(request):
    return render(request, 'playergame/index.html')

def chain_index(request):
    if len(player_names) < 2:
        return JsonResponse({'error': 'Not enough players in the top 500 list.'}, status=400)
    
    start_player_key = random.choice(list(player_names.keys()))
    end_player_key = random.choice(list(player_names.keys()))
    
    while start_player_key == end_player_key:
        end_player_key = random.choice(list(player_names.keys()))
    
    context = {
        'start_player': player_names[start_player_key],
        'end_player': player_names[end_player_key]
    }
    return render(request, 'playergame/player_chain.html', context)

def suggest_player_names(request):
    query = request.GET.get('query', '').strip()
    if not query:
        return JsonResponse([], safe=False)

    normalized_query = normalize_name(query)
    players = Player.objects.all()
    player_data = {normalize_name(player.original_name): player.original_name for player in players}

    matches = find_close_matches(normalized_query, player_data)
    suggestions = [player_data[match] for match in matches]
    return JsonResponse(suggestions, safe=False)
def validate_chain(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        start_player = data['start_player']
        end_player = data['end_player']
        intermediate_players = data['intermediate_players']

        normalized_start_player = normalize_name(start_player)
        normalized_end_player = normalize_name(end_player)
        normalized_intermediate_players = [normalize_name(player) for player in intermediate_players]

        # Load and preprocess player data
        player_data = load_and_preprocess_player_data()

        # Validate the chain
        chain = [normalized_start_player] + normalized_intermediate_players + [normalized_end_player]
        invalid_links = []
        for i in range(len(chain) - 1):
            if chain[i] not in player_data or chain[i + 1] not in player_data:
                invalid_links.append({
                    'from': chain[i],
                    'to': chain[i + 1],
                    'reason': 'One or both players not in database'
                })
                continue

            if not find_common_teams(player_data[chain[i]]['club_career'], player_data[chain[i + 1]]['club_career']) and \
               not find_common_teams(player_data[chain[i]]['intl_career'], player_data[chain[i + 1]]['intl_career']):
                invalid_links.append({
                    'from': chain[i],
                    'to': chain[i + 1],
                    'reason': 'No common teams'
                })

        if invalid_links:
            invalid_links_readable = [{'from': player_names.get(link['from'], link['from']), 
                                       'to': player_names.get(link['to'], link['to']), 
                                       'reason': link['reason']} for link in invalid_links]
            return JsonResponse({'valid': False, 'invalid_links': invalid_links_readable})

        return JsonResponse({'valid': True})
    return JsonResponse({'error': 'Invalid request method.'}, status=405)

def load_and_preprocess_player_data():
    players = Player.objects.all()
    player_data = {}
    for player in players:
        try:
            club_career = json.loads(player.club_career)
            intl_career = json.loads(player.intl_career)
        except Exception as e:
            print(f"Error parsing career data for player {player.original_name}: {e}")
            print(f"Problematic data: {player.club_career if 'club' in str(e).lower() else player.intl_career}")
            club_career = []
            intl_career = []

        player_data[player.normalized_name] = {
            'club_career': set(map(tuple, club_career)),
            'intl_career': set(map(tuple, intl_career))
        }
    return player_data

def find_common_teams(player1_career, player2_career):
    return player1_career & player2_career

def get_player_data(request):
    player_name = request.GET.get('player_name', '').strip()
    normalized_name = normalize_name(player_name)
    try:
        player = Player.objects.get(normalized_name=normalized_name)
        player_data = {
            'original_name': player.original_name,
            'wiki_url': player.wiki_url,
            'full_record': player.full_record,
            'club_career': player.club_career,
            'intl_career': player.intl_career
        }
        return JsonResponse(player_data)
    except Player.DoesNotExist:
        return JsonResponse({'error': 'Player not found'}, status=404)

def generate_player_chain(request):
    try:
        length = int(request.GET.get('length', '').strip())
    except ValueError:
        return JsonResponse({'error': 'Invalid length'}, status=400)

    if length < 2:
        return JsonResponse({'error': 'Length must be at least 2'}, status=400)

    # Load and preprocess player data
    player_data = load_and_preprocess_player_data()
    all_players = list(player_data.keys())

    # Select a random start and end player
    start_player = random.choice(all_players)
    end_player = random.choice(all_players)

    chain = [start_player]

    while len(chain) < length:
        next_player = random.choice(all_players)
        if next_player != chain[-1]:
            chain.append(next_player)

    chain_details = []
    for i in range(len(chain) - 1):
        player = Player.objects.get(normalized_name=chain[i])
        next_player = Player.objects.get(normalized_name=chain[i + 1])
        chain_details.append({
            'player': player.original_name,
            'wiki_url': player.wiki_url,
            'next_player': next_player.original_name,
            'common_clubs': [{'season': club[0], 'team': club[1]} for club in find_common_teams(player_data[player.normalized_name]['club_career'], player_data[next_player.normalized_name]['club_career'])],
            'common_intl': [{'season': intl[0], 'team': intl[1]} for intl in find_common_teams(player_data[player.normalized_name]['intl_career'], player_data[next_player.normalized_name]['intl_career'])]
        })

    return JsonResponse(chain_details, safe=False)

def find_close_matches(name, player_data, cutoff=0.8):
    normalized_names = list(player_data.keys())
    last_name = get_last_name(name)
    last_name_matches = [n for n in normalized_names if last_name in get_last_name(n)]
    last_name_matches_sorted = sorted(last_name_matches, key=lambda x: difflib.SequenceMatcher(None, name, x).ratio(), reverse=True)
    matches = last_name_matches_sorted[:5]
    if len(matches) < 5:
        additional_matches = difflib.get_close_matches(name, normalized_names, n=5-len(matches), cutoff=cutoff)
        matches.extend([m for m in additional_matches if m not in matches])
    return matches

def get_last_name(name):
    return name.split()[-1]

def a_star_find_link(player_data, start_player, end_player, link_type):
    def heuristic(player):
        common_clubs = find_common_teams(player_data[player]['club_career'], player_data[end_player]['club_career'])
        common_intl = find_common_teams(player_data[player]['intl_career'], player_data[end_player]['intl_career'])
        return -len(common_clubs) - len(common_intl)

    open_set = []
    heapq.heappush(open_set, (0, start_player, [start_player]))
    g_scores = defaultdict(lambda: float('inf'))
    g_scores[start_player] = 0
    visited = set()

    while open_set:
        _, current_player, path = heapq.heappop(open_set)
        if current_player in visited:
            continue
        visited.add(current_player)

        if current_player == end_player:
            return path

        for player in player_data.keys():
            if player == current_player or player in path:
                continue

            common_clubs = find_common_teams(player_data[current_player]['club_career'], player_data[player]['club_career'])
            common_intl = find_common_teams(player_data[current_player]['intl_career'], player_data[player]['intl_career'])

            if link_type == 'club' and common_clubs:
                tentative_g_score = g_scores[current_player] + 1
                if tentative_g_score < g_scores[player]:
                    g_scores[player] = tentative_g_score
                    f_score = tentative_g_score + heuristic(player)
                    heapq.heappush(open_set, (f_score, player, path + [player]))
            elif link_type == 'both' and (common_clubs or common_intl):
                tentative_g_score = g_scores[current_player] + 1
                if tentative_g_score < g_scores[player]:
                    g_scores[player] = tentative_g_score
                    f_score = tentative_g_score + heuristic(player)
                    heapq.heappush(open_set, (f_score, player, path + [player]))

    return None

def find_link(request):
    start_player = request.GET.get('start_player', '').strip()
    end_player = request.GET.get('end_player', '').strip()
    link_type = request.GET.get('link_type', 'both')

    if not start_player or not end_player:
        return JsonResponse({'error': 'Both player fields are required.'}, status=400)

    normalized_start_player = normalize_name(start_player)
    normalized_end_player = normalize_name(end_player)

    # Load and preprocess player data
    player_data = load_and_preprocess_player_data()

    start_time = time.time()
    shortest_link =  a_star_find_link(player_data, normalized_start_player, normalized_end_player, link_type)
    end_time = time.time()

    if shortest_link:
        link_details = []
        for i in range(len(shortest_link) - 1):
            player = Player.objects.get(normalized_name=shortest_link[i])
            next_player = Player.objects.get(normalized_name=shortest_link[i + 1])

            common_clubs = find_common_teams(player_data[player.normalized_name]['club_career'], player_data[next_player.normalized_name]['club_career'])
            common_intl = find_common_teams(player_data[player.normalized_name]['intl_career'], player_data[next_player.normalized_name]['intl_career'])

            formatted_common_clubs = []
            for club in common_clubs:
                club_parts = re.split(r'(\d{4}-\d{4}|\d{4})', club[0].strip())
                season = club_parts[1].strip() if len(club_parts) > 1 else club_parts[0].strip()
                team = club_parts[2].strip() + " " + club[1].strip()
                formatted_common_clubs.append({'season': season, 'team': team})

            formatted_common_intl = []
            for intl in common_intl:
                intl_parts = re.split(r'(\d{4}-\d{4}|\d{4})', intl[0].strip())
                season = intl_parts[1].strip() if len(intl_parts) > 1 else intl_parts[0].strip()
                team = intl_parts[2].strip() + " " + intl[1].strip()
                formatted_common_intl.append({'season': season, 'team': team})

            link_details.append({
                'player': player.original_name,
                'wiki_url': player.wiki_url,
                'next_player': next_player.original_name,
                'common_clubs': formatted_common_clubs,
                'common_intl': formatted_common_intl if link_type != 'club' else []  # Include intl only if not 'club'
            })
        print(f"Time taken to find link: {end_time - start_time:.2f} seconds")
        return JsonResponse(link_details, safe=False)
    else:
        print(f"Time taken to find link: {end_time - start_time:.2f} seconds")
        return JsonResponse({'error': 'No link found'}, status=404)
