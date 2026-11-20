import time
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone

import json
import logging
from datetime import datetime, timezone

import requests

from src.config import (
    API_KEY,
    BASE_URL,
    LEAGUE_ID,
    SEASON,
    REQUEST_TIMEOUT,
    RAW_DIR,
)


# ==================================================
# LOGGING
# ==================================================

logger = logging.getLogger(__name__)


# ==================================================
# API HEADERS
# ==================================================

HEADERS = {
    "x-apisports-key": API_KEY
}


# ==================================================
# API REQUEST FUNCTION
# ==================================================


def fetch_api_data(endpoint, params, max_attempts=3):
    """
    Fetch API data with controlled retries for temporary failures.
    """

    url = f"{BASE_URL}/{endpoint}"

    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.get(
                url,
                headers=HEADERS,
                params=params,
                timeout=REQUEST_TIMEOUT,
            )

            # Retry temporary server errors and rate limits.
            if response.status_code == 429 or response.status_code in {
                500, 502, 503, 504
            }:
                if attempt == max_attempts:
                    response.raise_for_status()

                retry_after = response.headers.get("Retry-After")
                delay = 2 ** (attempt - 1)

                if retry_after:
                    try:
                        delay = max(0, int(retry_after))
                    except ValueError:
                        try:
                            retry_date = parsedate_to_datetime(retry_after)
                            delay = max(
                                0,
                                int(
                                    (
                                        retry_date
                                        - datetime.now(timezone.utc)
                                    ).total_seconds()
                                ),
                            )
                        except (TypeError, ValueError, OverflowError):
                            pass

                logger.warning(
                    "Temporary HTTP error %s for %s. "
                    "Attempt %s/%s; retrying in %s seconds.",
                    response.status_code,
                    endpoint,
                    attempt,
                    max_attempts,
                    delay,
                )

                time.sleep(delay)
                continue

            # Other HTTP errors should stop immediately.
            response.raise_for_status()

            data = response.json()

            # Check API-level errors, even when HTTP status is 200.
            if data.get("errors"):
                raise RuntimeError(
                    f"API returned errors for endpoint '{endpoint}': "
                    f"{data['errors']}"
                )

            logger.info(
                "Fetched endpoint=%s, results=%s",
                endpoint,
                data.get("results", "unknown"),
            )

            return data

        except requests.exceptions.HTTPError:
            # HTTP errors are not automatically retried here.
            logger.exception(
                "Non-retryable or final HTTP error for '%s'",
                endpoint,
            )
            raise

        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        ):
            if attempt == max_attempts:
                logger.exception(
                    "Request failed after %s attempts: %s",
                    max_attempts,
                    endpoint,
                )
                raise

            delay = 2 ** (attempt - 1)

            logger.warning(
                "Network failure for %s. Attempt %s/%s; "
                "retrying in %s seconds.",
                endpoint,
                attempt,
                max_attempts,
                delay,
            )

            time.sleep(delay)

    raise RuntimeError(
        f"Request failed for endpoint '{endpoint}' after {max_attempts} attempts."
    )



# ==================================================
# SAVE RAW JSON
# ==================================================

def save_raw_json(data, dataset_name):
    """
    Save an unmodified API response as a timestamped JSON file.
    """

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    file_path = RAW_DIR / (
        f"{dataset_name}_{SEASON}_{timestamp}.json"
    )

    with file_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

    logger.info("Saved raw response to %s", file_path)

    return file_path


# ==================================================
# EXTRACT EPL DATASETS
# ==================================================

def extract_teams():
    data = fetch_api_data(
        "teams",
        {
            "league": LEAGUE_ID,
            "season": SEASON,
        },
    )

    save_raw_json(data, "teams")
    return data


def extract_fixtures():
    data = fetch_api_data(
        "fixtures",
        {
            "league": LEAGUE_ID,
            "season": SEASON,
        },
    )

    save_raw_json(data, "fixtures")
    return data


def extract_standings():
    data = fetch_api_data(
        "standings",
        {
            "league": LEAGUE_ID,
            "season": SEASON,
        },
    )

    save_raw_json(data, "standings")
    return data


def extract_all():
    """
    Extract all three datasets and return them together.
    """

    logger.info(
        "Starting EPL extraction for season %s",
        SEASON,
    )

    datasets = {
        "teams": extract_teams(),
        "fixtures": extract_fixtures(),
        "standings": extract_standings(),
    }

    logger.info("EPL extraction completed successfully")

    return datasets
