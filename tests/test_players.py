"""
Tests for baseball_api_wrapper.modules.players
===============================================
All HTTP calls are mocked — no network connection required.

Test categories:
    * get_player_info         – correct data is returned, KeyError on missing player,
                                path construction, error propagation, default client.
    * get_player_stats        – stat dict returned from first split, None when no
                                splits, query parameter forwarding, group defaulting,
                                error propagation, default client.
    * get_player_career_splits – all splits returned, empty list when no data,
                                 correct params (yearByYear, hydrate), group forwarding.
"""

import unittest
from unittest.mock import MagicMock, patch

from baseball_api_wrapper.client import MLBStatsAPIError, MLBStatsClient
from baseball_api_wrapper.modules.players import get_player_info, get_player_stats, get_player_career_splits


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MOCK_PLAYER = {
    "id": 660271,
    "fullName": "Juan Soto",
    "primaryPosition": {
        "code": "9",
        "name": "Outfielder",
        "type": "Outfielder",
        "abbreviation": "LF",
    },
    "active": True,
}

MOCK_PLAYER_INFO_RESPONSE = {
    "people": [MOCK_PLAYER],
    "copyright": "Copyright 2024 MLB",
}

MOCK_HITTING_STATS = {
    "gamesPlayed": 157,
    "atBats": 559,
    "runs": 102,
    "hits": 157,
    "doubles": 34,
    "triples": 2,
    "homeRuns": 41,
    "rbi": 109,
    "stolenBases": 13,
    "avg": ".281",
    "obp": ".419",
    "slg": ".569",
    "ops": ".989",
}

MOCK_STATS_RESPONSE = {
    "stats": [
        {
            "type": {"displayName": "season"},
            "group": {"displayName": "hitting"},
            "splits": [{"season": "2024", "stat": MOCK_HITTING_STATS}],
        }
    ],
    "copyright": "Copyright 2024 MLB",
}

MOCK_EMPTY_STATS_RESPONSE = {
    "stats": [],
}

MOCK_NO_SPLITS_RESPONSE = {
    "stats": [
        {
            "type": {"displayName": "season"},
            "group": {"displayName": "hitting"},
            "splits": [],
        }
    ],
}

MOCK_CAREER_SPLITS = [
    {
        "season": "2023",
        "team": {"id": 135, "name": "San Diego Padres", "abbreviation": "SD"},
        "stat": MOCK_HITTING_STATS,
    },
    {
        "season": "2024",
        "team": {"id": 121, "name": "New York Mets", "abbreviation": "NYM"},
        "stat": MOCK_HITTING_STATS,
    },
]

MOCK_CAREER_RESPONSE = {
    "stats": [
        {
            "type": {"displayName": "yearByYear"},
            "group": {"displayName": "hitting"},
            "splits": MOCK_CAREER_SPLITS,
        }
    ],
    "copyright": "Copyright 2024 MLB",
}

MOCK_CAREER_EMPTY_RESPONSE = {
    "stats": [
        {
            "type": {"displayName": "yearByYear"},
            "group": {"displayName": "hitting"},
            "splits": [],
        }
    ],
}


def _mock_client(return_value: dict) -> MLBStatsClient:
    client = MagicMock(spec=MLBStatsClient)
    client.get.return_value = return_value
    return client


# ---------------------------------------------------------------------------
# Tests: get_player_info
# ---------------------------------------------------------------------------

