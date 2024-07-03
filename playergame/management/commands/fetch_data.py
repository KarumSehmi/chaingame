from django.core.management.base import BaseCommand
from playergame.models import Player
import json

class Command(BaseCommand):
    help = 'Check and display player data from the database'

    def handle(self, *args, **kwargs):
        players = Player.objects.all()
        for player in players:
            try:
                club_career = json.loads(player.club_career)
                intl_career = json.loads(player.intl_career)
                self.stdout.write(self.style.SUCCESS(f"Player Name: {player.original_name}"))
                self.stdout.write(self.style.SUCCESS(f"Wikipedia URL: {player.wiki_url}"))
                self.stdout.write(self.style.SUCCESS(f"Club Career: {club_career}"))
                self.stdout.write(self.style.SUCCESS(f"International/Managerial Career: {intl_career}"))
                self.stdout.write(self.style.SUCCESS("-" * 40))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error parsing career data for player {player.original_name}: {e}"))
                self.stdout.write(self.style.ERROR(f"Problematic data: {player.club_career if 'club' in str(e).lower() else player.intl_career}"))

