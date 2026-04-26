"""
Tests for baseball_api_wrapper.modules.games
==============================
Uses ``unittest.mock`` to patch HTTP calls so the test suite can run
without a network connection.

Test categories:
    * Unit tests  – exercise ``get_schedule``, ``get_game_by_pk``, and
                    ``get_boxscore`` with mocked HTTP responses.
    * Error tests – verify correct exceptions are raised on API errors.
"""

import unittest
from unittest.mock import MagicMock, patch

from baseball_api_wrapper.client import MLBStatsAPIError, MLBStatsClient
from baseball_api_wrapper.modules.games import (
    get_boxscore,
    get_game_by_pk,
    get_schedule,
    MLB_SPORT_ID,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_game(game_pk: int, status: str = "Final") -> dict:
    """Return a minimal game dict that mirrors the schedule API response shape."""
    return {
        "gamePk": game_pk,
        "gameDate": "2024-04-15T20:05:00Z",
        "status": {"detailedState": status},
        "teams": {
            "away": {"team": {"id": 147, "name": "New York Yankees"}, "score": 5, "isWinner": True},
            "home": {"team": {"id": 111, "name": "Boston Red Sox"}, "score": 3, "isWinner": False},
        },
    }


MOCK_GAMES = [_make_game(717465), _make_game(717466)]

MOCK_SCHEDULE_RESPONSE = {
    "dates": [{"date": "2024-04-15", "games": MOCK_GAMES}]
}

MOCK_BOXSCORE_RESPONSE = {
    "teams": {
        "away": {
            "team": {"id": 147, "name": "New York Yankees", "abbreviation": "NYY"},
            "teamStats": {"batting": {"runs": 5}},
            "players": {},
            "batters": [],
            "pitchers": [],
        },
        "home": {
            "team": {"id": 111, "name": "Boston Red Sox", "abbreviation": "BOS"},
            "teamStats": {"batting": {"runs": 3}},
            "players": {},
            "batters": [],
            "pitchers": [],
        },
    },
    "info": [],
}


def _mock_client(return_value: dict) -> MLBStatsClient:
    """Return a MagicMock MLBStatsClient whose .get() returns return_value."""
    client = MagicMock(spec=MLBStatsClient)
    client.get.return_value = return_value
    return client


# ---------------------------------------------------------------------------
# Tests: get_schedule
# ---------------------------------------------------------------------------

class TestGetSchedule(unittest.TestCase):

    # --- Basic functionality ------------------------------------------------

    def test_returns_list_of_games(self):
        """get_schedule should return the games list from the first date entry."""
        client = _mock_client(MOCK_SCHEDULE_RESPONSE)
        result = get_schedule("2024-04-15", client=client)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

    def test_game_dict_contains_expected_keys(self):
        """Each game dict should contain at minimum 'gamePk' and 'teams'."""
        client = _mock_client(MOCK_SCHEDULE_RESPONSE)
        games = get_schedule("2024-04-15", client=client)
        for game in games:
            self.assertIn("gamePk", game)
            self.assertIn("teams", game)

    def test_game_pks_match_fixture(self):
        """Returned gamePk values should match the fixture data."""
        client = _mock_client(MOCK_SCHEDULE_RESPONSE)
        games = get_schedule("2024-04-15", client=client)
        pks = [g["gamePk"] for g in games]
        self.assertEqual(sorted(pks), [717465, 717466])

    def test_empty_dates_returns_empty_list(self):
        """When the API returns no dates, an empty list should be returned."""
        client = _mock_client({"dates": []})
        result = get_schedule("2024-04-15", client=client)
        self.assertEqual(result, [])

    def test_empty_games_returns_empty_list(self):
        """When the date has no games, an empty list should be returned."""
        client = _mock_client({"dates": [{"date": "2024-04-15", "games": []}]})
        result = get_schedule("2024-04-15", client=client)
        self.assertEqual(result, [])

    def test_missing_dates_key_returns_empty_list(self):
        """If the API response lacks the 'dates' key, return an empty list."""
        client = _mock_client({"copyright": "MLB"})
        result = get_schedule("2024-04-15", client=client)
        self.assertEqual(result, [])

    # --- Query parameter forwarding ----------------------------------------

    def test_date_forwarded_in_params(self):
        """The date parameter should be forwarded to the API."""
        client = _mock_client(MOCK_SCHEDULE_RESPONSE)
        get_schedule("2024-04-15", client=client)
        _, kwargs = client.get.call_args
        self.assertEqual(kwargs["params"]["date"], "2024-04-15")

    def test_default_sport_id_is_mlb(self):
        """Default sportId must be 1 (MLB major leagues)."""
        client = _mock_client(MOCK_SCHEDULE_RESPONSE)
        get_schedule("2024-04-15", client=client)
        _, kwargs = client.get.call_args
        self.assertEqual(kwargs["params"]["sportId"], MLB_SPORT_ID)

    def test_custom_sport_id_forwarded(self):
        """A custom sport_id should be forwarded as-is."""
        client = _mock_client(MOCK_SCHEDULE_RESPONSE)
        get_schedule("2024-04-15", sport_id=11, client=client)
        _, kwargs = client.get.call_args
        self.assertEqual(kwargs["params"]["sportId"], 11)

    def test_default_game_type_is_regular_season(self):
        """Default gameType must be 'R' (regular season)."""
        client = _mock_client(MOCK_SCHEDULE_RESPONSE)
        get_schedule("2024-04-15", client=client)
        _, kwargs = client.get.call_args
        self.assertEqual(kwargs["params"]["gameType"], "R")

    def test_custom_game_type_forwarded(self):
        """A custom game_type should be forwarded to the API."""
        client = _mock_client(MOCK_SCHEDULE_RESPONSE)
        get_schedule("2024-04-15", game_type="P", client=client)
        _, kwargs = client.get.call_args
        self.assertEqual(kwargs["params"]["gameType"], "P")

    # --- API error propagation ----------------------------------------------

    def test_api_error_propagates(self):
        """MLBStatsAPIError from the client should propagate to the caller."""
        client = MagicMock(spec=MLBStatsClient)
        client.get.side_effect = MLBStatsAPIError(503, "Service Unavailable")
        with self.assertRaises(MLBStatsAPIError):
            get_schedule("2024-04-15", client=client)

    # --- Default client creation --------------------------------------------

    def test_creates_default_client_when_none_provided(self):
        """When no client is given, a default MLBStatsClient should be created."""
        with patch("baseball_api_wrapper.modules.games.MLBStatsClient") as MC:
            mc_instance = MagicMock()
            mc_instance.get.return_value = MOCK_SCHEDULE_RESPONSE
            MC.return_value = mc_instance
            result = get_schedule("2024-04-15")
            MC.assert_called_once()
            self.assertIsInstance(result, list)


# ---------------------------------------------------------------------------
# Tests: get_game_by_pk
# ---------------------------------------------------------------------------

class TestGetGameByPk(unittest.TestCase):

    # --- Basic functionality ------------------------------------------------

    def test_returns_first_game_dict(self):
        """get_game_by_pk should return the first game in the response."""
        client = _mock_client(MOCK_SCHEDULE_RESPONSE)
        result = get_game_by_pk(717465, client=client)
        self.assertIsInstance(result, dict)
        self.assertIn("gamePk", result)

    def test_empty_dates_returns_empty_dict(self):
        """When the API returns no dates, an empty dict should be returned."""
        client = _mock_client({"dates": []})
        result = get_game_by_pk(717465, client=client)
        self.assertEqual(result, {})

    def test_empty_games_returns_empty_dict(self):
        """When the date has no games, an empty dict should be returned."""
        client = _mock_client({"dates": [{"date": "2024-04-15", "games": []}]})
        result = get_game_by_pk(717465, client=client)
        self.assertEqual(result, {})

    # --- Query parameter forwarding ----------------------------------------

    def test_game_pk_forwarded_in_params(self):
        """The game_pk should be forwarded as 'gamePks' in the query params."""
        client = _mock_client(MOCK_SCHEDULE_RESPONSE)
        get_game_by_pk(717465, client=client)
        _, kwargs = client.get.call_args
        self.assertEqual(kwargs["params"]["gamePks"], 717465)

    def test_sport_id_forwarded_in_params(self):
        """The MLB sport ID should be included in the query params."""
        client = _mock_client(MOCK_SCHEDULE_RESPONSE)
        get_game_by_pk(717465, client=client)
        _, kwargs = client.get.call_args
        self.assertEqual(kwargs["params"]["sportId"], MLB_SPORT_ID)

    # --- API error propagation ----------------------------------------------

    def test_api_error_propagates(self):
        """MLBStatsAPIError from the client should propagate to the caller."""
        client = MagicMock(spec=MLBStatsClient)
        client.get.side_effect = MLBStatsAPIError(404, "Not Found")
        with self.assertRaises(MLBStatsAPIError):
            get_game_by_pk(717465, client=client)

    # --- Default client creation --------------------------------------------

    def test_creates_default_client_when_none_provided(self):
        """When no client is given, a default MLBStatsClient should be created."""
        with patch("baseball_api_wrapper.modules.games.MLBStatsClient") as MC:
            mc_instance = MagicMock()
            mc_instance.get.return_value = MOCK_SCHEDULE_RESPONSE
            MC.return_value = mc_instance
            result = get_game_by_pk(717465)
            MC.assert_called_once()
            self.assertIsInstance(result, dict)


# ---------------------------------------------------------------------------
# Tests: get_boxscore
# ---------------------------------------------------------------------------

class TestGetBoxscore(unittest.TestCase):

    # --- Basic functionality ------------------------------------------------

    def test_returns_raw_response_dict(self):
        """get_boxscore should return the raw API response as a dict."""
        client = _mock_client(MOCK_BOXSCORE_RESPONSE)
        result = get_boxscore(717465, client=client)
        self.assertIsInstance(result, dict)
        self.assertIn("teams", result)

    def test_away_and_home_teams_present(self):
        """The returned dict should contain both 'away' and 'home' under 'teams'."""
        client = _mock_client(MOCK_BOXSCORE_RESPONSE)
        result = get_boxscore(717465, client=client)
        self.assertIn("away", result["teams"])
        self.assertIn("home", result["teams"])

    # --- Correct path used -------------------------------------------------

    def test_game_pk_included_in_request_path(self):
        """The request path should contain the game_pk."""
        client = _mock_client(MOCK_BOXSCORE_RESPONSE)
        get_boxscore(717465, client=client)
        args, _ = client.get.call_args
        self.assertIn("717465", args[0])

    # --- API error propagation ----------------------------------------------

    def test_api_error_propagates(self):
        """MLBStatsAPIError from the client should propagate to the caller."""
        client = MagicMock(spec=MLBStatsClient)
        client.get.side_effect = MLBStatsAPIError(404, "Not Found")
        with self.assertRaises(MLBStatsAPIError):
            get_boxscore(717465, client=client)

    # --- Default client creation --------------------------------------------

    def test_creates_default_client_when_none_provided(self):
        """When no client is given, a default MLBStatsClient should be created."""
        with patch("baseball_api_wrapper.modules.games.MLBStatsClient") as MC:
            mc_instance = MagicMock()
            mc_instance.get.return_value = MOCK_BOXSCORE_RESPONSE
            MC.return_value = mc_instance
            result = get_boxscore(717465)
            MC.assert_called_once()
            self.assertIn("teams", result)


# ---------------------------------------------------------------------------
# Run tests directly
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