class TestGetPlayerInfo(unittest.TestCase):

    def test_returns_player_dict(self):
        """get_player_info should return the first element from 'people'."""
        client = _mock_client(MOCK_PLAYER_INFO_RESPONSE)
        result = get_player_info(660271, client=client)
        self.assertEqual(result["id"], 660271)
        self.assertEqual(result["fullName"], "Juan Soto")

    def test_returns_primary_position(self):
        """Returned dict should include the primaryPosition nested object."""
        client = _mock_client(MOCK_PLAYER_INFO_RESPONSE)
        result = get_player_info(660271, client=client)
        self.assertIn("primaryPosition", result)
        self.assertEqual(result["primaryPosition"]["type"], "Outfielder")

    def test_correct_path_called(self):
        """The URL path should include the player_id."""
        client = _mock_client(MOCK_PLAYER_INFO_RESPONSE)
        get_player_info(660271, client=client)
        path_called = client.get.call_args[0][0]
        self.assertIn("660271", path_called)

    def test_raises_key_error_when_no_people(self):
        """KeyError should be raised when the API returns an empty people list."""
        client = _mock_client({"people": []})
        with self.assertRaises(KeyError):
            get_player_info(99999, client=client)

    def test_raises_key_error_when_people_key_missing(self):
        """KeyError should be raised when the 'people' key is absent."""
        client = _mock_client({"copyright": "MLB"})
        with self.assertRaises(KeyError):
            get_player_info(99999, client=client)

    def test_api_error_propagates(self):
        """MLBStatsAPIError from the client should propagate to the caller."""
        client = MagicMock(spec=MLBStatsClient)
        client.get.side_effect = MLBStatsAPIError(404, "Not Found")
        with self.assertRaises(MLBStatsAPIError):
            get_player_info(99999, client=client)

    def test_creates_default_client_when_none_provided(self):
        """A default MLBStatsClient should be created when none is supplied."""
        with patch("baseball_api_wrapper.modules.players.MLBStatsClient") as MockClient:
            mc_instance = MagicMock()
            mc_instance.get.return_value = MOCK_PLAYER_INFO_RESPONSE
            MockClient.return_value = mc_instance
            result = get_player_info(660271)
            MockClient.assert_called_once()
            self.assertEqual(result["id"], 660271)


# ---------------------------------------------------------------------------
# Tests: get_player_stats
# ---------------------------------------------------------------------------

class TestGetPlayerStats(unittest.TestCase):

    def test_returns_stat_dict_from_first_split(self):
        """get_player_stats should return the stat dict from the first split."""
        client = _mock_client(MOCK_STATS_RESPONSE)
        result = get_player_stats(660271, 2024, client=client)
        self.assertIsNotNone(result)
        self.assertEqual(result["homeRuns"], 41)
        self.assertEqual(result["avg"], ".281")

    def test_returns_none_when_no_splits(self):
        """None should be returned when the stat block has an empty splits list."""
        client = _mock_client(MOCK_NO_SPLITS_RESPONSE)
        result = get_player_stats(660271, 2024, client=client)
        self.assertIsNone(result)

    def test_returns_none_when_stats_list_empty(self):
        """None should be returned when the API returns no stat blocks."""
        client = _mock_client(MOCK_EMPTY_STATS_RESPONSE)
        result = get_player_stats(660271, 2024, client=client)
        self.assertIsNone(result)

    def test_season_forwarded_as_string(self):
        """Season should be coerced to a string in query params."""
        client = _mock_client(MOCK_STATS_RESPONSE)
        get_player_stats(660271, 2024, client=client)
        _, kwargs = client.get.call_args
        self.assertEqual(kwargs["params"]["season"], "2024")

    def test_stats_type_param_is_season(self):
        """The 'stats' query param should always be 'season'."""
        client = _mock_client(MOCK_STATS_RESPONSE)
        get_player_stats(660271, 2024, client=client)
        _, kwargs = client.get.call_args
        self.assertEqual(kwargs["params"]["stats"], "season")

    def test_default_group_is_hitting(self):
        """The default group param should be 'hitting'."""
        client = _mock_client(MOCK_STATS_RESPONSE)
        get_player_stats(660271, 2024, client=client)
        _, kwargs = client.get.call_args
        self.assertEqual(kwargs["params"]["group"], "hitting")

    def test_custom_group_forwarded(self):
        """A custom group value should be forwarded as-is."""
        client = _mock_client(MOCK_STATS_RESPONSE)
        get_player_stats(660271, 2024, group="pitching", client=client)
        _, kwargs = client.get.call_args
        self.assertEqual(kwargs["params"]["group"], "pitching")

    def test_correct_path_called(self):
        """The URL path should include the player_id."""
        client = _mock_client(MOCK_STATS_RESPONSE)
        get_player_stats(660271, 2024, client=client)
        path_called = client.get.call_args[0][0]
        self.assertIn("660271", path_called)

    def test_api_error_propagates(self):
        """MLBStatsAPIError from the client should propagate to the caller."""
        client = MagicMock(spec=MLBStatsClient)
        client.get.side_effect = MLBStatsAPIError(404, "Not Found")
        with self.assertRaises(MLBStatsAPIError):
            get_player_stats(99999, 2024, client=client)

    def test_creates_default_client_when_none_provided(self):
        """A default MLBStatsClient should be created when none is supplied."""
        with patch("baseball_api_wrapper.modules.players.MLBStatsClient") as MockClient:
            mc_instance = MagicMock()
            mc_instance.get.return_value = MOCK_STATS_RESPONSE
            MockClient.return_value = mc_instance
            result = get_player_stats(660271, 2024)
            MockClient.assert_called_once()
            self.assertIsNotNone(result)


