"""
Players
=======
Functions for retrieving player information and statistics from the MLB Stats API.

The primary entry points are:

* :func:`get_player_info`  – Basic biographical data for a player.
* :func:`get_player_stats` – Season statistics for a player, split by group
                             (``"hitting"`` or ``"pitching"``).
* :func:`search_players`   – Players whose names match a search string.
"""

from typing import Any, Dict, List, Optional

from ..client import MLBStatsClient
from .teams import MLB_SPORT_ID

_PLAYER_INFO_PATH = "/api/v1/people/{player_id}"
_PLAYER_STATS_PATH = "/api/v1/people/{player_id}/stats"
_PLAYER_SEARCH_PATH = "/api/v1/people/search"


def get_player_career_splits(
    player_id: int,
    group: str = "hitting",
    client: Optional[MLBStatsClient] = None,
) -> List[Dict[str, Any]]:
    """
    Return year-by-year career splits for a player.

    Each element in the returned list is a split dict with at minimum:
    * ``season`` – The season year as a string, e.g. ``"2024"``.
    * ``stat``   – Dict of raw stat fields for that season.

    Args:
        player_id: The player's unique MLB identifier.
        group:     ``"hitting"`` or ``"pitching"``. Defaults to ``"hitting"``.
        client:    Optional pre-configured MLBStatsClient.

    Returns:
        A list of split dicts, one per season, or an empty list if none found.
    """
    path = _PLAYER_STATS_PATH.format(player_id=player_id)
    params: Dict[str, Any] = {"stats": "yearByYear", "group": group, "hydrate": "team"}

    _owns_client = client is None
    if _owns_client:
        client = MLBStatsClient()

    try:
        data = client.get(path, params=params)
    finally:
        if _owns_client:
            client.close()

    for stat_block in data.get("stats", []):
        splits = stat_block.get("splits", [])
        if splits:
            return splits

    return []


def get_player_info(
    player_id: int,
    client: Optional[MLBStatsClient] = None,
) -> Dict[str, Any]:
    """
    Return biographical information for a single player.

    The returned dict contains at minimum:

    * ``id``               – Player's unique MLB identifier.
    * ``fullName``         – Full display name.
    * ``primaryPosition``  – Nested dict with ``code``, ``name``, ``type``,
                             ``abbreviation``.
    * ``active``           – Boolean indicating whether the player is active.

    Args:
        player_id:
            The player's unique MLB identifier, e.g. ``660271`` for Juan Soto.
        client:
            Optional pre-configured :class:`~baseball_api_wrapper.client.MLBStatsClient`.
            If omitted, a default client is created for the single call.

    Returns:
        A dict of player attributes as returned by the MLB Stats API.

    Raises:
        mlb_statsapi.client.MLBStatsAPIError:
            If the API returns a non-2xx HTTP status code.
        requests.RequestException:
            On network-level failures.
        KeyError:
            If the response contains no ``people`` entry for the given ID.
    """
    path = _PLAYER_INFO_PATH.format(player_id=player_id)

    _owns_client = client is None
    if _owns_client:
        client = MLBStatsClient()

    try:
        data = client.get(path)
    finally:
        if _owns_client:
            client.close()

    people: List[Dict[str, Any]] = data.get("people", [])
    if not people:
        raise KeyError(f"No player found with id {player_id}")

    return people[0]


