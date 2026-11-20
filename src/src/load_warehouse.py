from pathlib import Path
import logging

import pyodbc

from src import config


logger = logging.getLogger(__name__)

SQL_FILE = config.PROJECT_DIR / "sql" / "WarehouseLoad.sql"


def load_warehouse():
    """
    Execute the warehouse upsert SQL for the configured season.
    The SQL transaction handles commit and rollback.
    """
    if not SQL_FILE.exists():
        raise FileNotFoundError(
            f"Warehouse SQL script not found: {SQL_FILE}"
        )

    sql_script = SQL_FILE.read_text(encoding="utf-8")

    # GO is an SSMS batch separator, not a SQL Server statement.
    # Remove standalone GO lines so pyodbc can execute the batch.
    sql_lines = [
        line for line in sql_script.splitlines()
        if line.strip().upper() != "GO"
    ]
    sql_script = "\n".join(sql_lines)

    if "DECLARE @Season INT = ?;" not in sql_script:
        raise ValueError(
            "Warehouse SQL must contain "
            "'DECLARE @Season INT = ?;'"
        )

    logger.info(
        "Starting warehouse upsert for season %s",
        config.SEASON
    )

    with pyodbc.connect(
        config.CONNECTION_STRING,
        autocommit=True,
        timeout=30
    ) as connection:
        cursor = connection.cursor()
        cursor.execute(sql_script, config.SEASON)

        # Advance through result sets, if any, and capture the
        # final verification result returned by the SQL script.
        result = None

        while True:
            if cursor.description is not None:
                columns = [
                    column[0] for column in cursor.description
                ]
                rows = cursor.fetchall()

                if rows:
                    result = [
                        dict(zip(columns, row))
                        for row in rows
                    ]

            if not cursor.nextset():
                break

        logger.info(
            "Warehouse upsert completed for season %s",
            config.SEASON
        )

        return result


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    summary = load_warehouse()
    print("Warehouse load summary:")
    print(summary)
