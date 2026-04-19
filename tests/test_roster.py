"""
Tests for baseball_api_wrapper.modules.roster
==============================
All HTTP calls are mocked — no network connection required.

Test categories:
    * Basic functionality  – correct data is returned and unwrapped.
    * Query parameter forwarding – every supported param reaches the client.
    * RosterType handling  – enum values and raw strings both work.
    * Date validation      – malformed dates raise ValueError.
    * Error propagation    – API and network errors bubble up correctly.
    * Default client       – a client is created when none is supplied.
"""

import unittest
from unittest.mock import MagicMock, patch

from baseball_api_wrapper.client import MLBStatsAPIError, MLBStatsClient
from baseball_api_wrapper.modules.roster import RosterType, get_roster


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_player(player_id: int, full_name: str, jersey: str = "00") -> dict:
    """Return a minimal roster-entry dict mirroring the API response shape."""
    return {
        "person": {
            "id": player_id,
            "fullName": full_name,
            "link": f"/api/v1/people/{player_id}",
        },
        "jerseyNumber": jersey,
        "position": {
            "code": "1",
            "name": "Pitcher",
            "type": "Pitcher",
            "abbreviation": "P",
        },
        "status": {"code": "A", "description": "Active"},
        "parentTeamId": 147,
    }


MOCK_ROSTER = [
    _make_player(592450, "Gerrit Cole", "45"),
    _make_player(547989, "Aaron Judge", "99"),
    _make_player(641313, "Juan Soto", "22"),
]

MOCK_API_RESPONSE = {
    "roster": MOCK_ROSTER,
    "teamId": 147,
    "rosterType": "active",
    "copyright": "Copyright 2024 MLB",
}


def _mock_client(return_value: dict) -> MLBStatsClient:
    client = MagicMock(spec=MLBStatsClient)
    client.get.return_value = return_value
    return client


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