# ---------------------------------------------------------------------------
# Tests: get_player_career_splits
# ---------------------------------------------------------------------------

class TestGetPlayerCareerSplits(unittest.TestCase):

    def test_returns_all_splits(self):
        """All splits from the first non-empty stat block should be returned."""
        client = _mock_client(MOCK_CAREER_RESPONSE)
        result = get_player_career_splits(660271, client=client)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["season"], "2023")
        self.assertEqual(result[1]["season"], "2024")

    def test_each_split_contains_team_and_stat(self):
        """Each split should include 'team' and 'stat' keys."""
        client = _mock_client(MOCK_CAREER_RESPONSE)
        result = get_player_career_splits(660271, client=client)
        for split in result:
            self.assertIn("team", split)
            self.assertIn("stat", split)

    def test_returns_empty_list_when_no_splits(self):
        """An empty list should be returned when splits is empty."""
        client = _mock_client(MOCK_CAREER_EMPTY_RESPONSE)
        result = get_player_career_splits(660271, client=client)
        self.assertEqual(result, [])

    def test_returns_empty_list_when_stats_missing(self):
        """An empty list should be returned when stats key is absent."""
        client = _mock_client({})
        result = get_player_career_splits(660271, client=client)
        self.assertEqual(result, [])

    def test_stats_type_param_is_year_by_year(self):
        """The 'stats' query param should be 'yearByYear'."""
        client = _mock_client(MOCK_CAREER_RESPONSE)
        get_player_career_splits(660271, client=client)
        _, kwargs = client.get.call_args
        self.assertEqual(kwargs["params"]["stats"], "yearByYear")

    def test_hydrate_team_param_included(self):
        """The 'hydrate' param should request full team info including abbreviation."""
        client = _mock_client(MOCK_CAREER_RESPONSE)
        get_player_career_splits(660271, client=client)
        _, kwargs = client.get.call_args
        self.assertEqual(kwargs["params"]["hydrate"], "team")

    def test_default_group_is_hitting(self):
        """The default group param should be 'hitting'."""
        client = _mock_client(MOCK_CAREER_RESPONSE)
        get_player_career_splits(660271, client=client)
        _, kwargs = client.get.call_args
        self.assertEqual(kwargs["params"]["group"], "hitting")

    def test_custom_group_forwarded(self):
        """A custom group value should be forwarded as-is."""
        client = _mock_client(MOCK_CAREER_RESPONSE)
        get_player_career_splits(660271, group="pitching", client=client)
        _, kwargs = client.get.call_args
        self.assertEqual(kwargs["params"]["group"], "pitching")

    def test_correct_path_called(self):
        """The URL path should include the player_id."""
        client = _mock_client(MOCK_CAREER_RESPONSE)
        get_player_career_splits(660271, client=client)
        path_called = client.get.call_args[0][0]
        self.assertIn("660271", path_called)

    def test_api_error_propagates(self):
        """MLBStatsAPIError from the client should propagate to the caller."""
        client = MagicMock(spec=MLBStatsClient)
        client.get.side_effect = MLBStatsAPIError(404, "Not Found")
        with self.assertRaises(MLBStatsAPIError):
            get_player_career_splits(99999, client=client)

    def test_creates_default_client_when_none_provided(self):
        """A default MLBStatsClient should be created when none is supplied."""
        with patch("baseball_api_wrapper.modules.players.MLBStatsClient") as MockClient:
            mc_instance = MagicMock()
            mc_instance.get.return_value = MOCK_CAREER_RESPONSE
            MockClient.return_value = mc_instance
            result = get_player_career_splits(660271)
            MockClient.assert_called_once()
            self.assertEqual(len(result), 2)


# ---------------------------------------------------------------------------
# Run tests directly
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
