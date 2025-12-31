import json
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Elmosliga.settings")
django.setup()

from League.models import League, Team

# Load JSON data
with open("teams.json", "r", encoding="utf-8") as file:
    data = json.load(file)

competitions = data["competitions"]

# Create leagues and their teams
for league_name, teams_list in competitions.items():
    # Create or get the league
    league, created = League.objects.get_or_create(
        name=league_name,
        defaults={
            'is_active': True,
            'first_place_points': 20,
            'second_place_points': 15,
            'third_place_points': 10,
            'fourth_place_points': 7,
            'fifth_place_points': 5,
            'sixth_place_points': 3,
        }
    )
    
    if created:
        print(f"✅ Created league: {league_name}")
    else:
        print(f"ℹ️  League already exists: {league_name}")
    
    # Add teams to the league
    teams_added = 0
    for team_name in teams_list:
        team, team_created = Team.objects.get_or_create(
            name=team_name,
            league=league
        )
        if team_created:
            teams_added += 1
    
    print(f"   Added {teams_added} teams to {league_name}")
    print()

print("✅ All leagues and teams have been added successfully!")