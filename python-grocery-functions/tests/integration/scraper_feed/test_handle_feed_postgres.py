"""
Integration tests for handle_feed_with_config_postgres - the core feed processing function.

This function orchestrates the entire feed processing pipeline:
- JSON stream parsing
- Offer transformation and filtering
- Batch processing (1000 items per batch)
- Database storage operations
- Error handling

These are integration tests that test the complete workflow using real test data,
but with mocked database operations to avoid external dependencies.
"""

import os
from unittest.mock import patch

import pytest

from scraper_feed.handle_feed_postgres import handle_feed_with_config_postgres
from tests.integration.scraper_feed.conftest import create_mock_stream


# Mock all database operations at the module level
@pytest.fixture(autouse=True)
def mock_database_calls():
    """Automatically mock all database operations for these tests."""
    with (
        patch("scraper_feed.handle_feed_postgres.insert_handle_run_batch") as mock_insert,
        patch("scraper_feed.handle_feed_postgres.handle_store_offer_batch") as mock_store,
        patch("scraper_feed.handle_feed_postgres.update_handle_run_batch_status") as mock_update,
    ):
        # Configure realistic return values
        mock_insert.return_value = "test-batch-run-id"
        mock_store.return_value = None  # void function
        mock_update.return_value = None  # void function

        yield {"insert_batch": mock_insert, "store_batch": mock_store, "update_status": mock_update}


