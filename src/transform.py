import pandas as pd


# ==================================================
# TEAMS TRANSFORMATION
# ==================================================

def transform_teams(data):
    """
    Flatten team and venue information into one row per team.
    """

    rows = []

    for item in data.get("response", []):
        team = item.get("team") or {}
        venue = item.get("venue") or {}

        rows.append({
            "team_id": team.get("id"),
            "team_name": team.get("name"),
            "team_code": team.get("code"),
            "country": team.get("country"),
            "founded": team.get("founded"),
            "national": team.get("national"),
            "team_logo": team.get("logo"),
            "venue_id": venue.get("id"),
            "venue_name": venue.get("name"),
            "venue_address": venue.get("address"),
            "venue_city": venue.get("city"),
            "venue_capacity": venue.get("capacity"),
            "venue_surface": venue.get("surface"),
        })

    df = pd.DataFrame(rows)

    if not df.empty:
        df["team_id"] = pd.to_numeric(
            df["team_id"], errors="raise"
        ).astype("int64")

        df = df.drop_duplicates(subset=["team_id"])

    return df


# ==================================================
# FIXTURES TRANSFORMATION
# ==================================================

def transform_fixtures(data):
    """
    Flatten fixture, league, team, goal, and status information.
    """

    rows = []

    for item in data.get("response", []):
        fixture = item.get("fixture") or {}
        league = item.get("league") or {}
        teams = item.get("teams") or {}
        home = teams.get("home") or {}
        away = teams.get("away") or {}
        goals = item.get("goals") or {}
        score = item.get("score") or {}
        fulltime = score.get("fulltime") or {}
        halftime = score.get("halftime") or {}
        status = fixture.get("status") or {}
        venue = fixture.get("venue") or {}

        rows.append({
            "fixture_id": fixture.get("id"),
            "league_id": league.get("id"),
            "season": league.get("season"),
            "round": league.get("round"),
            "fixture_date": fixture.get("date"),
            "timestamp": fixture.get("timestamp"),
            "referee": fixture.get("referee"),
            "venue_id": venue.get("id"),
            "venue_name": venue.get("name"),
            "venue_city": venue.get("city"),
            "home_team_id": home.get("id"),
            "home_team_name": home.get("name"),
            "away_team_id": away.get("id"),
            "away_team_name": away.get("name"),
            "home_goals": goals.get("home"),
            "away_goals": goals.get("away"),
            "home_fulltime_goals": fulltime.get("home"),
            "away_fulltime_goals": fulltime.get("away"),
            "home_halftime_goals": halftime.get("home"),
            "away_halftime_goals": halftime.get("away"),
            "home_winner": home.get("winner"),
            "away_winner": away.get("winner"),
            "status_short": status.get("short"),
            "status_long": status.get("long"),
            "elapsed_minutes": status.get("elapsed"),
        })

    df = pd.DataFrame(rows)

    if not df.empty:
        df["fixture_id"] = pd.to_numeric(
            df["fixture_id"], errors="raise"
        ).astype("int64")

        df["fixture_date"] = pd.to_datetime(
            df["fixture_date"], errors="raise", utc=True
        )

        df = df.drop_duplicates(subset=["fixture_id"])

    return df


# ==================================================
# STANDINGS TRANSFORMATION
# ==================================================

def transform_standings(data):
    """
    Unpack the league's nested standings table into one row per team.
    """

    rows = []

    for item in data.get("response", []):
        league = item.get("league") or {}

        for group in league.get("standings", []):
            for standing in group:
                team = standing.get("team") or {}
                all_stats = standing.get("all") or {}
                goals = all_stats.get("goals") or {}

                rows.append({
                    "team_id": team.get("id"),
                    "team_name": team.get("name"),
                    "season": league.get("season"),
                    "position": standing.get("rank"),
                    "points": standing.get("points"),
                    "goal_difference": standing.get("goalsDiff"),
                    "played": all_stats.get("played"),
                    "wins": all_stats.get("win"),
                    "draws": all_stats.get("draw"),
                    "losses": all_stats.get("lose"),
                    "goals_for": goals.get("for"),
                    "goals_against": goals.get("against"),
                    "form": standing.get("form"),
                    "description": standing.get("description"),
                    "group_name": standing.get("group"),
                    "updated_at": standing.get("update"),
                })

    df = pd.DataFrame(rows)

    if not df.empty:
        df["team_id"] = pd.to_numeric(
            df["team_id"], errors="raise"
        ).astype("int64")

        df = df.drop_duplicates(subset=["team_id", "season"])

    return df


# ==================================================
# TRANSFORM ALL DATASETS
# ==================================================

def transform_all(datasets):
    """
    Transform all extracted API responses into DataFrames.
    """

    transformed = {
        "teams": transform_teams(datasets["teams"]),
        "fixtures": transform_fixtures(datasets["fixtures"]),
        "standings": transform_standings(datasets["standings"]),
    }

    return transformed
