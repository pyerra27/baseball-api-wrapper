"""
Tests for baseball_api.teams
==============================
Uses ``unittest.mock`` to patch HTTP calls so the test suite can run
without a network connection.

Test categories:
    * Unit tests  – exercise ``get_teams`` logic with mocked HTTP responses.
    * Error tests – verify correct exceptions are raised on bad inputs or
                    API error responses.
"""

import unittest
from unittest.mock import MagicMock, patch

from baseball_api.client import MLBStatsAPIError, MLBStatsClient
from baseball_api.teams import get_teams, MLB_SPORT_ID


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_team(team_id: int, name: str) -> dict:
    """Return a minimal team dict that mirrors the API response shape."""
    return {
        "id": team_id,
        "name": name,
        "teamCode": name[:3].lower(),
        "abbreviation": name[:3].upper(),
        "teamName": name.split()[-1],
        "locationName": name.split()[0],
        "league": {"id": 103, "name": "American League"},
        "division": {"id": 200, "name": "AL West"},
        "venue": {"id": 1, "name": "Some Stadium"},
    }


MOCK_TEAMS = [
    _make_team(147, "New York Yankees"),
    _make_team(111, "Boston Red Sox"),
    _make_team(141, "Toronto Blue Jays"),
]

MOCK_API_RESPONSE = {"teams": MOCK_TEAMS, "copyright": "Copyright 2024 MLB"}


# ---------------------------------------------------------------------------
# Helper: build a mock MLBStatsClient whose .get() returns a preset payload
# ---------------------------------------------------------------------------

def _mock_client(return_value: dict) -> MLBStatsClient:
    client = MagicMock(spec=MLBStatsClient)
    client.get.return_value = return_value
    return client


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

