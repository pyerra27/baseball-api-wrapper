"""
baseball_api_wrapper
====================
A Python wrapper for the official MLB Stats API (https://statsapi.mlb.com).

Quick start::

    from baseball_api_wrapper import get_teams

    teams = get_teams(2024)
    for team in teams:
        print(team["id"], team["name"])
"""

from .client import MLBStatsAPIError, MLBStatsClient
from .modules.teams import get_teams
from .modules.roster import get_roster
from .modules.players import get_player_info, get_player_stats, get_player_career_splits
from .modules.games import get_schedule, get_boxscore, get_game_by_pk

__all__ = [
    "MLBStatsClient",
    "MLBStatsAPIError",
    "get_teams",
    "get_roster",
    "get_player_info",
    "get_player_stats",
    "get_player_career_splits",
    "get_schedule",
    "get_boxscore",
    "get_game_by_pk",
]
