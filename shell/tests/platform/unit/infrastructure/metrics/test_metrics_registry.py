"""Unit tests — MetricsRegistry Prometheus text-format rendering."""

from __future__ import annotations

import pytest

from shell.platform.observability.infrastructure.metrics.registry import MetricsRegistry


class TestMetricsRegistry:
    def test_counter_renders_with_total_suffix(self) -> None:
        registry = MetricsRegistry()
        counter = registry.counter("http_requests_total", help="Requests.", label_names=("method",))
        counter.inc(1.0, method="GET")
        counter.inc(2.0, method="GET")

        output = registry.render()

        assert "# TYPE http_requests_total counter" in output
        assert "# HELP http_requests_total Requests." in output
        assert 'http_requests_total{method="GET"} 3.0' in output

    def test_gauge_set_and_dec(self) -> None:
        registry = MetricsRegistry()
        gauge = registry.gauge("inbox_backlog_pending", help="Pending count.")
        gauge.set(7.0)
        assert gauge.value() == 7.0
        gauge.dec(2.0)
        assert gauge.value() == 5.0

        assert "inbox_backlog_pending 5.0" in registry.render()

    def test_histogram_renders_buckets_sum_and_count(self) -> None:
        registry = MetricsRegistry()
        histogram = registry.histogram(
            "http_request_duration_seconds",
            help="Duration.",
            buckets=(0.1, 0.5),
        )
        histogram.observe(0.05)
        histogram.observe(0.3)
        histogram.observe(1.2)

        output = registry.render()
        assert "# TYPE http_request_duration_seconds histogram" in output
        assert 'http_request_duration_seconds_bucket{le="0.1"} 1.0' in output
        assert 'http_request_duration_seconds_bucket{le="0.5"} 2.0' in output
        assert 'http_request_duration_seconds_bucket{le="+Inf"} 3.0' in output
        sum_line = next(
            line
            for line in output.splitlines()
            if line.startswith("http_request_duration_seconds_sum")
        )
        assert float(sum_line.split()[-1]) == pytest.approx(1.55)
        assert "http_request_duration_seconds_count 3.0" in output

    def test_unknown_label_is_rejected(self) -> None:
        registry = MetricsRegistry()
        gauge = registry.gauge("some_metric", help="Metrics.", label_names=("service",))

        with pytest.raises(ValueError):
            gauge.set(1.0, service="execution", unexpected="x")

    def test_missing_label_is_rejected(self) -> None:
        registry = MetricsRegistry()
        gauge = registry.gauge("some_metric", help="Metrics.", label_names=("service",))

        with pytest.raises(ValueError):
            gauge.set(1.0)

    def test_invalid_metric_name_is_rejected(self) -> None:
        registry = MetricsRegistry()

        with pytest.raises(ValueError):
            registry.counter("not-a-valid-name", help="Bad.")

    def test_inbound_request_records_counter_and_histogram(self) -> None:
        registry = MetricsRegistry()
        registry.record_inbound_request(
            service="execution",
            method="GET",
            status=200,
            duration_seconds=0.05,
        )

        output = registry.render()
        assert "# TYPE http_requests_total counter" in output
        assert 'http_requests_total{service="execution",method="GET",status="200"} 1.0' in output
        assert "# TYPE http_request_duration_seconds histogram" in output

    def test_outbound_metrics_recording(self) -> None:
        registry = MetricsRegistry()
        registry.record_outbound_attempt(target_service="definition", method="GET")
        registry.record_outbound_retry(target_service="definition", method="GET")
        registry.record_circuit_trip(target_service="definition", method="GET")
        registry.record_circuit_reject(target_service="definition", method="GET")
        registry.record_circuit_state(target_service="definition", method="GET", state="open")

        output = registry.render()
        assert (
            'http_outbound_requests_total{target_service="definition",method="GET"} 1.0' in output
        )
        assert 'http_outbound_retries_total{target_service="definition",method="GET"} 1.0' in output
        assert (
            'http_outbound_circuit_trips_total{target_service="definition",method="GET"} 1.0'
            in output
        )
        assert (
            'http_outbound_circuit_rejects_total{target_service="definition",method="GET"} 1.0'
            in output
        )
        assert 'http_outbound_circuit_state{target_service="definition",method="GET"} 1.0' in output
