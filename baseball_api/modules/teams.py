"""
Teams
=====
Functions for retrieving MLB team data from the Stats API.

The primary entry point is :func:`get_teams`, which returns a list of teams
for a given MLB season.  Optional filters let callers narrow results by
league, division, or active status.

MLB Sport IDs
-------------
The Stats API serves data for multiple sports / levels. When fetching
official MLB teams you almost always want ``sport_id=1`` (the default).

Common sport IDs:
  * 1  – MLB (majors)
  * 11 – Triple-A
  * 12 – Double-A
  * 13 – High-A
  * 14 – Single-A

Common league IDs:
  * 103 – American League
  * 104 – National League
"""

from typing import Any, Dict, List, Optional

from ..client import MLBStatsClient

# The Stats API path for the teams collection resource.
_TEAMS_PATH = "/api/v1/teams"

# Sport ID for MLB (major leagues).
MLB_SPORT_ID = 1


def get_teams(
    season: int | str,
    sport_id: int = MLB_SPORT_ID,
    league_ids: Optional[List[int]] = None,
    division_id: Optional[int] = None,
    active_status: Optional[str] = None,
    client: Optional[MLBStatsClient] = None,
) -> List[Dict[str, Any]]:
    """
    Return a list of MLB teams for the specified season.

    Each team is represented as a dictionary containing at minimum:
    ``id``, ``name``, ``teamCode``, ``abbreviation``, ``teamName``,
    ``locationName``, ``league``, ``division``, and ``venue``.

    Args:
        season:
            The MLB season year to query, e.g. ``2024`` or ``"2024"``.
        sport_id:
            Top-level sport identifier.  Use ``1`` (default) for MLB
            major-league teams.  Pass a different value to retrieve teams
            from the minors or other affiliated leagues.
        league_ids:
            Optional list of league IDs to filter results.  For example,
            ``[103]`` returns only American League teams and ``[104]``
            returns only National League teams.
        division_id:
            Optional single division ID to restrict results to one division
            (e.g. ``200`` for AL West).
        active_status:
            Controls which teams are included based on their franchise
            status.  Accepted values:

            * ``"Y"`` – active franchises only (default API behaviour)
            * ``"N"`` – inactive / historical franchises only
            * ``"P"`` – pending franchises
            * ``"B"`` – all franchises regardless of status

        client:
            Optional pre-configured :class:`~mlb_statsapi.client.MLBStatsClient`
            instance.  If omitted, a default client pointing at the official
            production endpoint is created and used for the single call.

    Returns:
        A list of team dictionaries as returned by the MLB Stats API.
        Returns an empty list if the API response contains no teams.

    Raises:
        mlb_statsapi.client.MLBStatsAPIError:
            If the API returns a non-2xx HTTP status code.
        requests.RequestException:
            On network-level failures (timeouts, DNS errors, etc.).
        ValueError:
            If *active_status* is not one of the accepted values.

    Example::

        from mlb_statsapi.teams import get_teams

        # All 30 MLB teams for the 2024 season
        teams = get_teams(2024)
        for team in teams:
            print(team["id"], team["name"])

        # Only American League teams
        al_teams = get_teams(2024, league_ids=[103])

        # All historical franchises (active + inactive)
        all_franchises = get_teams(2024, active_status="B")
    """
    valid_statuses = {"Y", "N", "P", "B"}
    if active_status is not None and active_status not in valid_statuses:
        raise ValueError(
            f"active_status must be one of {sorted(valid_statuses)}, "
            f"got {active_status!r}"
        )

    params: Dict[str, Any] = {
        "season": str(season),
        "sportId": sport_id,
    }

    if league_ids is not None:
        # The API accepts a comma-separated list for leagueIds.
        params["leagueIds"] = ",".join(str(lid) for lid in league_ids)

    if division_id is not None:
        params["divisionId"] = division_id

    if active_status is not None:
        params["activeStatus"] = active_status

    # Allow callers to inject a client (useful for testing / custom config).
    # If none is provided, create a throw-away default client.
    _owns_client = client is None
    if _owns_client:
        client = MLBStatsClient()

    try:
        data = client.get(_TEAMS_PATH, params=params)
    finally:
        if _owns_client:
            client.close()

    return data.get("teams", [])
