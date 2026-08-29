"""Unit tests — PrometheusMetricsBackend maps delivery metrics into a registry."""

from __future__ import annotations

from shell.platform.observability.infrastructure.metrics.prometheus_metrics_backend import (
    PrometheusMetricsBackend,
)
from shell.platform.observability.infrastructure.metrics.registry import MetricsRegistry


class TestPrometheusMetricsBackend:
    def test_record_backlog_sets_gauges(self) -> None:
        registry = MetricsRegistry()
        backend = PrometheusMetricsBackend(registry)

        backend.record_backlog(
            pending=3,
            processing=1,
            processed=9,
            retry=2,
            dead_letter=4,
            oldest_pending_age_seconds=12.5,
        )

        output = registry.render()
        assert "inbox_backlog_pending 3.0" in output
        assert "inbox_backlog_processing 1.0" in output
        assert "inbox_backlog_processed 9.0" in output
        assert "inbox_backlog_retry 2.0" in output
        assert "inbox_backlog_dead_letter 4.0" in output
        assert "inbox_oldest_pending_age_seconds 12.5" in output

    def test_record_backlog_without_pending_sets_negative_age(self) -> None:
        registry = MetricsRegistry()
        backend = PrometheusMetricsBackend(registry)

        backend.record_backlog(
            pending=0,
            processing=0,
            processed=0,
            retry=0,
            dead_letter=0,
            oldest_pending_age_seconds=None,
        )

        assert "inbox_oldest_pending_age_seconds -1.0" in registry.render()

    def test_record_outbox_backlog_sets_gauge(self) -> None:
        registry = MetricsRegistry()
        backend = PrometheusMetricsBackend(registry)

        backend.record_outbox_backlog(pending=5)

        assert "outbox_backlog_pending 5.0" in registry.render()

    def test_lease_and_duplicate_metrics_are_counters(self) -> None:
        registry = MetricsRegistry()
        backend = PrometheusMetricsBackend(registry)

        backend.record_lease_expired(2)
        backend.record_duplicate_delivery(1)
        backend.record_duplicate_delivery(1)

        output = registry.render()
        assert "inbox_lease_expired_total 2.0" in output
        assert "inbox_duplicate_delivery_total 2.0" in output
