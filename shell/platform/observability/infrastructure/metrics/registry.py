"""MetricsRegistry — dependency-free Prometheus text-format metrics registry.

Implements a small subset of the Prometheus client model (counter, gauge,
histogram) and renders it in the text exposition format
(``text/plain; version=0.0.4``) without pulling a third-party dependency. The
registry is thread-safe and is the single source of truth for every service
``/metrics`` endpoint.
"""

from __future__ import annotations

import re
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

_METRIC_NAME_RE = re.compile(r"^[a-zA-Z_:][a-zA-Z0-9_:]*$")


def _validate_name(name: str) -> None:
    if not _METRIC_NAME_RE.fullmatch(name):
        raise ValueError(f"invalid metric name: {name!r}")


def _escape_help(help_text: str) -> str:
    return help_text.replace("\\", "\\\\").replace("\n", "\\n")


def _escape_label_value(value: object) -> str:
    text = str(value)
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _format_number(value: float) -> str:
    return str(float(value))


def _render_labels(label_names: tuple[str, ...], values: tuple[str, ...]) -> str:
    if not label_names:
        return ""
    rendered = ",".join(
        f'{name}="{_escape_label_value(value)}"'
        for name, value in zip(label_names, values, strict=False)
    )
    return f"{{{rendered}}}"


class _Family:
    def __init__(self, name: str, help_text: str, label_names: tuple[str, ...]) -> None:
        _validate_name(name)
        self.name = name
        self.help_text = help_text
        self.type = "untyped"
        self.label_names = label_names
        self._values: dict[tuple[str, ...], float] = {}
        self._lock = threading.RLock()

    def _label_key(self, labels: dict[str, object]) -> tuple[str, ...]:
        if not self.label_names:
            if labels:
                raise ValueError(f"metric {self.name!r} takes no labels")
            return ()
        missing = [label for label in self.label_names if label not in labels]
        if missing:
            raise ValueError(f"metric {self.name!r} missing labels: {missing}")
        extra = sorted(set(labels) - set(self.label_names))
        if extra:
            raise ValueError(f"metric {self.name!r} has unknown labels: {extra}")
        return tuple(str(labels[label]) for label in self.label_names)

    def _render_values(self, metric_name: str) -> Iterable[str]:
        with self._lock:
            ordered = sorted(self._values.items())
        for key, value in ordered:
            yield f"{metric_name}{_render_labels(self.label_names, key)} {_format_number(value)}"

    def render(self) -> list[str]:
        lines = [
            f"# HELP {self.name} {_escape_help(self.help_text)}",
            f"# TYPE {self.name} {self.type}",
        ]
        lines.extend(self._render_values(self.name))
        return lines


class CounterFamily:
    """Monotonic counter; exposed with the conventional ``_total`` suffix."""

    def __init__(self, family: _Family) -> None:
        self._family = family

    def inc(self, amount: float = 1.0, **labels: object) -> None:
        key = self._family._label_key(labels)
        with self._family._lock:
            current = self._family._values.get(key, 0.0)
            self._family._values[key] = current + float(amount)

    def value(self, **labels: object) -> float:
        key = self._family._label_key(labels)
        with self._family._lock:
            return self._family._values.get(key, 0.0)


class GaugeFamily:
    """Value that can go up and down."""

    def __init__(self, family: _Family) -> None:
        self._family = family

    def set(self, value: float, **labels: object) -> None:
        key = self._family._label_key(labels)
        with self._family._lock:
            self._family._values[key] = float(value)

    def inc(self, amount: float = 1.0, **labels: object) -> None:
        self.set(self.value(**labels) + float(amount), **labels)

    def dec(self, amount: float = 1.0, **labels: object) -> None:
        self.set(self.value(**labels) - float(amount), **labels)

    def value(self, **labels: object) -> float:
        key = self._family._label_key(labels)
        with self._family._lock:
            return self._family._values.get(key, 0.0)


class HistogramFamily:
    """Histogram with fixed buckets; exposes bucket/sum/count samples."""

    def __init__(self, family: _Family, buckets: tuple[float, ...]) -> None:
        self._family = family
        self._buckets = sorted(float(bucket) for bucket in buckets)
        self._counts: dict[tuple[str, ...], list[float]] = {}
        self._sums: dict[tuple[str, ...], float] = {}

    def observe(self, value: float, **labels: object) -> None:
        key = self._family._label_key(labels)
        with self._family._lock:
            counts = self._counts.setdefault(key, [0.0] * (len(self._buckets) + 1))
            for index, upper_bound in enumerate(self._buckets):
                if value <= upper_bound:
                    counts[index] += 1.0
            counts[-1] += 1.0
            self._sums[key] = self._sums.get(key, 0.0) + float(value)

    def render(self) -> list[str]:
        lines = [
            f"# HELP {self._family.name} {_escape_help(self._family.help_text)}",
            f"# TYPE {self._family.name} histogram",
        ]
        with self._family._lock:
            keys = sorted(self._counts)
            for key in keys:
                counts = self._counts[key]
                total = counts[-1]
                for index, upper_bound in enumerate(self._buckets):
                    bucket_lines = (
                        f"{self._family.name}_bucket"
                        f"{_render_labels(self._family.label_names + ('le',), key + (str(upper_bound),))}"
                        f" {_format_number(counts[index])}"
                    )
                    lines.append(bucket_lines)
                lines.append(
                    f"{self._family.name}_bucket"
                    f"{_render_labels(self._family.label_names + ('le',), key + ('+Inf',))}"
                    f" {_format_number(total)}"
                )
                lines.append(
                    f"{self._family.name}_sum"
                    f"{_render_labels(self._family.label_names, key)} "
                    f"{_format_number(self._sums[key])}"
                )
                lines.append(
                    f"{self._family.name}_count"
                    f"{_render_labels(self._family.label_names, key)} "
                    f"{_format_number(total)}"
                )
        return lines