class TestGetTeams(unittest.TestCase):

    # --- Basic functionality ------------------------------------------------

    def test_returns_list_of_teams(self):
        """get_teams should return the list nested under the 'teams' key."""
        client = _mock_client(MOCK_API_RESPONSE)
        result = get_teams(2024, client=client)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)

    def test_team_dict_contains_expected_keys(self):
        """Each team dict should contain at minimum 'id' and 'name'."""
        client = _mock_client(MOCK_API_RESPONSE)
        teams = get_teams(2024, client=client)
        for team in teams:
            self.assertIn("id", team)
            self.assertIn("name", team)

    def test_team_ids_match_fixture(self):
        """Returned team IDs should match the fixture data."""
        client = _mock_client(MOCK_API_RESPONSE)
        teams = get_teams(2024, client=client)
        ids = [t["id"] for t in teams]
        self.assertEqual(sorted(ids), sorted([147, 111, 141]))

    def test_empty_response_returns_empty_list(self):
        """When the API returns no teams, an empty list should be returned."""
        client = _mock_client({"teams": []})
        result = get_teams(2024, client=client)
        self.assertEqual(result, [])

    def test_missing_teams_key_returns_empty_list(self):
        """If the API response lacks the 'teams' key, return an empty list."""
        client = _mock_client({"copyright": "MLB"})
        result = get_teams(2024, client=client)
        self.assertEqual(result, [])

    # --- Query parameter forwarding ----------------------------------------

    def test_season_passed_as_string(self):
        """The season parameter should be converted to a string."""
        client = _mock_client(MOCK_API_RESPONSE)
        get_teams(2024, client=client)
        _, kwargs = client.get.call_args
        self.assertEqual(kwargs["params"]["season"], "2024")

    def test_season_string_accepted(self):
        """A season provided as a string should also work."""
        client = _mock_client(MOCK_API_RESPONSE)
        get_teams("2024", client=client)
        _, kwargs = client.get.call_args
        self.assertEqual(kwargs["params"]["season"], "2024")

    def test_default_sport_id_is_mlb(self):
        """Default sportId must be 1 (MLB major leagues)."""
        client = _mock_client(MOCK_API_RESPONSE)
        get_teams(2024, client=client)
        _, kwargs = client.get.call_args
        self.assertEqual(kwargs["params"]["sportId"], MLB_SPORT_ID)

    def test_custom_sport_id_forwarded(self):
        """A custom sport_id should be forwarded as-is."""
        client = _mock_client(MOCK_API_RESPONSE)
        get_teams(2024, sport_id=11, client=client)
        _, kwargs = client.get.call_args
        self.assertEqual(kwargs["params"]["sportId"], 11)

    def test_league_ids_forwarded_as_csv(self):
        """league_ids should be joined into a comma-separated string."""
        client = _mock_client(MOCK_API_RESPONSE)
        get_teams(2024, league_ids=[103, 104], client=client)
        _, kwargs = client.get.call_args
        self.assertEqual(kwargs["params"]["leagueIds"], "103,104")

    def test_single_league_id_forwarded(self):
        """A single league_id should still be converted to a string."""
        client = _mock_client(MOCK_API_RESPONSE)
        get_teams(2024, league_ids=[103], client=client)
        _, kwargs = client.get.call_args
        self.assertEqual(kwargs["params"]["leagueIds"], "103")

    def test_league_ids_not_sent_when_none(self):
        """leagueIds should not appear in params when not specified."""
        client = _mock_client(MOCK_API_RESPONSE)
        get_teams(2024, client=client)
        _, kwargs = client.get.call_args
        self.assertNotIn("leagueIds", kwargs["params"])

    def test_division_id_forwarded(self):
        """division_id should be included in params when provided."""
        client = _mock_client(MOCK_API_RESPONSE)
        get_teams(2024, division_id=200, client=client)
        _, kwargs = client.get.call_args
        self.assertEqual(kwargs["params"]["divisionId"], 200)

    def test_division_id_not_sent_when_none(self):
        """divisionId should not appear in params when not specified."""
        client = _mock_client(MOCK_API_RESPONSE)
        get_teams(2024, client=client)
        _, kwargs = client.get.call_args
        self.assertNotIn("divisionId", kwargs["params"])

    def test_active_status_forwarded(self):
        """active_status 'B' should appear as activeStatus in params."""
        client = _mock_client(MOCK_API_RESPONSE)
        get_teams(2024, active_status="B", client=client)
        _, kwargs = client.get.call_args
        self.assertEqual(kwargs["params"]["activeStatus"], "B")

    def test_active_status_not_sent_when_none(self):
        """activeStatus should not appear in params when not specified."""
        client = _mock_client(MOCK_API_RESPONSE)
        get_teams(2024, client=client)
        _, kwargs = client.get.call_args
        self.assertNotIn("activeStatus", kwargs["params"])

    # --- Validation ---------------------------------------------------------

    def test_invalid_active_status_raises_value_error(self):
        """An unrecognised active_status value should raise ValueError."""
        client = _mock_client(MOCK_API_RESPONSE)
        with self.assertRaises(ValueError):
            get_teams(2024, active_status="INVALID", client=client)

    def test_valid_active_statuses_accepted(self):
        """All four valid active_status values should be accepted."""
        for status in ("Y", "N", "P", "B"):
            with self.subTest(status=status):
                client = _mock_client(MOCK_API_RESPONSE)
                # Should not raise
                get_teams(2024, active_status=status, client=client)

    # --- API error propagation ----------------------------------------------

    def test_api_error_propagates(self):
        """MLBStatsAPIError from the client should propagate to the caller."""
        client = MagicMock(spec=MLBStatsClient)
        client.get.side_effect = MLBStatsAPIError(404, "Not Found")
        with self.assertRaises(MLBStatsAPIError):
            get_teams(2024, client=client)

    # --- Default client creation --------------------------------------------

    def test_creates_default_client_when_none_provided(self):
        """When no client is given, a default MLBStatsClient should be used."""
        with patch("baseball_api.teams.MLBStatsClient") as MockClient:
            mock_instance = MockClient.return_value.__enter__.return_value
            mock_instance.get.return_value = MOCK_API_RESPONSE

            # Patch context-manager protocol used internally
            mock_ctx = MagicMock()
            mock_ctx.__enter__ = MagicMock(return_value=mock_instance)
            mock_ctx.__exit__ = MagicMock(return_value=False)
            MockClient.return_value = mock_ctx

            # Re-use get_teams without a client; just ensure it does not raise
            # and that MLBStatsClient was instantiated.
            with patch("baseball_api.teams.MLBStatsClient") as MC:
                mc_instance = MagicMock()
                mc_instance.get.return_value = MOCK_API_RESPONSE
                MC.return_value = mc_instance
                result = get_teams(2024)
                MC.assert_called_once()
                self.assertIsInstance(result, list)


# ---------------------------------------------------------------------------
# Run tests directly
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
