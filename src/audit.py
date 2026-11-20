import logging
import pyodbc

from src import config

logger = logging.getLogger(__name__)


def run_warehouse_audit():
    """Audit warehouse integrity for the configured EPL season."""

    checks = {
        "duplicate_team_ids": """
            SELECT COUNT(*)
            FROM (
                SELECT team_id
                FROM dw.DimTeam
                GROUP BY team_id
                HAVING COUNT(*) > 1
            ) AS duplicates;
        """,
        "duplicate_fixture_ids": """
            SELECT COUNT(*)
            FROM (
                SELECT fixture_id
                FROM dw.FactFixture
                GROUP BY fixture_id
                HAVING COUNT(*) > 1
            ) AS duplicates;
        """,
        "missing_fixture_teams": """
            SELECT COUNT(*)
            FROM dw.FactFixture AS f
            LEFT JOIN dw.DimTeam AS h
                ON f.home_team_id = h.team_id
            LEFT JOIN dw.DimTeam AS a
                ON f.away_team_id = a.team_id
            WHERE f.season = ?
              AND (h.team_id IS NULL OR a.team_id IS NULL);
        """,
        "invalid_standings": """
            SELECT COUNT(*)
            FROM dw.FactStandings
            WHERE season = ?
              AND (
                  points <> wins * 3 + draws
                  OR goal_difference <> goals_scored - goals_conceded
                  OR matches_played <> wins + draws + losses
              );
        """,
        "duplicate_standings_positions": """
            SELECT COUNT(*)
            FROM (
                SELECT season, position
                FROM dw.FactStandings
                WHERE season = ?
                GROUP BY season, position
                HAVING COUNT(*) > 1
            ) AS duplicates;
        """,
    }

    results = {}

    with pyodbc.connect(config.CONNECTION_STRING, timeout=30) as connection:
        cursor = connection.cursor()

        results["warehouse_teams"] = cursor.execute(
            "SELECT COUNT(*) FROM dw.DimTeam;"
        ).fetchone()[0]

        results["warehouse_fixtures"] = cursor.execute(
            "SELECT COUNT(*) FROM dw.FactFixture WHERE season = ?;",
            config.SEASON,
        ).fetchone()[0]

        results["warehouse_standings"] = cursor.execute(
            "SELECT COUNT(*) FROM dw.FactStandings WHERE season = ?;",
            config.SEASON,
        ).fetchone()[0]

        for name, query in checks.items():
            if name in {
                "missing_fixture_teams",
                "invalid_standings",
                "duplicate_standings_positions",
            }:
                count = cursor.execute(query, config.SEASON).fetchone()[0]
            else:
                count = cursor.execute(query).fetchone()[0]

            results[name] = count

    audit_checks = {
        name: count == 0
        for name, count in results.items()
        if name not in {
            "warehouse_teams",
            "warehouse_fixtures",
            "warehouse_standings",
        }
    }

    results["audit_checks"] = audit_checks
    results["audit_passed"] = all(audit_checks.values())

    if results["audit_passed"]:
        logger.info("Warehouse audit passed.")
    else:
        logger.error("Warehouse audit failed.")

    return results


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    audit_results = run_warehouse_audit()

    for name, value in audit_results.items():
        print(f"{name}: {value}")

    if not audit_results["audit_passed"]:
        raise SystemExit("Warehouse audit failed.")
