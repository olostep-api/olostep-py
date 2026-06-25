"""
Batch scraped stats endpoint contract tests.

Validates the BatchScrapedStatsResponse model and the BATCH_SCRAPED_STATS
endpoint contract shape. No live API calls.
"""

from __future__ import annotations

import pytest

from olostep.backend.api_endpoints import BATCH_SCRAPED_STATS
from olostep.models.response import BatchScrapedStatsResponse


FIXTURE = {
    "object": "batch.scraped_stats",
    "window": 12.0,
    "start_time": 1750800000000,
    "end_time": 1750843200000,
    "start_time_iso": "2025-06-25T00:00:00.000Z",
    "end_time_iso": "2025-06-25T12:00:00.000Z",
    "parser": None,
    "batches": 5,
    "items": 2500,
    "scraped_items": 2375,
    "scraped_pct": 95.0,
}


class TestBatchScrapedStatsResponse:
    """Validate BatchScrapedStatsResponse model parsing."""

    def test_parses_full_fixture(self):
        r = BatchScrapedStatsResponse(**FIXTURE)
        assert r.object == "batch.scraped_stats"
        assert r.window == 12.0
        assert r.start_time == 1750800000000
        assert r.end_time == 1750843200000
        assert r.batches == 5
        assert r.items == 2500
        assert r.scraped_items == 2375
        assert r.scraped_pct == 95.0

    def test_parser_is_none_when_not_filtered(self):
        r = BatchScrapedStatsResponse(**FIXTURE)
        assert r.parser is None

    def test_parser_is_set_when_filtered(self):
        r = BatchScrapedStatsResponse(**{**FIXTURE, "parser": "amazon-product"})
        assert r.parser == "amazon-product"

    def test_scraped_pct_within_range(self):
        r = BatchScrapedStatsResponse(**FIXTURE)
        assert 0.0 <= r.scraped_pct <= 100.0

    def test_scraped_items_does_not_exceed_items(self):
        r = BatchScrapedStatsResponse(**FIXTURE)
        assert r.scraped_items <= r.items

    def test_end_time_greater_than_start_time(self):
        r = BatchScrapedStatsResponse(**FIXTURE)
        assert r.end_time > r.start_time

    @pytest.mark.parametrize("window", [1.0, 12.0, 48.0, 744.0])
    def test_various_window_values(self, window: float):
        r = BatchScrapedStatsResponse(**{**FIXTURE, "window": window})
        assert r.window == window

    def test_zero_counts_valid(self):
        r = BatchScrapedStatsResponse(**{
            **FIXTURE,
            "batches": 0,
            "items": 0,
            "scraped_items": 0,
            "scraped_pct": 0.0,
        })
        assert r.batches == 0
        assert r.scraped_pct == 0.0


class TestBatchScrapedStatsContract:
    """Validate the BATCH_SCRAPED_STATS endpoint contract definition."""

    def test_method_is_get(self):
        assert BATCH_SCRAPED_STATS.method == "GET"

    def test_path_is_correct(self):
        assert BATCH_SCRAPED_STATS.path == "/batches/stats/scraped"

    def test_response_model_is_set(self):
        assert BATCH_SCRAPED_STATS.response_model is BatchScrapedStatsResponse

    def test_request_model_is_none(self):
        assert BATCH_SCRAPED_STATS.request_model is None

    def test_has_examples(self):
        assert len(BATCH_SCRAPED_STATS.examples) >= 1