class MetricsRegistry:
    """Thread-safe registry of counters/gauges/histograms with text rendering."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._counters: dict[str, CounterFamily] = {}
        self._gauges: dict[str, GaugeFamily] = {}
        self._histograms: dict[str, HistogramFamily] = {}

    def counter(
        self,
        name: str,
        *,
        help: str = "",
        label_names: tuple[str, ...] = (),
    ) -> CounterFamily:
        with self._lock:
            if name in self._counters:
                return self._counters[name]
            family = _Family(name, help, label_names)
            family.type = "counter"
            counter = CounterFamily(family)
            self._counters[name] = counter
            return counter

    def gauge(
        self,
        name: str,
        *,
        help: str = "",
        label_names: tuple[str, ...] = (),
    ) -> GaugeFamily:
        with self._lock:
            if name in self._gauges:
                return self._gauges[name]
            family = _Family(name, help, label_names)
            family.type = "gauge"
            gauge = GaugeFamily(family)
            self._gauges[name] = gauge
            return gauge

    def histogram(
        self,
        name: str,
        *,
        help: str = "",
        label_names: tuple[str, ...] = (),
        buckets: tuple[float, ...] = (
            0.005,
            0.01,
            0.025,
            0.05,
            0.1,
            0.25,
            0.5,
            1.0,
            2.5,
            5.0,
            10.0,
        ),
    ) -> HistogramFamily:
        with self._lock:
            if name in self._histograms:
                return self._histograms[name]
            family = _Family(name, help, label_names)
            family.type = "histogram"
            histogram = HistogramFamily(family, buckets)
            self._histograms[name] = histogram
            return histogram

    def render(self) -> str:
        blocks: list[list[str]] = []
        with self._lock:
            for counter in self._counters.values():
                blocks.append(counter._family.render())
            for gauge in self._gauges.values():
                blocks.append(gauge._family.render())
            for histogram in self._histograms.values():
                blocks.append(histogram.render())
        blocks.sort(key=lambda lines: lines[0] if lines else "")
        output = "\n".join("\n".join(lines) for lines in blocks)
        return output + "\n" if output else ""

    # OutboundHttpMetricsRecorder / InboundHttpMetricsRecorder entrypoints ------
    def record_inbound_request(
        self,
        *,
        service: str,
        method: str,
        status: int,
        duration_seconds: float,
    ) -> None:
        requests = self.counter(
            "http_requests_total",
            help="Total inbound HTTP requests by service, method and status.",
            label_names=("service", "method", "status"),
        )
        requests.inc(1.0, service=service, method=method, status=str(status))
        duration = self.histogram(
            "http_request_duration_seconds",
            help="Inbound HTTP request duration in seconds.",
            label_names=("service", "method"),
        )
        duration.observe(duration_seconds, service=service, method=method)

    def record_outbound_attempt(self, *, target_service: str, method: str) -> None:
        attempts = self.counter(
            "http_outbound_requests_total",
            help="Total outbound HTTP attempts by target service and method.",
            label_names=("target_service", "method"),
        )
        attempts.inc(1.0, target_service=target_service, method=method)

    def record_outbound_retry(self, *, target_service: str, method: str) -> None:
        retries = self.counter(
            "http_outbound_retries_total",
            help="Total outbound HTTP retries by target service and method.",
            label_names=("target_service", "method"),
        )
        retries.inc(1.0, target_service=target_service, method=method)

    def record_circuit_trip(self, *, target_service: str, method: str) -> None:
        trips = self.counter(
            "http_outbound_circuit_trips_total",
            help="Times the circuit breaker opened for a target service.",
            label_names=("target_service", "method"),
        )
        trips.inc(1.0, target_service=target_service, method=method)

    def record_circuit_reject(self, *, target_service: str, method: str) -> None:
        rejects = self.counter(
            "http_outbound_circuit_rejects_total",
            help="Requests rejected locally because the circuit was open.",
            label_names=("target_service", "method"),
        )
        rejects.inc(1.0, target_service=target_service, method=method)

    def record_circuit_state(self, *, target_service: str, method: str, state: str) -> None:
        gauge = self.gauge(
            "http_outbound_circuit_state",
            help="Circuit breaker state (0=closed, 1=open, 2=half_open).",
            label_names=("target_service", "method"),
        )
        state_value = {"closed": 0.0, "open": 1.0, "half_open": 2.0}.get(state, 0.0)
        gauge.set(state_value, target_service=target_service, method=method)