class TestHandleFeedWithConfigPostgres:
    """Integration tests for the core feed processing function."""

    @patch.dict(os.environ, {"STAGE": "test"})
    def test_handle_small_feed_success(self, gottebiten_feed_data, gottebiten_config, mock_database_calls):
        """Test successful processing of a small feed (gottebiten ~20 offers)."""
        # Arrange
        feed_stream = create_mock_stream(gottebiten_feed_data)

        # Act
        result = handle_feed_with_config_postgres(feed_stream, gottebiten_config)

        # Assert - Check return value structure
        assert isinstance(result, dict)
        assert "items_handled" in result
        assert "n_filtered_offers" in result
        assert result["items_handled"] > 0
        assert result["n_filtered_offers"] >= 0

        # Assert - Verify database operations were called
        mocks = mock_database_calls
        mocks["insert_batch"].assert_called_once()
        mocks["update_status"].assert_called_once_with("test-batch-run-id", "COMPLETED")

        # Assert - Verify batch insertion was called (if there were offers to store)
        if result["n_filtered_offers"] > 0:
            assert mocks["store_batch"].call_count >= 1

        # Assert - Check that batch was called with correct parameters (if there were offers to store)
        if result["n_filtered_offers"] > 0:
            store_calls = mocks["store_batch"].call_args_list
            assert len(store_calls) > 0, "Expected store_batch to be called when there are filtered offers"

            for call in store_calls:
                args, kwargs = call

                # The function is called with keyword arguments
                if args:
                    offers, scrape_time, context = args
                else:
                    offers = kwargs["offers"]
                    scrape_time = kwargs["scrape_time"]
                    context = kwargs["context"]

                assert isinstance(offers, list)
                assert len(offers) > 0
                assert scrape_time == gottebiten_config.scrape_time
                assert context == gottebiten_config.context

                # Verify offer structure (transformed offers should have required fields)
                for offer in offers:
                    assert "context" in offer
                    assert "scrapeBatchId" in offer
                    assert "namespace" in offer
                    assert offer["context"] == gottebiten_config.context
                    assert offer["scrapeBatchId"] == gottebiten_config.scrapeBatchId
                    assert offer["namespace"] == gottebiten_config.namespace

    @patch.dict(os.environ, {"STAGE": "test"})
    def test_handle_empty_feed(self, gottebiten_config, mock_database_calls):
        """Test handling of completely empty feed."""
        # Arrange
        empty_feed_data = []
        feed_stream = create_mock_stream(empty_feed_data)

        # Act
        result = handle_feed_with_config_postgres(feed_stream, gottebiten_config)

        # Assert
        assert result["items_handled"] == 0
        assert result["n_filtered_offers"] == 0

        # Database operations should still be called for batch tracking
        mocks = mock_database_calls
        mocks["insert_batch"].assert_called_once()
        mocks["update_status"].assert_called_once_with("test-batch-run-id", "COMPLETED")

        # No offers to store, so store_batch should not be called
        mocks["store_batch"].assert_not_called()

    @patch.dict(os.environ, {"STAGE": "test"})
    def test_handle_feed_with_filtering(self, gottebiten_feed_data, gottebiten_config, mock_database_calls):
        """Test that filtering works correctly by adding a restrictive filter."""
        # Arrange - Add a filter that will exclude most items
        # Use the filter format that the system expects
        config_with_filter = gottebiten_config.model_copy(
            update={
                "filters": [
                    {
                        "source": "pricing.price",
                        "operator": "gte",
                        "target": 1000,  # Very high minimum price - will filter out most items
                    }
                ]
            }
        )

        feed_stream = create_mock_stream(gottebiten_feed_data)

        # Act
        result = handle_feed_with_config_postgres(feed_stream, config_with_filter)

        # Assert
        assert result["items_handled"] > 0  # Items were processed
        # Filtered offers should be less than total (most items filtered out)
        assert result["n_filtered_offers"] < result["items_handled"]

    @patch.dict(os.environ, {"STAGE": "dev"})
    def test_handle_feed_dev_stage_limit(self, meny_feed_data, meny_config, mock_database_calls):
        """Test that development stage limits processing to 512 offers."""
        # Arrange
        feed_stream = create_mock_stream(meny_feed_data)

        # Act
        result = handle_feed_with_config_postgres(feed_stream, meny_config)

        # Assert - Should stop at 512 offers in dev mode
        assert result["items_handled"] <= 512

        # Verify database operations were still called
        mocks = mock_database_calls
        mocks["insert_batch"].assert_called_once()
        mocks["update_status"].assert_called_once()

    @patch.dict(os.environ, {"STAGE": "test"})
    def test_handle_medium_feed_batching(self, meny_feed_data, meny_config, mock_database_calls):
        """Test batching behavior with medium-sized feed (meny ~200 offers)."""
        # Arrange
        feed_stream = create_mock_stream(meny_feed_data)

        # Act
        result = handle_feed_with_config_postgres(feed_stream, meny_config)

        # Assert
        assert result["items_handled"] > 0

        # Check batching - should be called once for the final batch
        # (since meny feed is < 1000 items, it won't trigger mid-processing batches)
        mocks = mock_database_calls
        mocks["store_batch"].assert_called()

        # Verify all processed offers are in reasonable range
        total_stored_offers = 0
        for call in mocks["store_batch"].call_args_list:
            args, kwargs = call
            if args:
                offers = args[0]
            else:
                offers = kwargs["offers"]
            total_stored_offers += len(offers)

        assert total_stored_offers == result["n_filtered_offers"]

    @patch.dict(os.environ, {"STAGE": "test"})
    def test_handle_malformed_json_error(self, gottebiten_config, mock_database_calls):
        """Test error handling for incomplete/malformed JSON."""
        # Arrange - Create a malformed JSON stream
        malformed_json = '{"incomplete": "json" '  # Missing closing brace
        import io
        from unittest.mock import Mock

        from botocore.response import StreamingBody

        mock_stream = Mock(spec=StreamingBody)
        mock_stream._raw_stream = io.BytesIO(malformed_json.encode("utf-8"))
        mock_stream.read = lambda size=-1: mock_stream._raw_stream.read(size)
        mock_stream.close = Mock()

        # Act
        result = handle_feed_with_config_postgres(mock_stream, gottebiten_config)

        # Assert - Should return error result
        assert isinstance(result, dict)
        assert result["message"] == "Incomplete JSON error"
        assert "error" in result

        # Database operations should still have been initiated
        mocks = mock_database_calls
        mocks["insert_batch"].assert_called_once()

    @patch.dict(os.environ, {"STAGE": "test"})
    def test_handle_single_item_feed(self, gottebiten_feed_data, gottebiten_config, mock_database_calls):
        """Test handling of feed with exactly one item."""
        # Arrange - Use only the first item from gottebiten feed
        single_item_feed = [gottebiten_feed_data[0]]
        feed_stream = create_mock_stream(single_item_feed)

        # Act
        result = handle_feed_with_config_postgres(feed_stream, gottebiten_config)

        # Assert
        assert result["items_handled"] == 1
        assert result["n_filtered_offers"] >= 0

        # Should still process normally
        mocks = mock_database_calls
        mocks["insert_batch"].assert_called_once()
        mocks["update_status"].assert_called_once()

        # Should store the single item
        if result["n_filtered_offers"] > 0:
            mocks["store_batch"].assert_called()
            call_args, call_kwargs = mocks["store_batch"].call_args
            if call_args:
                stored_offers = call_args[0]
            else:
                stored_offers = call_kwargs["offers"]
            assert len(stored_offers) == 1

    @patch.dict(os.environ, {"STAGE": "test"})
    def test_database_error_handling(
        self,
        gottebiten_feed_data,
        gottebiten_config,
        mock_database_calls,  # We need this to stop the autouse fixture from working
    ):
        """Test behavior when database operations fail."""
        # Override the autouse fixture mock to simulate failure
        mock_database_calls["insert_batch"].side_effect = Exception("Database connection failed")

        feed_stream = create_mock_stream(gottebiten_feed_data)

        # Act & Assert - Should propagate the database error
        with pytest.raises(Exception, match="Database connection failed"):
            handle_feed_with_config_postgres(feed_stream, gottebiten_config)

    # === Additional Dogfeeding Tests with Different Feed Types ===

    @patch.dict(os.environ, {"STAGE": "test"})
    def test_handle_swecandy_feed_success(self, swecandy_feed_data, swecandy_config, mock_database_calls):
        """Test processing Swedish candy feed (different market/context)."""
        # Arrange
        feed_stream = create_mock_stream(swecandy_feed_data)

        # Act
        result = handle_feed_with_config_postgres(feed_stream, swecandy_config)

        # Assert
        assert result["items_handled"] > 0
        assert result["n_filtered_offers"] >= 0

        # Verify Swedish context
        mocks = mock_database_calls
        mocks["insert_batch"].assert_called_once()
        mocks["update_status"].assert_called_once_with("test-batch-run-id", "COMPLETED")

        # Check that offers have Swedish context
        if result["n_filtered_offers"] > 0:
            store_calls = mocks["store_batch"].call_args_list
            for call in store_calls:
                args, kwargs = call
                offers = kwargs["offers"] if not args else args[0]
                context = kwargs["context"] if not args else args[2]

                assert context == "amp-se"
                for offer in offers:
                    assert offer["context"] == "amp-se"
                    assert offer["namespace"] == "swecandy"

    @patch.dict(os.environ, {"STAGE": "test"})
    def test_handle_monter_feed_with_extraction(self, monter_feed_data, monter_config, mock_database_calls):
        """Test building supplies feed with quantity/properties extraction enabled."""
        # Arrange
        feed_stream = create_mock_stream(monter_feed_data)

        # Act
        result = handle_feed_with_config_postgres(feed_stream, monter_config)

        # Assert
        assert result["items_handled"] > 0

        # Verify extraction fields were configured
        assert "title" in monter_config.extractQuantityFields
        assert "description" in monter_config.extractQuantityFields
        assert "description" in monter_config.extractPropertiesFields

        mocks = mock_database_calls
        mocks["insert_batch"].assert_called_once()

    @patch.dict(os.environ, {"STAGE": "test"})
    def test_handle_obsbygg_feed_with_filtering(self, obsbygg_feed_data, obsbygg_config, mock_database_calls):
        """Test building supplies feed with pre-configured filtering."""
        # Arrange
        feed_stream = create_mock_stream(obsbygg_feed_data)

        # Act
        result = handle_feed_with_config_postgres(feed_stream, obsbygg_config)

        # Assert
        assert result["items_handled"] > 0
        # With price filter >= 1 NOK, most items should pass
        assert result["n_filtered_offers"] >= 0

        # Verify filtering was applied
        assert len(obsbygg_config.filters) > 0
        assert obsbygg_config.filters[0]["source"] == "pricing.price"

        mocks = mock_database_calls
        mocks["insert_batch"].assert_called_once()

    @patch.dict(os.environ, {"STAGE": "test"})
    def test_handle_large_byggmax_feed_batching(self, byggmax_feed_data, byggmax_config, mock_database_calls):
        """Test large feed that should trigger 1000-item batching logic."""
        # Arrange - Use only first 1500 items to test batching without being too slow
        large_subset = byggmax_feed_data[:1500]  # Should trigger mid-processing batching
        feed_stream = create_mock_stream(large_subset)

        # Act
        result = handle_feed_with_config_postgres(feed_stream, byggmax_config)

        # Assert
        assert result["items_handled"] > 1000  # Should process more than 1000 items

        # Should have multiple batch calls due to 1000-item batching
        mocks = mock_database_calls
        assert mocks["store_batch"].call_count >= 2, "Expected multiple batch calls for large feed"

        # Verify total offers processed
        total_stored_offers = 0
        for call in mocks["store_batch"].call_args_list:
            args, kwargs = call
            offers = kwargs["offers"] if not args else args[0]
            total_stored_offers += len(offers)

        assert total_stored_offers == result["n_filtered_offers"]

        # Verify comprehensive extraction config
        assert len(byggmax_config.extractQuantityFields) > 0
        assert len(byggmax_config.extractPropertiesFields) > 0
        assert len(byggmax_config.extractIngredientsFields) > 0

    @patch.dict(os.environ, {"STAGE": "test"})
    def test_handle_europris_feed_edge_case(self, europris_feed_data, europris_config, mock_database_calls):
        """Test another small feed to verify consistency across different feed structures."""
        # Arrange
        feed_stream = create_mock_stream(europris_feed_data)

        # Act
        result = handle_feed_with_config_postgres(feed_stream, europris_config)

        # Assert
        assert result["items_handled"] > 0
        assert isinstance(result["items_handled"], int)
        assert isinstance(result["n_filtered_offers"], int)

        mocks = mock_database_calls
        mocks["insert_batch"].assert_called_once()
        mocks["update_status"].assert_called_once()

    @patch.dict(os.environ, {"STAGE": "test"})
    def test_feed_processing_consistency_across_markets(
        self,
        gottebiten_feed_data,
        meny_feed_data,
        swecandy_feed_data,
        gottebiten_config,
        meny_config,
        swecandy_config,
        mock_database_calls,
    ):
        """Test that different feeds/configs produce consistent result structures."""
        feeds_and_configs = [
            (gottebiten_feed_data, gottebiten_config, "amp-se"),
            (meny_feed_data, meny_config, "amp-no"),
            (swecandy_feed_data, swecandy_config, "amp-se"),
        ]

        results = []
        for feed_data, config, expected_context in feeds_and_configs:
            # Reset mocks between feeds
            for mock in mock_database_calls.values():
                mock.reset_mock()

            feed_stream = create_mock_stream(feed_data)
            result = handle_feed_with_config_postgres(feed_stream, config)

            # Verify consistent result structure
            assert "items_handled" in result
            assert "n_filtered_offers" in result
            assert result["items_handled"] >= 0
            assert result["n_filtered_offers"] >= 0

            results.append(result)

        # All feeds should have processed some items
        assert all(r["items_handled"] > 0 for r in results), "All feeds should have items"
