import json
import os
import logging
import pydash
from pymongo.operations import UpdateOne
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

from storage.db import get_collection

logger = logging.getLogger()
logging.getLogger("botocore").setLevel(logging.WARNING)
logging.getLogger("boto3").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
if os.getenv("IS_LOCAL"):
    logging.basicConfig(level=logging.DEBUG)
    logger.setLevel(logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)
    logger.setLevel(logging.INFO)

SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]
KEY_FILE_LOCATION = "scraper_feed/google_anal/_SECRET_mpnmpn-779aa439f931.json"

sites = {
    "bygg-de": {"view_id": "250610345", "offer_string": "/angebote/"},
    "amp-de": {"view_id": "250230468", "offer_string": "/angebote/"},
    "amp-dk": {"view_id": "252921853", "offer_string": "/tilbud/"},
    "bygg-dk": {"view_id": "252899683", "offer_string": "/tilbud/"},
    "bygg-no": {"view_id": "209692000", "offer_string": "/tilbud/"},
    "beauty-no": {"view_id": "239885466", "offer_string": "/tilbud/"},
    "amp-no": {"view_id": "187893382", "offer_string": "/tilbud/"},
    "bygg-se": {"view_id": "234405434", "offer_string": "/erbjudande/"},
    "beauty-se": {"view_id": "240724194", "offer_string": "/erbjudande/"},
    "amp-se": {"view_id": "234437137", "offer_string": "/erbjudande/"},
    "bygg-uk": {"view_id": "252885276", "offer_string": "/offers/"},
    "beauty-uk": {"view_id": "252859573", "offer_string": "/offers/"},
    "amp-uk": {"view_id": "252812272", "offer_string": "/offers/"},
    "bygg-us": {"view_id": "252892165", "offer_string": "/offers/"},
    "beauty-us": {"view_id": "252892678", "offer_string": "/offers/"},
    "amp-us": {"view_id": "252904698", "offer_string": "/offers/"},
}


def initialize_analyticsreporting():
    """Initializes an Analytics Reporting API V4 service object.

    Returns:
      An authorized Analytics Reporting API V4 service object.
    """
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        KEY_FILE_LOCATION, SCOPES
    )

    # Build the service object.
    analytics = build("analyticsreporting", "v4", credentials=credentials)

    return analytics


def get_report(analytics, view_id, offer_string, page_size=6000):
    """Queries the Analytics Reporting API V4.

    Args:
      analytics: An authorized Analytics Reporting API V4 service object.
    Returns:
      The Analytics Reporting API V4 response.
    """
    return (
        analytics.reports()
        .batchGet(
            body={
                "reportRequests": [
                    {
                        "viewId": view_id,
                        "dateRanges": [{"startDate": "yesterday", "endDate": "today"}],
                        "metrics": [{"expression": "ga:pageviews"}],
                        "dimensions": [
                            {"name": "ga:pagepath"},
                            {"name": "ga:dateHour"},
                        ],
                        "orderBys": [
                            {"fieldName": "ga:pageviews", "sortOrder": "DESCENDING"},
                        ],
                        "pageSize": str(page_size),
                        "dimensionFilterClauses": [
                            {
                                "filters": [
                                    {
                                        "dimensionName": "ga:pagepath",
                                        "operator": "PARTIAL",
                                        "expressions": ["/offers/"],
                                    },
                                    {
                                        "dimensionName": "ga:pagepath",
                                        "operator": "PARTIAL",
                                        "expressions": ["/tilbud/"],
                                    },
                                    {
                                        "dimensionName": "ga:pagepath",
                                        "operator": "PARTIAL",
                                        "expressions": ["/angebote/"],
                                    },
                                    {
                                        "dimensionName": "ga:pagepath",
                                        "operator": "PARTIAL",
                                        "expressions": ["/erbjudande/"],
                                    },
                                ]
                            }
                        ],
                    }
                ]
            }
        )
        .execute()
    )


def get_latest_uri_pageviews_from_response(response, max_uris=1024):
    reports = response.get("reports", [])

    grouped_by_hour = pydash.group_by(
        reports[0].get("data", {}).get("rows", []), "dimensions.1"
    )
    hours = sorted(list(grouped_by_hour.keys()), reverse=True)

    result = {}
    for hour in hours[:]:
        for measure in grouped_by_hour[hour]:
            url = measure["dimensions"][0]
            uri = f"{url}/".replace("//", "/").split("/")[-2]
            pageviews = int(measure["metrics"][0]["values"][0])
            if url in result.keys():
                result[uri] += pageviews
            else:
                result[uri] = pageviews
        if len(result.keys()) >= max_uris:
            logging.info(f"Got {max_uris} uris. Stopping")
            return result
    return result


def save_mongo_pageviews(uri_pageviews):
    collection = get_collection("mpnoffers")

    updates = list(
        UpdateOne({"uri": uri}, {"$set": {"pageviews": pageviews}})
        for uri, pageviews in uri_pageviews.items()
    )

    bulk_write_result = collection.bulk_write(updates)

    return bulk_write_result.modified_count


def get_and_save_pageviews(max_pages=6000):
    analytics = initialize_analyticsreporting()

    reports = []

    for site_key, site_config in sites.items():
        response = get_report(
            analytics, site_config["view_id"], site_config["offer_string"], max_pages
        )
        uri_pageviews = get_latest_uri_pageviews_from_response(response)
        reports.append(
            {
                "uri_pageviews": uri_pageviews,
                "site_config": site_config,
                "site_key": site_key,
            }
        )

    result = []
    for report in reports:
        uri_pageviews = report["uri_pageviews"]
        mongo_modified = (
            save_mongo_pageviews(uri_pageviews) if len(uri_pageviews) > 0 else 0
        )
        result.append({"mongo_modified": mongo_modified, "site": report["site_key"]})

    logging.info("Modified offers")
    logging.info(result)

    return result


def handle(event, context):
    max_pages = event.get("max_pages", 6000)
    return get_and_save_pageviews(max_pages)


if __name__ == "__main__":
    get_and_save_pageviews()
