import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when a dataset fails a required data quality check."""
    pass


def require(condition, message):
    """Stop the pipeline when a required check fails."""
    if not condition:
        raise ValidationError(message)

    logger.info("PASS: %s", message)


def validate_teams(df):
    """Validate the transformed teams dataset."""

    require(not df.empty, "Teams dataset is not empty")
    require(df["team_id"].notna().all(), "Team IDs are not null")
    require(df["team_id"].is_unique, "Team IDs are unique")
    require(df["team_name"].notna().all(), "Team names are not null")

    return True


def validate_fixtures(df, teams_df):
    """Validate fixture keys, scores, dates, and team references."""

    require(not df.empty, "Fixtures dataset is not empty")
    require(df["fixture_id"].notna().all(), "Fixture IDs are not null")
    require(df["fixture_id"].is_unique, "Fixture IDs are unique")

    require(
        df["fixture_date"].notna().all(),
        "Fixture dates are not null",
    )

    require(
        (df["home_team_id"] != df["away_team_id"]).all(),
        "Home and away teams differ",
    )

    known_team_ids = set(teams_df["team_id"])

    home_ids = set(df["home_team_id"].dropna())
    away_ids = set(df["away_team_id"].dropna())

    require(
        home_ids.issubset(known_team_ids),
        "All home team IDs exist in teams",
    )

    require(
        away_ids.issubset(known_team_ids),
        "All away team IDs exist in teams",
    )

    require(
        df["season"].notna().all(),
        "Fixture seasons are not null",
    )

    return True


def validate_standings(df, teams_df):
    """Validate standings keys and football calculations."""

    require(not df.empty, "Standings dataset is not empty")
    require(df["team_id"].notna().all(), "Standing team IDs are not null")
    require(df["season"].notna().all(), "Standing seasons are not null")

    require(
        not df.duplicated(["team_id", "season"]).any(),
        "Team-season standings keys are unique",
    )

    known_team_ids = set(teams_df["team_id"])
    standing_team_ids = set(df["team_id"])

    require(
        standing_team_ids.issubset(known_team_ids),
        "All standings team IDs exist in teams",
    )

    require(
        (
            df["points"] == df["wins"] * 3 + df["draws"]
        ).all(),
        "Standings points equal wins * 3 + draws",
    )

    require(
        (
            df["goal_difference"]
            == df["goals_for"] - df["goals_against"]
        ).all(),
        "Goal difference equals goals for - goals against",
    )

    require(
        (df["played"] == df["wins"] + df["draws"] + df["losses"]).all(),
        "Played equals wins + draws + losses",
    )

    return True


def validate_all(transformed):
    """Run all dataset validations before loading."""

    teams_df = transformed["teams"]
    fixtures_df = transformed["fixtures"]
    standings_df = transformed["standings"]

    validate_teams(teams_df)
    validate_fixtures(fixtures_df, teams_df)
    validate_standings(standings_df, teams_df)

    logger.info("All dataset validations passed.")

    return True
