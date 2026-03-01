# baseball-api

A Python wrapper for the [official MLB Stats API](https://statsapi.mlb.com).

## Installation

Make sure to create and activate a python virtual enviroment

```bash
pip install -r requirements.txt
```

## Quick Start

```python
from baseball_api import get_teams

# All 30 MLB teams for the 2024 season
teams = get_teams(2024)
for team in teams:
    print(team["id"], team["name"])

# American League only
al_teams = get_teams(2024, league_ids=[103])

# Include historical / inactive franchises
all_franchises = get_teams(2024, active_status="B")
```

## Running Tests

```bash
pytest
```

## Project Structure

```
baseball_api/
├── __init__.py      # Public API surface
├── client.py        # Low-level HTTP client
└── teams.py         # Teams endpoint wrapper

tests/
└── test_teams.py    # Unit tests for teams module
```
