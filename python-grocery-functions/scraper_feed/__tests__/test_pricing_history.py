from datetime import datetime
from unittest import TestCase

from scraper_feed.pricing_history import (
    get_differences_for_series,
    get_price_difference_update_set,
)


class TestPriceDifferencesUpdateSet(TestCase):
    def test_basic(self):
        history_object = {"history": [{"price": 20, "date": "2022-05-20"}]}
        current_price = 20
        scrape_time = datetime(year=2022, month=5, day=31)
        config = {
            "collection_name": "groceryoffers",
            "scrape_time": scrape_time,
        }
        print('config["scrape_time"]')
        print(config["scrape_time"])
        actual = get_price_difference_update_set(history_object, config, current_price)
        print("update_set")
        print(actual)
        self.assertEqual(actual["updatedAt"], scrape_time)
        self.assertAlmostEqual(actual["difference"], 0)
        self.assertAlmostEqual(actual["differencePercentage"], 0)
        self.assertAlmostEqual(actual["price7DaysMean"], 0)
        self.assertAlmostEqual(actual["difference7DaysMean"], 0)
        self.assertAlmostEqual(actual["difference7DaysMeanPercentage"], 0)
        self.assertAlmostEqual(actual["price30DaysMean"], 0)
        self.assertAlmostEqual(actual["difference30DaysMean"], 0)
        self.assertAlmostEqual(actual["difference30DaysMeanPercentage"], 0)
        self.assertAlmostEqual(actual["price365DaysMean"], 0)
        self.assertAlmostEqual(actual["difference365DaysMean"], 0)
        self.assertAlmostEqual(actual["difference365DaysMeanPercentage"], 0)

    def test_with_7_days_history(self):
        history_object = {
            "history": [
                {"price": 20, "date": "2022-05-20"},
                {"price": 20, "date": "2022-05-28"},
            ]
        }
        current_price = 20
        scrape_time = datetime(year=2022, month=5, day=31)
        config = {
            "collection_name": "groceryoffers",
            "scrape_time": scrape_time,
        }
        print('config["scrape_time"]')
        print(config["scrape_time"])
        actual = get_price_difference_update_set(history_object, config, current_price)
        print("update_set")
        print(actual)
        self.assertEqual(actual["updatedAt"], scrape_time)
        self.assertAlmostEqual(actual["difference"], 0)
        self.assertAlmostEqual(actual["differencePercentage"], 0)
        self.assertAlmostEqual(actual["price7DaysMean"], 20)
        self.assertAlmostEqual(actual["difference7DaysMean"], 0)
        self.assertAlmostEqual(actual["difference7DaysMeanPercentage"], 0)
        self.assertAlmostEqual(actual["price30DaysMean"], 0)
        self.assertAlmostEqual(actual["difference30DaysMean"], 0)
        self.assertAlmostEqual(actual["difference30DaysMeanPercentage"], 0)
        self.assertAlmostEqual(actual["price365DaysMean"], 0)
        self.assertAlmostEqual(actual["difference365DaysMean"], 0)
        self.assertAlmostEqual(actual["difference365DaysMeanPercentage"], 0)

    def test_with_90_days_history_and_difference(self):
        history_object = {
            "history": [
                {"price": 57, "date": "2022-05-20"},
                {"price": 57, "date": "2022-05-18"},
                {"price": 57, "date": "2022-05-16"},
                {"price": 57, "date": "2022-05-14"},
                {"price": 57, "date": "2022-05-12"},
                {"price": 57, "date": "2022-05-10"},
                {"price": 57, "date": "2022-05-08"},
                {"price": 57, "date": "2022-05-06"},
                {"price": 57, "date": "2022-05-04"},
                {"price": 57, "date": "2022-05-02"},
                {"price": 57, "date": "2022-04-30"},
                {"price": 57, "date": "2022-04-28"},
                {"price": 57, "date": "2022-04-26"},
                {"price": 57, "date": "2022-04-24"},
                {"price": 57, "date": "2022-04-22"},
                {"price": 57, "date": "2022-04-20"},
                {"price": 57, "date": "2022-04-18"},
                {"price": 57, "date": "2022-04-16"},
                {"price": 57, "date": "2022-04-14"},
                {"price": 57, "date": "2022-04-12"},
                {"price": 57, "date": "2022-04-10"},
                {"price": 57, "date": "2022-04-08"},
                {"price": 57, "date": "2022-04-06"},
                {"price": 57, "date": "2022-04-03"},
                {"price": 57, "date": "2022-04-01"},
                {"price": 57, "date": "2022-03-30"},
                {"price": 57, "date": "2022-03-28"},
                {"price": 39.8, "date": "2022-03-26"},
                {"price": 39.8, "date": "2022-03-24"},
                {"price": 39.8, "date": "2022-03-20"},
                {"price": 39.8, "date": "2022-03-18"},
                {"price": 39.8, "date": "2022-03-16"},
                {"price": 39.8, "date": "2022-03-14"},
                {"price": 39.8, "date": "2022-03-12"},
                {"price": 39.8, "date": "2022-03-10"},
                {"price": 49.1, "date": "2022-01-14"},
                {"price": 49.1, "date": "2022-01-13"},
                {"price": 49.1, "date": "2022-01-11"},
                {"price": 49.1, "date": "2022-01-09"},
                {"price": 49.1, "date": "2022-01-07"},
                {"price": 49.1, "date": "2022-01-05"},
                {"price": 44.8, "date": "2022-01-03"},
                {"price": 44.8, "date": "2022-01-01"},
                {"price": 43.9, "date": "2021-12-30"},
                {"price": 43.9, "date": "2021-12-28"},
                {"price": 49.1, "date": "2021-12-26"},
                {"price": 43.9, "date": "2021-12-23"},
                {"price": 43.9, "date": "2021-12-21"},
                {"price": 43.9, "date": "2021-12-19"},
                {"price": 43.9, "date": "2021-12-17"},
                {"price": 43.9, "date": "2021-12-15"},
                {"price": 43.9, "date": "2021-12-13"},
                {"price": 43.9, "date": "2021-12-11"},
                {"price": 43.9, "date": "2021-12-09"},
                {"price": 43.9, "date": "2021-11-29"},
                {"price": 43.9, "date": "2021-11-25"},
                {"price": 49.1, "date": "2021-11-23"},
                {"price": 49.1, "date": "2021-10-25"},
                {"price": 49.1, "date": "2021-10-23"},
                {"price": 49.1, "date": "2021-10-21"},
                {"price": 49.1, "date": "2021-10-19"},
                {"price": 49.1, "date": "2021-10-17"},
                {"price": 49.1, "date": "2021-10-15"},
                {"price": 49.1, "date": "2021-10-11"},
                {"price": 57, "date": "2022-05-24"},
            ],
        }
        current_price = 57
        scrape_time = datetime(year=2022, month=5, day=24)
        config = {
            "collection_name": "groceryoffers",
            "scrape_time": scrape_time,
        }
        print('config["scrape_time"]')
        print(config["scrape_time"])
        actual = get_price_difference_update_set(history_object, config, current_price)
        print("update_set")
        print(actual)
        self.assertEqual(actual["updatedAt"], scrape_time)
        self.assertAlmostEqual(actual["difference"], 0)
        self.assertAlmostEqual(actual["differencePercentage"], 0)
        self.assertNotAlmostEqual(actual["price90DaysMean"], 0)

    def test_with_30_days_history_and_difference(self):
        history_object = {
            "history": [
                {"price": 18, "date": "2022-04-28"},
                {"price": 18, "date": "2022-05-02"},
                {"price": 20, "date": "2022-05-12"},
                {"price": 20, "date": "2022-05-20"},
                {"price": 19, "date": "2022-05-28"},
            ]
        }
        current_price = 20
        scrape_time = datetime(year=2022, month=5, day=31)
        config = {
            "collection_name": "groceryoffers",
            "scrape_time": scrape_time,
        }
        print('config["scrape_time"]')
        print(config["scrape_time"])
        actual = get_price_difference_update_set(history_object, config, current_price)
        print("update_set")
        print(actual)
        self.assertEqual(actual["updatedAt"], scrape_time)
        self.assertAlmostEqual(actual["difference"], 1)
        self.assertAlmostEqual(actual["differencePercentage"], 5.263157894736842)
        self.assertAlmostEqual(actual["price7DaysMean"], 19)
        self.assertAlmostEqual(actual["difference7DaysMean"], 1)
        self.assertAlmostEqual(
            actual["difference7DaysMeanPercentage"], 5.263157894736842
        )
        self.assertAlmostEqual(actual["price30DaysMean"], 19.25)
        self.assertAlmostEqual(actual["difference30DaysMean"], 0.75)
        self.assertAlmostEqual(
            actual["difference30DaysMeanPercentage"], 3.896103896103896
        )
        self.assertAlmostEqual(actual["price365DaysMean"], 0)
        self.assertAlmostEqual(actual["difference365DaysMean"], 0)
        self.assertAlmostEqual(actual["difference365DaysMeanPercentage"], 0)


class TestPriceDifferencesForSeries(TestCase):
    def test_basic(self):
        series = [{"price": 20}]
        current_price = 20
        actual = get_differences_for_series(series, current_price)

        self.assertAlmostEqual(actual["mean"], 20)
        self.assertAlmostEqual(actual["difference"], 0)
        self.assertAlmostEqual(actual["differencePercentage"], 0)

    def test_with_multiple_values(self):
        series = [{"price": 10}, {"price": 12}]
        current_price = 20
        actual = get_differences_for_series(series, current_price)

        self.assertAlmostEqual(actual["mean"], 11)
        self.assertAlmostEqual(actual["difference"], 9)
        self.assertAlmostEqual(actual["differencePercentage"], 81.81818181818183)