def get_player_stats(
    player_id: int,
    season: int | str,
    group: str = "hitting",
    client: Optional[MLBStatsClient] = None,
) -> Optional[Dict[str, Any]]:
    """
    Return season statistics for a player for a specific stat group.

    Args:
        player_id:
            The player's unique MLB identifier.
        season:
            The MLB season year, e.g. ``2024`` or ``"2024"``.
        group:
            The stat group to retrieve: ``"hitting"`` or ``"pitching"``.
            Defaults to ``"hitting"``.
        client:
            Optional pre-configured :class:`~baseball_api_wrapper.client.MLBStatsClient`.
            If omitted, a default client is created for the single call.

    Returns:
        A dict of raw stat fields as returned by the MLB Stats API (the
        ``stat`` object from the first split), or ``None`` if no stats are
        available for this player/season/group combination.

    Raises:
        mlb_statsapi.client.MLBStatsAPIError:
            If the API returns a non-2xx HTTP status code.
        requests.RequestException:
            On network-level failures.

    Example::

        from baseball_api_wrapper.modules.players import get_player_stats

        # Juan Soto's 2024 hitting stats
        stats = get_player_stats(660271, 2024, group="hitting")
        if stats:
            print(stats["avg"], stats["homeRuns"], stats["rbi"])
    """
    path = _PLAYER_STATS_PATH.format(player_id=player_id)

    params: Dict[str, Any] = {
        "stats": "season",
        "season": str(season),
        "group": group,
    }

    _owns_client = client is None
    if _owns_client:
        client = MLBStatsClient()

    try:
        data = client.get(path, params=params)
    finally:
        if _owns_client:
            client.close()

    for stat_block in data.get("stats", []):
        splits = stat_block.get("splits", [])
        if splits:
            return splits[0].get("stat")

    return None


def search_players(
    name: str,
    sport_id: int = MLB_SPORT_ID,
    active: Optional[bool] = None,
    limit: Optional[int] = None,
    client: Optional[MLBStatsClient] = None,
) -> List[Dict[str, Any]]:
    """
    Return players whose names match a search string.

    Each word in *name* matches the start of a first, last, or other name,
    and every word must match: ``"jud"`` finds Aaron Judge and Wally Judnich,
    while ``"aaron jud"`` finds only Aaron Judge. Matching ignores case and
    accents, so ``"acuna"`` finds Ronald Acuña Jr. A comma searches for
    several names at once, e.g. ``"judge,ohtani"``.

    Results cover every era and list active players first. They can include
    minor leaguers who have never played in the majors; those players have
    no ``mlbDebutDate``.

    Args:
        name:
            All or part of a player's name, e.g. ``"judge"`` or ``"aaron j"``.
        sport_id:
            Top-level sport identifier. Defaults to ``1`` (MLB).
        active:
            ``True`` for active players only, ``False`` for inactive players
            only. Omit to search both.
        limit:
            Maximum number of players to return. The API returns at most 50,
            however high this is set.
        client:
            Optional pre-configured :class:`~baseball_api_wrapper.client.MLBStatsClient`.
            If omitted, a default client is created for the single call.

    Returns:
        A list of player dicts as returned by the MLB Stats API, or an empty
        list if no players match.

    Raises:
        baseball_api_wrapper.client.MLBStatsAPIError:
            If the API returns a non-2xx HTTP status code.
        requests.RequestException:
            On network-level failures.
        ValueError:
            If *name* is blank or *limit* is less than 1.

    Example::

        from baseball_api_wrapper import search_players

        # Aaron Judge's id is 592450
        for player in search_players("aaron judge"):
            print(player["id"], player["fullName"])
    """
    query = name.strip()
    if not query:
        # The API doesn't reject a blank search; it returns a default list of players.
        raise ValueError("name must not be blank")
    if limit is not None and limit < 1:
        raise ValueError(f"limit must be at least 1, got {limit!r}")

    params: Dict[str, Any] = {
        "names": query,
        "sportIds": sport_id,
    }

    if active is not None:
        # Send the API's lowercase form; requests would send "True" or "False".
        params["active"] = "true" if active else "false"

    if limit is not None:
        params["limit"] = limit

    _owns_client = client is None
    if _owns_client:
        client = MLBStatsClient()

    try:
        data = client.get(_PLAYER_SEARCH_PATH, params=params)
    finally:
        if _owns_client:
            client.close()

    return data.get("people", [])