class TestGetRoster(unittest.TestCase):

    # --- Basic functionality ------------------------------------------------

    def test_returns_list_of_players(self):
        """get_roster should return the list nested under the 'roster' key."""
        client = _mock_client(MOCK_API_RESPONSE)
        result = get_roster(147, 2024, client=client)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)

    def test_player_dict_contains_expected_keys(self):
        """Each roster entry should contain 'person', 'position', and 'jerseyNumber'."""
        client = _mock_client(MOCK_API_RESPONSE)
        roster = get_roster(147, 2024, client=client)
        for entry in roster:
            self.assertIn("person", entry)
            self.assertIn("position", entry)
            self.assertIn("jerseyNumber", entry)

    def test_person_contains_id_and_name(self):
        """The nested 'person' dict should include 'id' and 'fullName'."""
        client = _mock_client(MOCK_API_RESPONSE)
        roster = get_roster(147, 2024, client=client)
        for entry in roster:
            self.assertIn("id", entry["person"])
            self.assertIn("fullName", entry["person"])

    def test_empty_response_returns_empty_list(self):
        """When the API returns no roster entries, an empty list is returned."""
        client = _mock_client({"roster": []})
        result = get_roster(147, 2024, client=client)
        self.assertEqual(result, [])

    def test_missing_roster_key_returns_empty_list(self):
        """If the API response lacks the 'roster' key, return an empty list."""
        client = _mock_client({"teamId": 147})
        result = get_roster(147, 2024, client=client)
        self.assertEqual(result, [])

    # --- Path construction --------------------------------------------------

    def test_correct_path_is_called(self):
        """The URL path should include the team_id."""
        client = _mock_client(MOCK_API_RESPONSE)
        get_roster(147, 2024, client=client)
        path_called = client.get.call_args[0][0]
        self.assertIn("147", path_called)

    def test_different_team_id_in_path(self):
        """Different team IDs should produce different URL paths."""
        client = _mock_client(MOCK_API_RESPONSE)
        get_roster(111, 2024, client=client)
        path_called = client.get.call_args[0][0]
        self.assertIn("111", path_called)

    # --- Query parameter forwarding ----------------------------------------

    def test_season_forwarded_as_string(self):
        """season should be coerced to a string in query params."""
        client = _mock_client(MOCK_API_RESPONSE)
        get_roster(147, 2024, client=client)
        _, kwargs = client.get.call_args
        self.assertEqual(kwargs["params"]["season"], "2024")

    def test_season_string_accepted(self):
        """A season provided as a string should also work."""
        client = _mock_client(MOCK_API_RESPONSE)
        get_roster(147, "2024", client=client)
        _, kwargs = client.get.call_args
        self.assertEqual(kwargs["params"]["season"], "2024")

    def test_default_roster_type_is_active(self):
        """Default rosterType param should be 'active'."""
        client = _mock_client(MOCK_API_RESPONSE)
        get_roster(147, 2024, client=client)
        _, kwargs = client.get.call_args
        self.assertEqual(kwargs["params"]["rosterType"], "active")

    def test_roster_type_enum_forwarded(self):
        """A RosterType enum value should be serialised to its string value."""
        client = _mock_client(MOCK_API_RESPONSE)
        get_roster(147, 2024, roster_type=RosterType.FORTY_MAN, client=client)
        _, kwargs = client.get.call_args
        self.assertEqual(kwargs["params"]["rosterType"], "40Man")

    def test_roster_type_raw_string_accepted(self):
        """A raw string roster type should be forwarded unchanged."""
        client = _mock_client(MOCK_API_RESPONSE)
        get_roster(147, 2024, roster_type="fullSeason", client=client)
        _, kwargs = client.get.call_args
        self.assertEqual(kwargs["params"]["rosterType"], "fullSeason")

    def test_date_forwarded_when_provided(self):
        """A valid date string should appear in query params."""
        client = _mock_client(MOCK_API_RESPONSE)
        get_roster(147, 2024, date="2024-07-04", client=client)
        _, kwargs = client.get.call_args
        self.assertEqual(kwargs["params"]["date"], "2024-07-04")

    def test_date_not_sent_when_none(self):
        """The date param should be absent when not provided."""
        client = _mock_client(MOCK_API_RESPONSE)
        get_roster(147, 2024, client=client)
        _, kwargs = client.get.call_args
        self.assertNotIn("date", kwargs["params"])

    # --- RosterType enum coverage ------------------------------------------

    def test_all_roster_type_values_are_strings(self):
        """Every RosterType member should be usable as a plain string."""
        for rt in RosterType:
            self.assertIsInstance(rt.value, str)

    def test_roster_type_str_comparison(self):
        """RosterType inherits from str, so direct comparison should work."""
        self.assertEqual(RosterType.ACTIVE, "active")
        self.assertEqual(RosterType.FORTY_MAN, "40Man")

    # --- Date validation ----------------------------------------------------

    def test_invalid_date_format_raises_value_error(self):
        """A date not in YYYY-MM-DD format should raise ValueError."""
        client = _mock_client(MOCK_API_RESPONSE)
        with self.assertRaises(ValueError):
            get_roster(147, 2024, date="07-04-2024", client=client)

    def test_non_date_string_raises_value_error(self):
        """A completely invalid date string should raise ValueError."""
        client = _mock_client(MOCK_API_RESPONSE)
        with self.assertRaises(ValueError):
            get_roster(147, 2024, date="not-a-date", client=client)

    def test_valid_date_does_not_raise(self):
        """A properly formatted date should not raise any exception."""
        client = _mock_client(MOCK_API_RESPONSE)
        try:
            get_roster(147, 2024, date="2024-04-01", client=client)
        except ValueError:
            self.fail("get_roster raised ValueError for a valid date")

    # --- Error propagation --------------------------------------------------

    def test_api_error_propagates(self):
        """MLBStatsAPIError from the client should propagate to the caller."""
        client = MagicMock(spec=MLBStatsClient)
        client.get.side_effect = MLBStatsAPIError(404, "Team not found")
        with self.assertRaises(MLBStatsAPIError):
            get_roster(9999, 2024, client=client)

    # --- Default client creation --------------------------------------------

    def test_creates_default_client_when_none_provided(self):
        """When no client is given, a default MLBStatsClient should be created."""
        with patch("baseball_api_wrapper.modules.roster.MLBStatsClient") as MockClient:
            mc_instance = MagicMock()
            mc_instance.get.return_value = MOCK_API_RESPONSE
            MockClient.return_value = mc_instance
            result = get_roster(147, 2024)
            MockClient.assert_called_once()
            self.assertIsInstance(result, list)


# ---------------------------------------------------------------------------
# Run tests directly
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
