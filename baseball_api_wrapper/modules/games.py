"""
Games
=====
Functions for retrieving MLB game schedule and score data from the Stats API.

The primary entry point is :func:`get_schedule`, which returns games for a
given date.  By default it fetches regular-season MLB games only.
"""

from typing import Any, Dict, List, Optional

from ..client import MLBStatsClient

_SCHEDULE_PATH = "/api/v1/schedule"
_BOXSCORE_PATH = "/api/v1/game/{game_pk}/boxscore"

MLB_SPORT_ID = 1


def get_schedule(
    date: str,
    sport_id: int = MLB_SPORT_ID,
    game_type: str = "R",
    client: Optional[MLBStatsClient] = None,
) -> List[Dict[str, Any]]:
    """
    Return all games scheduled for the given date.

    Args:
        date:
            The date to query in ``YYYY-MM-DD`` format, e.g. ``"2024-04-01"``.
        sport_id:
            Top-level sport identifier.  Use ``1`` (default) for MLB.
        game_type:
            Game type filter.  ``"R"`` (default) returns regular-season games.
            Pass ``"S"`` for spring training, ``"P"`` for playoffs, or ``"A"``
            for the All-Star game.
        client:
            Optional pre-configured :class:`~baseball_api_wrapper.client.MLBStatsClient`.
            If omitted, a default client is created for this single call.

    Returns:
        A list of game dictionaries as returned by the MLB Stats API
        ``/api/v1/schedule`` endpoint.  Returns an empty list when no games
        are scheduled for the requested date.

    Raises:
        baseball_api_wrapper.client.MLBStatsAPIError:
            If the API returns a non-2xx HTTP status code.
        requests.RequestException:
            On network-level failures.
    """
    params: Dict[str, Any] = {
        "sportId": sport_id,
        "date": date,
        "gameType": game_type,
    }

    _owns_client = client is None
    if _owns_client:
        client = MLBStatsClient()

    try:
        data = client.get(_SCHEDULE_PATH, params=params)
    finally:
        if _owns_client:
            client.close()

    dates = data.get("dates", [])
    if not dates:
        return []
    return dates[0].get("games", [])


def get_game_by_pk(
    game_pk: int,
    client: Optional[MLBStatsClient] = None,
) -> Dict[str, Any]:
    """
    Return the schedule entry for a single game by its ``gamePk``.

    Useful for fetching lightweight metadata (status, date, teams) without
    the full boxscore payload.

    Args:
        game_pk: The unique game identifier.
        client: Optional pre-configured :class:`~baseball_api_wrapper.client.MLBStatsClient`.

    Returns:
        The game dictionary for the requested ``gamePk``, or an empty dict
        if the game is not found.
    """
    params: Dict[str, Any] = {"gamePks": game_pk, "sportId": MLB_SPORT_ID}

    _owns_client = client is None
    if _owns_client:
        client = MLBStatsClient()

    try:
        data = client.get(_SCHEDULE_PATH, params=params)
    finally:
        if _owns_client:
            client.close()

    dates = data.get("dates", [])
    if not dates:
        return {}
    games = dates[0].get("games", [])
    return games[0] if games else {}


def get_boxscore(
    game_pk: int,
    client: Optional[MLBStatsClient] = None,
) -> Dict[str, Any]:
    """
    Return the box score for a single game.

    Args:
        game_pk:
            The unique game identifier (``gamePk``) returned by
            :func:`get_schedule`.
        client:
            Optional pre-configured :class:`~baseball_api_wrapper.client.MLBStatsClient`.
            If omitted, a default client is created for this single call.

    Returns:
        The raw box score dictionary as returned by the MLB Stats API
        ``/api/v1/game/{gamePk}/boxscore`` endpoint.

    Raises:
        baseball_api_wrapper.client.MLBStatsAPIError:
            If the API returns a non-2xx HTTP status code.
        requests.RequestException:
            On network-level failures.
    """
    path = _BOXSCORE_PATH.format(game_pk=game_pk)

    _owns_client = client is None
    if _owns_client:
        client = MLBStatsClient()

    try:
        return client.get(path)
    finally:
        if _owns_client:
            client.close()
