import os
import logging
import pydash
from pymongo.operations import UpdateOne
import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration
from google.analytics import data_v1beta
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Filter,
    FilterExpression,
    Metric,
    OrderBy,
)
from typing import Mapping

from scraper_feed.google_anal.utils import (
    sites,
    initialize_analyticsreporting,
    get_analytics_data_client,
)

from storage.db import get_collection
from util.logging import configure_lambda_logging
from offer_feed.offer_relations_handler import update_offer_relations_view

if not os.getenv("IS_LOCAL"):
    sentry_sdk.init(
        integrations=[AwsLambdaIntegration()],
    )


configure_lambda_logging()


def get_report_ga4(
    client: data_v1beta.BetaAnalyticsDataClient,
    property_id: str,
    offer_string: str,
    page_size=6000,
):
    logging.info(f"offer_string: {offer_string}")

    request = data_v1beta.RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[
            DateRange(start_date="yesterday", end_date="today"),
        ],
        metrics=[Metric(name="screenPageViews")],
        dimensions=[Dimension(name="date"), Dimension(name="pagePath")],
        dimension_filter=FilterExpression(
            filter=Filter(
                field_name="pagePath",
                string_filter=Filter.StringFilter(
                    value=f"{offer_string}",
                    match_type=Filter.StringFilter.MatchType.CONTAINS,
                ),
            )
        ),
        limit=page_size,
        order_bys=[
            OrderBy(
                metric=OrderBy.MetricOrderBy(metric_name="screenPageViews"), desc=True
            )
        ],
    )
    report = client.run_report(request=request)
    uri_to_views_map: Mapping[str, int] = {}
    for row in report.rows:
        path: str = row.dimension_values[1].value
        views = int(row.metric_values[0].value)
        uri = list(x for x in path.replace("%3A", ":").split("/") if x)[-1]

        if not uri:
            continue

        if uri in uri_to_views_map.keys():
            uri_to_views_map[uri] += views
        else:
            uri_to_views_map[uri] = views
    return uri_to_views_map


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


def save_mongo_pageviews(uri_pageviews: Mapping[str, int]):
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
        if not site_config.get("view_id"):
            continue
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


def get_and_save_pageviews_ga4(max_pages=6000):
    client = get_analytics_data_client()

    reports = []

    for site_key, site_config in sites.items():
        if not site_config.get("property_id"):
            continue
        logging.info(f"Getting report for {site_key}")

        uri_pageviews = get_report_ga4(
            client,
            site_config["property_id"],
            site_config["offer_string"],
            max_pages,
        )

        reports.append(
            {
                "uri_pageviews": uri_pageviews,
                "site_config": site_config,
                "site_key": site_key,
            }
        )

    result = []
    logging.info("reports")
    logging.info(reports)

    for report in reports:
        uri_pageviews = report["uri_pageviews"]
        mongo_modified = (
            save_mongo_pageviews(uri_pageviews) if len(uri_pageviews) > 0 else 0
        )
        update_offer_relations_view_response = update_offer_relations_view(
            {"offerSet": {"$in": list(uri_pageviews.keys())}},
            market=report["site_config"]["market"],
        )
        logging.info("update_offer_relations_view_response")
        logging.info(update_offer_relations_view_response)
        result.append({"mongo_modified": mongo_modified, "site": report["site_key"]})

    logging.info("Modified offers")
    logging.info(result)

    return result


def handle(event, context):
    max_pages = event.get("max_pages", 6000)
    return get_and_save_pageviews(max_pages)


def handle_ga4(event, context):
    max_pages = event.get("max_pages", 6000)
    return get_and_save_pageviews_ga4(max_pages)


if __name__ == "__main__":
    # get_and_save_pageviews()
    get_and_save_pageviews_ga4()
