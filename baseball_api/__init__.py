"""
baseball_api
============
A Python wrapper for the official MLB Stats API (https://statsapi.mlb.com).

Quick start::

    from baseball_api import get_teams

    teams = get_teams(2024)
    for team in teams:
        print(team["id"], team["name"])
"""

from .client import MLBStatsAPIError, MLBStatsClient
from .teams import get_teams

__all__ = [
    "MLBStatsClient",
    "MLBStatsAPIError",
    "get_teams",
]
