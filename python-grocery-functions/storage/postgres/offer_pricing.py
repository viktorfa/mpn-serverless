from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func, select, case, text
from datetime import datetime, timedelta

from storage.postgres.common import get_pg_engine
from storage.postgres.postgres_tables import OfferPricesTable, OffersTable


def update_offer_pricing(affected_offer_uris: List[str]):
    engine = get_pg_engine()
    with Session(engine) as session:
        try:
            # Define the base table
            op_table = OfferPricesTable.__table__

            # Subquery to get current prices
            op_inner = op_table.alias("op_inner")
            op_sub = op_table.alias("op_sub")

            current_prices_subq = (
                select(
                    op_sub.c.uri,
                    op_sub.c.price.label("current_price"),
                )
                .select_from(
                    select(
                        op_inner.c.uri,
                        op_inner.c.price,
                        func.row_number()
                        .over(
                            partition_by=op_inner.c.uri,
                            order_by=op_inner.c.recorded_at.desc(),
                        )
                        .label("rn"),
                    )
                    .where(op_inner.c.uri.in_(affected_offer_uris))
                    .alias("op_current")  # Use a unique alias
                )
                .where(text("op_current.rn = 1"))
                .cte("current_prices")
            )

            # Reference op_current in the select
            op_current = current_prices_subq.alias("op_current")

            # Subquery to get average prices
            op_ap = op_table.alias("op_ap")

            avg_prices_subq = (
                select(
                    op_ap.c.uri,
                    func.avg(
                        case(
                            (
                                op_ap.c.recorded_at
                                >= datetime.utcnow() - timedelta(days=7),
                                op_ap.c.price,
                            ),
                            else_=None,
                        )
                    ).label("avg_price_7_days"),
                    func.avg(
                        case(
                            (
                                op_ap.c.recorded_at
                                >= datetime.utcnow() - timedelta(days=30),
                                op_ap.c.price,
                            ),
                            else_=None,
                        )
                    ).label("avg_price_30_days"),
                    func.avg(
                        case(
                            (
                                op_ap.c.recorded_at
                                >= datetime.utcnow() - timedelta(days=90),
                                op_ap.c.price,
                            ),
                            else_=None,
                        )
                    ).label("avg_price_90_days"),
                    func.avg(
                        case(
                            (
                                op_ap.c.recorded_at
                                >= datetime.utcnow() - timedelta(days=180),
                                op_ap.c.price,
                            ),
                            else_=None,
                        )
                    ).label("avg_price_180_days"),
                    func.avg(
                        case(
                            (
                                op_ap.c.recorded_at
                                >= datetime.utcnow() - timedelta(days=365),
                                op_ap.c.price,
                            ),
                            else_=None,
                        )
                    ).label("avg_price_365_days"),
                )
                .where(op_ap.c.uri.in_(affected_offer_uris))
                .group_by(op_ap.c.uri)
                .cte("avg_prices")
            )

            # Main query to compute differences
            main_query = select(
                current_prices_subq.c.uri,
                current_prices_subq.c.current_price,
                avg_prices_subq.c.avg_price_7_days,
                avg_prices_subq.c.avg_price_30_days,
                avg_prices_subq.c.avg_price_90_days,
                (
                    current_prices_subq.c.current_price
                    - avg_prices_subq.c.avg_price_7_days
                ).label("difference_7_days_mean"),
                (
                    (
                        current_prices_subq.c.current_price
                        - avg_prices_subq.c.avg_price_7_days
                    )
                    / func.nullif(avg_prices_subq.c.avg_price_7_days, 0)
                    * 100
                ).label("difference_7_days_mean_percentage"),
                (
                    current_prices_subq.c.current_price
                    - avg_prices_subq.c.avg_price_30_days
                ).label("difference_30_days_mean"),
                (
                    (
                        current_prices_subq.c.current_price
                        - avg_prices_subq.c.avg_price_30_days
                    )
                    / func.nullif(avg_prices_subq.c.avg_price_30_days, 0)
                    * 100
                ).label("difference_30_days_mean_percentage"),
                (
                    current_prices_subq.c.current_price
                    - avg_prices_subq.c.avg_price_90_days
                ).label("difference_90_days_mean"),
                (
                    (
                        current_prices_subq.c.current_price
                        - avg_prices_subq.c.avg_price_90_days
                    )
                    / func.nullif(avg_prices_subq.c.avg_price_90_days, 0)
                    * 100
                ).label("difference_90_days_mean_percentage"),
                (
                    current_prices_subq.c.current_price
                    - avg_prices_subq.c.avg_price_180_days
                ).label("difference_180_days_mean"),
                (
                    (
                        current_prices_subq.c.current_price
                        - avg_prices_subq.c.avg_price_180_days
                    )
                    / func.nullif(avg_prices_subq.c.avg_price_180_days, 0)
                    * 100
                ).label("difference_180_days_mean_percentage"),
                (
                    current_prices_subq.c.current_price
                    - avg_prices_subq.c.avg_price_365_days
                ).label("difference_365_days_mean"),
                (
                    (
                        current_prices_subq.c.current_price
                        - avg_prices_subq.c.avg_price_365_days
                    )
                    / func.nullif(avg_prices_subq.c.avg_price_365_days, 0)
                    * 100
                ).label("difference_365_days_mean_percentage"),
            ).select_from(
                current_prices_subq.join(
                    avg_prices_subq, current_prices_subq.c.uri == avg_prices_subq.c.uri
                )
            )

            # Execute the query and fetch results
            results = session.execute(main_query).fetchall()

            # Prepare a mapping of uri to computed values
            price_diffs_map = {
                row.uri: {
                    "difference_7_days_mean": row.difference_7_days_mean,
                    "difference_7_days_mean_percentage": row.difference_7_days_mean_percentage,
                    "difference_30_days_mean": row.difference_30_days_mean,
                    "difference_30_days_mean_percentage": row.difference_30_days_mean_percentage,
                    "difference_90_days_mean": row.difference_90_days_mean,
                    "difference_90_days_mean_percentage": row.difference_90_days_mean_percentage,
                    "difference_180_days_mean": row.difference_180_days_mean,
                    "difference_180_days_mean_percentage": row.difference_180_days_mean_percentage,
                    "difference_365_days_mean": row.difference_365_days_mean,
                    "difference_365_days_mean_percentage": row.difference_365_days_mean_percentage,
                }
                for row in results
            }

            updates = [
                {
                    "uri": uri,
                    "difference_7_days_mean": diffs["difference_7_days_mean"],
                    "difference_7_days_mean_percentage": diffs[
                        "difference_7_days_mean_percentage"
                    ],
                    "difference_30_days_mean": diffs["difference_30_days_mean"],
                    "difference_30_days_mean_percentage": diffs[
                        "difference_30_days_mean_percentage"
                    ],
                    "difference_90_days_mean": diffs["difference_90_days_mean"],
                    "difference_90_days_mean_percentage": diffs[
                        "difference_90_days_mean_percentage"
                    ],
                    "difference_180_days_mean": diffs["difference_180_days_mean"],
                    "difference_180_days_mean_percentage": diffs[
                        "difference_180_days_mean_percentage"
                    ],
                    "difference_365_days_mean": diffs["difference_365_days_mean"],
                    "difference_365_days_mean_percentage": diffs[
                        "difference_365_days_mean_percentage"
                    ],
                }
                for uri, diffs in price_diffs_map.items()
            ]

            # Bulk update offers
            session.bulk_update_mappings(
                OffersTable,
                updates,
            )

            session.commit()

        except Exception as e:
            session.rollback()
            print(f"An error occurred: {e}")
            raise e
