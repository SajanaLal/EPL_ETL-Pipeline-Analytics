import logging
from datetime import datetime

from src import (
    config,
    extract,
    transform,
    validate,
    load_staging,
    load_warehouse,
    audit,
)


def setup_logging():
    """Configure console and file logging."""

    log_dir = config.PROJECT_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "pipeline.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
        force=True,
    )


logger = logging.getLogger(__name__)


def run_pipeline():
    """Run the complete EPL ETL pipeline."""

    start_time = datetime.now()

    logger.info("=" * 60)
    logger.info("EPL ETL PIPELINE STARTED")
    logger.info("League ID: %s | Season: %s", config.LEAGUE_ID, config.SEASON)
    logger.info("=" * 60)

    try:
        # 1. Extract
        logger.info("STEP 1: Extracting API data")
        raw_datasets = extract.extract_all()

        # 2. Transform
        logger.info("STEP 2: Transforming extracted data")
        transformed_datasets = transform.transform_all(raw_datasets)

        # 3. Validate
        logger.info("STEP 3: Validating transformed data")
        validate.validate_all(transformed_datasets)

        # 4. Load staging
        logger.info("STEP 4: Loading staging tables")
        staging_summary = load_staging.load_staging(transformed_datasets)
        logger.info("Staging load summary: %s", staging_summary)

        # 5. Load warehouse
        logger.info("STEP 5: Loading warehouse")
        warehouse_summary = load_warehouse.load_warehouse()

        # 6. Audit warehouse
        logger.info("STEP 6: Auditing warehouse")
        audit_results = audit.run_warehouse_audit()

        if not audit_results["audit_passed"]:
            raise RuntimeError("Warehouse audit failed. Review the audit results.")

        elapsed_seconds = (datetime.now() - start_time).total_seconds()

        summary = {
            "status": "SUCCESS",
            "season": config.SEASON,
            "staging_load": staging_summary,
            "warehouse_load": warehouse_summary,
            "warehouse_audit": audit_results,
            "duration_seconds": round(elapsed_seconds, 2),
        }

        logger.info("=" * 60)
        logger.info("EPL ETL PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("Duration: %.2f seconds", elapsed_seconds)
        logger.info("=" * 60)

        return summary

    except Exception:
        logger.exception("EPL ETL PIPELINE FAILED")
        raise


if __name__ == "__main__":
    setup_logging()
    result = run_pipeline()

    print("\nEPL ETL PIPELINE SUMMARY")
    print("=" * 40)
    print(f"Status: {result['status']}")
    print(f"Season: {result['season']}")
    print(f"Duration: {result['duration_seconds']} seconds")
    print(f"Warehouse load: {result['warehouse_load']}")
    print(f"Audit passed: {result['warehouse_audit']['audit_passed']}")
