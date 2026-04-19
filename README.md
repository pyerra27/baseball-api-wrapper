# baseball-api-wrapper

A Python wrapper for the official [MLB Stats API](https://statsapi.mlb.com).

## Installation

Clone the repo and install in editable mode so changes to the source are reflected immediately:

```bash
git clone <your-repo-url>
cd baseball-api-wrapper
pip install -e ".[dev]"   # includes pytest and test dependencies
```

For use in another project without dev tools:

```bash
pip install -e /path/to/baseball-api-wrapper
```

## Quick Start

```python
from baseball_api_wrapper import get_teams, get_roster

# List all MLB teams for the 2024 season
teams = get_teams(2024)
for team in teams:
    print(team["id"], team["name"])

# Get the active roster for the New York Yankees (teamId=147)
roster = get_roster(147, season=2024)
for player in roster:
    print(player["person"]["fullName"], player["position"]["name"])
```

## Using the Low-Level Client

For endpoints not yet covered by a module, use `MLBStatsClient` directly:

```python
from baseball_api_wrapper import MLBStatsClient

with MLBStatsClient() as client:
    data = client.get("/api/v1/standings", params={"leagueId": 103, "season": 2024})
    print(data)
```

## Project Structure

```
baseball_api_wrapper/          # Installable package
    __init__.py        # Public API surface
    client.py          # Low-level HTTP client (MLBStatsClient, MLBStatsAPIError)
    modules/
        teams.py       # get_teams()
        roster.py      # get_roster()
tests/                 # pytest test suite
    test_teams.py
    test_roster.py
pyproject.toml         # Build & dependency config
```

## Running Tests

```bash
pytest                        # Run all tests
pytest --cov=baseball_api_wrapper     # Run with coverage report
```

## Error Handling

Network or API errors raise `MLBStatsAPIError`:

```python
from baseball_api_wrapper import MLBStatsClient, MLBStatsAPIError

try:
    with MLBStatsClient() as client:
        data = client.get("/api/v1/teams/99999")  # Non-existent team
except MLBStatsAPIError as e:
    print(f"API error {e.status_code}: {e.message}")
```

## License

MIT — see [LICENSE](LICENSE) for details.
