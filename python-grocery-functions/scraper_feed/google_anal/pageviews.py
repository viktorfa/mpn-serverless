import os
import logging
import pydash
from pymongo.operations import UpdateOne

import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

from scraper_feed.google_anal.utils import (
    sites,
    initialize_analyticsreporting,
)

from storage.db import get_collection
from util.logging import configure_lambda_logging

if not os.getenv("IS_LOCAL"):
    sentry_sdk.init(
        integrations=[AwsLambdaIntegration()],
    )


configure_lambda_logging()


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
                                    {
                                        "dimensionName": "ga:pagepath",
                                        "operator": "PARTIAL",
                                        "expressions": ["/tarjouksia/"],
                                    },
                                    {
                                        "dimensionName": "ga:pagepath",
                                        "operator": "PARTIAL",
                                        "expressions": ["/offres/"],
                                    },
                                    {
                                        "dimensionName": "ga:pagepath",
                                        "operator": "PARTIAL",
                                        "expressions": ["/aanbiedingen/"],
                                    },
                                    {
                                        "dimensionName": "ga:pagepath",
                                        "operator": "PARTIAL",
                                        "expressions": ["/oferty/"],
                                    },
                                    {
                                        "dimensionName": "ga:pagepath",
                                        "operator": "PARTIAL",
                                        "expressions": ["/ofertas/"],
                                    },
                                    {
                                        "dimensionName": "ga:pagepath",
                                        "operator": "PARTIAL",
                                        "expressions": ["/offerte/"],
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
        logging.info(f"Getting report for {site_key}")
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
