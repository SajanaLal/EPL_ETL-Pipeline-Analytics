import logging

import pandas as pd
import pyodbc

from src.config import CONNECTION_STRING


logger = logging.getLogger(__name__)


# ==================================================
# PREPARE DATA FOR SQL SERVER
# ==================================================

def prepare_teams(df):
    return df[
        [
            "team_id",
            "team_name",
            "team_code",
            "country",
            "founded",
            "venue_id",
            "venue_name",
            "venue_city",
            "venue_capacity",
            "venue_surface",
        ]
    ].rename(
        columns={
            "country": "team_country",
            "founded": "team_founded",
        }
    )


def prepare_fixtures(df):
    result = df[
        [
            "fixture_id",
            "fixture_date",
            "timestamp",
            "venue_name",
            "venue_city",
            "status_short",
            "round",
            "home_team_id",
            "home_team_name",
            "away_team_id",
            "away_team_name",
            "home_goals",
            "away_goals",
            "home_halftime_goals",
            "away_halftime_goals",
            "home_fulltime_goals",
            "away_fulltime_goals",
        ]
    ].copy()

    return result.rename(
        columns={
            "timestamp": "fixture_timestamp",
            "status_short": "match_status",
            "round": "league_round",
            "home_halftime_goals": "halftime_home_goals",
            "away_halftime_goals": "halftime_away_goals",
            "home_fulltime_goals": "fulltime_home_goals",
            "away_fulltime_goals": "fulltime_away_goals",
        }
    )


def prepare_standings(df):
    return df[
        [
            "position",
            "team_id",
            "team_name",
            "points",
            "goal_difference",
            "played",
            "wins",
            "draws",
            "losses",
            "goals_for",
            "goals_against",
        ]
    ].rename(
        columns={
            "played": "matches_played",
            "goals_for": "goals_scored",
            "goals_against": "goals_conceded",
        }
    )


# ==================================================
# INSERT DATA
# ==================================================

def insert_dataframe(cursor, table_name, df):
    """
    Insert a DataFrame into a predefined staging table.
    Table and column names come from this module, not user input.
    """

    if df.empty:
        raise ValueError(f"{table_name} DataFrame is empty.")

    columns = list(df.columns)

    column_sql = ", ".join(f"[{column}]" for column in columns)
    placeholders = ", ".join("?" for _ in columns)

    sql = (
        f"INSERT INTO {table_name} ({column_sql}) "
        f"VALUES ({placeholders})"
    )

    # Convert pandas missing values to Python None for SQL NULL.
    rows = [
        tuple(
            None if pd.isna(value) else value
            for value in row
        )
        for row in df.itertuples(index=False, name=None)
    ]

    cursor.fast_executemany = True
    cursor.executemany(sql, rows)

    logger.info("Inserted %s rows into %s", len(rows), table_name)

    return len(rows)


# ==================================================
# TRANSACTIONAL STAGING REFRESH
# ==================================================

def load_staging(transformed):
    """
    Refresh all staging tables in one transaction.
    Existing warehouse tables are not modified.
    """

    teams_df = prepare_teams(transformed["teams"])
    fixtures_df = prepare_fixtures(transformed["fixtures"])
    standings_df = prepare_standings(transformed["standings"])

    expected_counts = {
        "stg.Teams": len(teams_df),
        "stg.Fixtures": len(fixtures_df),
        "stg.Standings": len(standings_df),
    }

    connection = pyodbc.connect(
        CONNECTION_STRING,
        autocommit=False,
    )

    try:
        cursor = connection.cursor()

        # Delete child tables before parent tables.
        # All deletes are rolled back if any later operation fails.
        cursor.execute("DELETE FROM stg.Fixtures")
        cursor.execute("DELETE FROM stg.Standings")
        cursor.execute("DELETE FROM stg.Teams")

        insert_dataframe(cursor, "stg.Teams", teams_df)
        insert_dataframe(cursor, "stg.Fixtures", fixtures_df)
        insert_dataframe(cursor, "stg.Standings", standings_df)

        # Verify row counts inside the same transaction.
        for table_name, expected in expected_counts.items():
            schema, table = table_name.split(".")
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
                """,
                schema,
                table,
            )

            if cursor.fetchone()[0] != 1:
                raise RuntimeError(
                    f"Staging table {table_name} does not exist."
                )

            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            actual = cursor.fetchone()[0]

            if actual != expected:
                raise RuntimeError(
                    f"{table_name}: expected {expected} rows, "
                    f"found {actual}."
                )

            logger.info(
                "Verified %s: %s rows",
                table_name,
                actual,
            )

        connection.commit()
        logger.info("Staging refresh committed successfully.")

        return expected_counts

    except Exception:
        connection.rollback()
        logger.exception(
            "Staging refresh failed. Transaction rolled back."
        )
        raise

    finally:
        connection.close()
