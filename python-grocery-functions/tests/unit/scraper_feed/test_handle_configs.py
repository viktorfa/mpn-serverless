from unittest import TestCase, mock

from storage.postgres.scraper_feed import get_handle_configs
from storage.postgres.postgres_tables import HandleConfigsTable
from util.errors import NoHandleConfigError


class TestHandleConfig(TestCase):
    @mock.patch('storage.postgres.scraper_feed.Session')
    @mock.patch('storage.postgres.scraper_feed.pg_engine')
    def test_get_handle_config(self, mock_pg_engine, mock_session_class):
        # Mock the session and query
        mock_session = mock.MagicMock()
        mock_session_class.return_value.__enter__.return_value = mock_session

        # Mock the query result
        mock_config = mock.MagicMock(spec=HandleConfigsTable)
        mock_config.provenance = "shopgun"
        mock_config.context = "amp-no"
        mock_config.market = "no"
        mock_config.namespace = "meny"

        mock_stmt = mock.MagicMock()
        mock_stmt.all.return_value = [mock_config]
        mock_session.query.return_value.filter.return_value = mock_stmt

        result = get_handle_configs("shopgun")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].provenance, "shopgun")
        self.assertEqual(result[0].market, "no")
        mock_session.query.assert_called_once_with(HandleConfigsTable)

    @mock.patch('storage.postgres.scraper_feed.Session')
    @mock.patch('storage.postgres.scraper_feed.pg_engine')
    def test_get_handle_config_without_config(self, mock_pg_engine, mock_session_class):
        # Mock the session and query to return empty result
        mock_session = mock.MagicMock()
        mock_session_class.return_value.__enter__.return_value = mock_session

        mock_stmt = mock.MagicMock()
        mock_stmt.all.return_value = []
        mock_session.query.return_value.filter.return_value = mock_stmt

        result = get_handle_configs("nonexistent")

        self.assertEqual(len(result), 0)
        mock_session.query.assert_called_once_with(HandleConfigsTable)
