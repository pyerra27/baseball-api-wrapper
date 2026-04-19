"""
Players
=======
Functions for retrieving player information and statistics from the MLB Stats API.

The two primary entry points are:

* :func:`get_player_info`  – Basic biographical data for a player.
* :func:`get_player_stats` – Season statistics for a player, split by group
                             (``"hitting"`` or ``"pitching"``).
"""

from typing import Any, Dict, List, Optional

from ..client import MLBStatsClient

_PLAYER_INFO_PATH = "/api/v1/people/{player_id}"
_PLAYER_STATS_PATH = "/api/v1/people/{player_id}/stats"


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
