"""
Roster
======
Functions for retrieving team roster data from the MLB Stats API.

The primary entry point is :func:`get_roster`, which returns the list of
players (or coaches) on a team's roster for a given season.

Roster Types
------------
The API supports several roster types, all exposed via the :class:`RosterType`
enum.  The most commonly used types are:

* ``ACTIVE``          – The 26-man active roster (in-season).
* ``FORTY_MAN``       – The full 40-man roster.
* ``FULL_SEASON``     – Everyone who appeared on the roster at any point
                        during the season.
* ``FULL_ROSTER``     – Alias similar to FULL_SEASON.
* ``NON_ROSTER_INVITEES`` – Spring training non-roster invitees.
* ``DEPTH_CHART``     – Organizational depth chart.
* ``GAMEDAY``         – Roster for a specific game day.
* ``ALL_TIME``        – All-time historical roster.
* ``COACH``           – Coaching staff.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from ..client import MLBStatsClient

# API path template for the roster endpoint. teamId is a required path param.
_ROSTER_PATH = "/api/v1/teams/{team_id}/roster"


class RosterType(str, Enum):
    """
    Valid roster type identifiers accepted by the MLB Stats API.

    Inherits from ``str`` so values can be passed directly wherever a
    string is expected (e.g. as a query parameter).
    """

    ACTIVE = "active"
    FORTY_MAN = "40Man"
    FULL_SEASON = "fullSeason"
    FULL_ROSTER = "fullRoster"
    NON_ROSTER_INVITEES = "nonRosterInvitees"
    DEPTH_CHART = "depthChart"
    GAMEDAY = "gameday"
    ALL_TIME = "allTime"
    COACH = "coach"


def get_roster(
    team_id: int,
    season: int | str,
    roster_type: RosterType | str = RosterType.ACTIVE,
    date: Optional[str] = None,
    client: Optional[MLBStatsClient] = None,
) -> List[Dict[str, Any]]:
    """
    Return the roster for a team in a given MLB season.

    Each entry in the returned list represents a single player (or coach,
    depending on *roster_type*) and contains at minimum:

    * ``person``       – dict with ``id``, ``fullName``, ``link``
    * ``jerseyNumber`` – string jersey number
    * ``position``     – dict with ``code``, ``name``, ``type``,
                         ``abbreviation``
    * ``status``       – dict describing roster transaction status
    * ``parentTeamId`` – ID of the parent MLB club

    Args:
        team_id:
            Unique team identifier, e.g. ``147`` for the New York Yankees.
            Team IDs can be retrieved via :func:`~mlb_statsapi.teams.get_teams`.
        season:
            The MLB season year, e.g. ``2024`` or ``"2024"``.
        roster_type:
            The type of roster to retrieve.  Accepts a :class:`RosterType`
            member or the equivalent raw string value.  Defaults to
            :attr:`RosterType.ACTIVE` (the 26-man active roster).
        date:
            Optional date string in ``"YYYY-MM-DD"`` format.  When provided,
            the roster is returned as it stood on that date.  Useful with
            ``roster_type=RosterType.GAMEDAY``.
        client:
            Optional pre-configured :class:`~mlb_statsapi.client.MLBStatsClient`
            instance.  If omitted, a default client pointing at the official
            production endpoint is created and used for the single call.

    Returns:
        A list of roster-entry dictionaries as returned by the MLB Stats API.
        Returns an empty list if the API response contains no roster entries.

    Raises:
        mlb_statsapi.client.MLBStatsAPIError:
            If the API returns a non-2xx HTTP status code (e.g. 404 for an
            unknown team ID).
        requests.RequestException:
            On network-level failures (timeouts, DNS errors, etc.).
        ValueError:
            If *date* is provided but does not match the ``YYYY-MM-DD`` format.

    Example::

        from mlb_statsapi.roster import get_roster, RosterType

        # Active 26-man roster for the 2024 Yankees
        roster = get_roster(147, 2024)
        for entry in roster:
            print(entry["jerseyNumber"], entry["person"]["fullName"])

        # Full 40-man roster
        roster_40 = get_roster(147, 2024, roster_type=RosterType.FORTY_MAN)

        # Roster as of a specific date
        roster_date = get_roster(147, 2024, date="2024-07-04")
    """
    if date is not None:
        _validate_date(date)

    path = _ROSTER_PATH.format(team_id=team_id)

    params: Dict[str, Any] = {
        "season": str(season),
        "rosterType": roster_type.value if isinstance(roster_type, RosterType) else roster_type,
    }

    if date is not None:
        params["date"] = date

    _owns_client = client is None
    if _owns_client:
        client = MLBStatsClient()

    try:
        data = client.get(path, params=params)
    finally:
        if _owns_client:
            client.close()

    return data.get("roster", [])


def _validate_date(date: str) -> None:
    """
    Ensure *date* matches the ``YYYY-MM-DD`` format expected by the API.

    Args:
        date: Date string to validate.

    Raises:
        ValueError: If the string is not a valid ``YYYY-MM-DD`` date.
    """
    import datetime

    try:
        datetime.date.fromisoformat(date)
    except ValueError:
        raise ValueError(
            f"date must be in YYYY-MM-DD format, got {date!r}"
        )
