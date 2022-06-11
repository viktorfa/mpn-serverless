from datetime import datetime, timedelta
import logging
from pprint import pprint
from typing import List
from amp_types.amp_product import HandleConfig, PriceHistoryForOffer, PriceHistoryRecord
from statistics import StatisticsError, mean

from util.helpers import get_difference_percentage


def get_price_difference_update_set(
    price_history: PriceHistoryForOffer, config: HandleConfig, current_price: float
):
    scrape_time = config["scrape_time"]
    scrape_time_string = scrape_time.strftime("%Y-%m-%d")
    scrape_time_minus_7_days = scrape_time - timedelta(days=7)
    scrape_time_minus_30_days = scrape_time - timedelta(days=30)
    scrape_time_minus_90_days = scrape_time - timedelta(days=90)
    scrape_time_minus_365_days = scrape_time - timedelta(days=365)
    scrape_time_minus_7_days_string = scrape_time_minus_7_days.strftime("%Y-%m-%d")
    scrape_time_minus_30_days_string = scrape_time_minus_30_days.strftime("%Y-%m-%d")
    scrape_time_minus_90_days_string = scrape_time_minus_90_days.strftime("%Y-%m-%d")
    scrape_time_minus_365_days_string = scrape_time_minus_365_days.strftime("%Y-%m-%d")

    sorted_price_history = sorted(price_history["history"], key=lambda x: x["date"])
    last_365_days_prices = list(
        x
        for x in sorted_price_history
        if x["date"] >= scrape_time_minus_365_days_string
        and x["date"] < scrape_time_string
    )
    last_90_days_prices = list(
        x
        for x in last_365_days_prices
        if x["date"] >= scrape_time_minus_90_days_string
        and x["date"] < scrape_time_string
    )
    last_30_days_prices = list(
        x
        for x in last_90_days_prices
        if x["date"] >= scrape_time_minus_30_days_string
        and x["date"] < scrape_time_string
    )
    last_7_days_prices = list(
        x
        for x in last_30_days_prices
        if x["date"] >= scrape_time_minus_7_days_string
        and x["date"] < scrape_time_string
    )

    update_set = {
        "siteCollection": config["collection_name"],
        "updatedAt": scrape_time,
        "latestPrice": current_price,
        "difference": 0,
        "differencePercentage": 0,
        "price7DaysMean": 0,
        "difference7DaysMean": 0,
        "difference7DaysMeanPercentage": 0,
        "price30DaysMean": 0,
        "difference30DaysMean": 0,
        "difference30DaysMeanPercentage": 0,
        "price90DaysMean": 0,
        "difference90DaysMean": 0,
        "difference90DaysMeanPercentage": 0,
        "price365DaysMean": 0,
        "difference365DaysMean": 0,
        "difference365DaysMeanPercentage": 0,
    }
    if len(sorted_price_history) > 0:
        previous_pricing = sorted_price_history[-1]
        earliest_pricing = sorted_price_history[0]
        if scrape_time_string > previous_pricing["date"] or True:
            price_difference = current_price - previous_pricing["price"]
            price_difference_percentage = get_difference_percentage(
                previous_pricing["price"], current_price
            )

            update_set["difference"] = price_difference
            update_set["differencePercentage"] = price_difference_percentage

            if (
                len(last_7_days_prices) > 0
                and earliest_pricing["date"] <= scrape_time_minus_7_days_string
            ):
                differences = get_differences_for_series(
                    last_7_days_prices, current_price
                )
                update_set["price7DaysMean"] = differences["mean"]
                update_set["difference7DaysMean"] = differences["difference"]
                update_set["difference7DaysMeanPercentage"] = differences[
                    "differencePercentage"
                ]

            if (
                len(last_30_days_prices) > 0
                and earliest_pricing["date"] <= scrape_time_minus_30_days_string
            ):
                differences = get_differences_for_series(
                    last_30_days_prices, current_price
                )
                update_set["price30DaysMean"] = differences["mean"]
                update_set["difference30DaysMean"] = differences["difference"]
                update_set["difference30DaysMeanPercentage"] = differences[
                    "differencePercentage"
                ]
            if (
                len(last_90_days_prices) > 0
                and earliest_pricing["date"] <= scrape_time_minus_90_days_string
            ):
                differences = get_differences_for_series(
                    last_90_days_prices, current_price
                )
                update_set["price90DaysMean"] = differences["mean"]
                update_set["difference90DaysMean"] = differences["difference"]
                update_set["difference90DaysMeanPercentage"] = differences[
                    "differencePercentage"
                ]
            if (
                len(last_365_days_prices) > 0
                and earliest_pricing["date"] <= scrape_time_minus_365_days_string
            ):
                differences = get_differences_for_series(
                    last_365_days_prices, current_price
                )
                update_set["price365DaysMean"] = differences["mean"]
                update_set["difference365DaysMean"] = differences["difference"]
                update_set["difference365DaysMeanPercentage"] = differences[
                    "differencePercentage"
                ]
    return update_set


def get_differences_for_series(prices: List[PriceHistoryRecord], current_price: float):
    mean_price = mean(x["price"] for x in prices)
    difference = current_price - mean_price
    difference_percentage = get_difference_percentage(mean_price, current_price)

    return {
        "mean": mean_price,
        "difference": difference,
        "differencePercentage": difference_percentage,
    }
