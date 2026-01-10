import logging
from collections import defaultdict
from collections.abc import Mapping

from google.analytics import data_v1beta
from google.analytics.data_v1beta.types import DateRange, Dimension, Filter, FilterExpression, Metric, OrderBy
from sqlalchemy import select
from sqlalchemy.orm import Session

from scraper_feed.google_anal.utils import get_analytics_data_client, sites
from storage.postgres.common import get_pg_engine
from storage.postgres.postgres_tables import DenormalizedProductsTable, OffersTable
from util.logging import configure_lambda_logging

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
            # DateRange(start_date="yesterday", end_date="today"),
            DateRange(start_date="7daysAgo", end_date="today"),
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
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="screenPageViews"), desc=True)],
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


def save_postgres_pageviews(uri_pageviews: Mapping[str, int], market: str, session: Session):
    # Step 1: Fetch offers and map URIs to product IDs
    uris = list(uri_pageviews.keys())
    offers = session.query(OffersTable.uri, OffersTable.product_id).filter(OffersTable.uri.in_(uris)).all()

    logging.info(f"Found {len(offers)} offers in the database.")

    # Build a mapping from product_id to total pageviews
    product_pageviews = defaultdict(int)
    for uri, product_id in offers:
        pageviews = uri_pageviews.get(uri, 0)
        product_pageviews[product_id] += pageviews

    existing_rows = session.execute(
        select(DenormalizedProductsTable.product_id, DenormalizedProductsTable.market)
        .filter(DenormalizedProductsTable.market == market)
        .filter(DenormalizedProductsTable.product_id.in_(product_pageviews.keys()))
    ).fetchall()

    existing_pairs = {(row.product_id, row.market) for row in existing_rows}

    logging.info(f"Found {len(existing_pairs)} existing rows in the denormalized table.")

    updates = [
        {
            "product_id": product_id,
            "market": market,
            "page_views": total_pageviews,
        }
        for product_id, total_pageviews in product_pageviews.items()
        if (product_id, market) in existing_pairs
    ]

    logging.info(f"Updating {len(updates)} rows in the denormalized table.")
    if updates:
        session.bulk_update_mappings(DenormalizedProductsTable, updates)
        session.commit()
    else:
        logging.info("No updates to perform.")


def get_and_save_pageviews_ga4(max_pages=6000):
    with get_analytics_data_client() as client:
        with Session(get_pg_engine()) as session:
            try:
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
                    transformed_uri_pageviews: Mapping[str, int] = {}
                    for uri, views in uri_pageviews.items():
                        try:
                            namespace, _, sku = uri.split(":")
                            new_uri = f"{namespace}:{sku}"
                        except ValueError:
                            logging.warning(f"Could not split URI: {uri}")
                            continue
                        transformed_uri_pageviews[new_uri] = views

                    logging.info(f"Got {len(transformed_uri_pageviews)} pages from GA4 for {site_key}")

                    market = site_config["market"]
                    if transformed_uri_pageviews:
                        save_postgres_pageviews(transformed_uri_pageviews, market, session)

                logging.info("Pageviews have been updated in denormalized_products.")
                session.commit()
            except Exception as e:
                logging.error(f"An error occurred: {e}")
                session.rollback()
                raise


def handle_ga4(event, context):
    max_pages = event.get("max_pages", 6000)
    try:
        get_and_save_pageviews_ga4(max_pages)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        logging.error(e)
        raise

    return None


if __name__ == "__main__":
    # get_and_save_pageviews()
    get_and_save_pageviews_ga4()
