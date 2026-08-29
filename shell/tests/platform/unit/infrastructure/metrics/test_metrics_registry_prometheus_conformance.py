"""Conformance tests — MetricsRegistry output vs Prometheus text exposition format.

Renders a populated registry and validates the resulting ``text/plain;
version=0.0.4`` output against a strict reference parser that implements the
exposition grammar (HELP/TYPE headers, escaped label values, bucket/sum/count
samples). This is the dependency-free guard called for by
ADR-0003 ``observability.v1``.
"""

from __future__ import annotations

import re

from shell.platform.observability.infrastructure.metrics.registry import MetricsRegistry

_METRIC_NAME = re.compile(r"[a-zA-Z_:][a-zA-Z0-9_:]*")
_HELP_VALUE = re.compile(r"((?:\\\\)|\\n|[^\\])*")
_VALUE = re.compile(r"-?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?")
_LABEL_VALUE = re.compile(r'((?:\\\\)|\\"|\\n|[^\\"])*')

_TYPES = frozenset({"counter", "gauge", "histogram", "summary", "untyped"})


class _Sample:
    __slots__ = ("name", "labels", "value")

    def __init__(self, name: str, labels: dict[str, str], value: float) -> None:
        self.name = name
        self.labels = labels
        self.value = value


class _ParsedExposition:
    __slots__ = ("help", "types", "samples")

    def __init__(self) -> None:
        self.help: dict[str, str] = {}
        self.types: dict[str, str] = {}
        self.samples: list[_Sample] = []


class _ReferenceParser:
    """Strict parser for the Prometheus text exposition format 0.0.4."""

    def __init__(self, payload: str) -> None:
        self._lines = payload.splitlines()
        self._index = 0

    def parse(self) -> _ParsedExposition:
        result = _ParsedExposition()
        for raw in self._lines:
            line = raw.strip()
            if not line:
                continue
            if line.startswith("#"):
                self._parse_comment(line, result)
            else:
                result.samples.append(self._parse_sample(line))
        return result

    def _parse_comment(self, line: str, result: _ParsedExposition) -> None:
        parts = line.split()
        if len(parts) < 3:
            raise ValueError(f"malformed comment: {line!r}")
        keyword = parts[1]
        name = parts[2]
        if not _METRIC_NAME.fullmatch(name):
            raise ValueError(f"invalid metric name in comment: {name!r}")
        if keyword == "HELP":
            help_raw = line.split(maxsplit=3)
            if len(help_raw) < 4:
                help_raw.append("")
            unescaped = self._unescape_help(help_raw[3])
            if name in result.help:
                raise ValueError(f"duplicate HELP for {name!r}")
            result.help[name] = unescaped
        elif keyword == "TYPE":
            if len(parts) < 4 or parts[3] not in _TYPES:
                raise ValueError(f"invalid TYPE line: {line!r}")
            if name in result.types:
                raise ValueError(f"duplicate TYPE for {name!r}")
            result.types[name] = parts[3]
        else:
            raise ValueError(f"unknown comment keyword: {parts[1]!r}")

    def _parse_sample(self, line: str) -> _Sample:
        match = re.match(r"([^\s{]+)(\{[^}]*\})?\s+([^\s]+)\s*(.*)?$", line)
        if match is None:
            raise ValueError(f"malformed sample: {line!r}")
        name = match.group(1)
        if not _METRIC_NAME.fullmatch(name):
            raise ValueError(f"invalid sample name: {name!r}")
        labels_str = match.group(2) or ""
        labels: dict[str, str] = {}
        if labels_str:
            labels = self._parse_labels(labels_str[1:-1])
        value_raw = match.group(3)
        if not _VALUE.fullmatch(value_raw):
            raise ValueError(f"invalid sample value: {value_raw!r}")
        return _Sample(name, labels, float(value_raw))

    def _parse_labels(self, body: str) -> dict[str, str]:
        # Label names cannot be empty, but an empty body also means no labels.
        declared = [segment for segment in (body.split(",") if body else []) if segment]
        labels: dict[str, str] = {}
        for segment in declared:
            pair = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)=("(?:\\"|[^"])*")', segment)
            if pair is None:
                raise ValueError(f"malformed label segment: {segment!r}")
            label_name = pair.group(1)
            value = self._unescape_label(pair.group(2)[1:-1])
            if label_name in labels:
                raise ValueError(f"duplicate label {label_name!r}")
            labels[label_name] = value
        return labels

    @staticmethod
    def _unescape_help(raw: str) -> str:
        return raw.replace("\\n", "\n").replace("\\\\", "\\")

    @staticmethod
    def _unescape_label(raw: str) -> str:
        return raw.replace('\\"', '"').replace("\\n", "\n").replace("\\\\", "\\")


class TestPrometheusConformance:
    def test_render_parses_as_valid_exposition(self) -> None:
        registry = MetricsRegistry()
        counter = registry.counter(
            "http_requests_total",
            help="Inbound HTTP requests.",
            label_names=("service", "method"),
        )
        counter.inc(1.0, service="execution", method="GET")
        gauge = registry.gauge("inbox_backlog_pending", help="Pending records.")
        gauge.set(5.0)
        histogram = registry.histogram(
            "http_request_duration_seconds",
            help="Inbound duration.",
            buckets=(0.1, 0.5),
        )
        histogram.observe(0.05)
        histogram.observe(1.2)

        parsed = _ReferenceParser(registry.render()).parse()

        assert parsed.help == {
            "http_requests_total": "Inbound HTTP requests.",
            "inbox_backlog_pending": "Pending records.",
            "http_request_duration_seconds": "Inbound duration.",
        }
        assert parsed.types == {
            "http_requests_total": "counter",
            "inbox_backlog_pending": "gauge",
            "http_request_duration_seconds": "histogram",
        }
        assert (
            "http_requests_total",
            {"service": "execution", "method": "GET"},
            1.0,
        ) in [(sample.name, sample.labels, sample.value) for sample in parsed.samples]
        assert ("inbox_backlog_pending", {}, 5.0) in [
            (sample.name, sample.labels, sample.value) for sample in parsed.samples
        ]
        buckets = {
            labels["le"]: value
            for sample in parsed.samples
            if sample.name == "http_request_duration_seconds_bucket"
            for labels, value in [(sample.labels, sample.value)]
        }
        assert buckets == {"0.1": 1.0, "0.5": 1.0, "+Inf": 2.0}
        count = [
            sample.value
            for sample in parsed.samples
            if sample.name == "http_request_duration_seconds_count"
        ]
        assert count == [2.0]

    def test_label_and_help_escaping_round_trips(self) -> None:
        registry = MetricsRegistry()
        gauge = registry.gauge(
            "escaping_probe",
            help="Line 1\nLine 2 with \\ backslash.",
            label_names=("note",),
        )
        gauge.set(1.0, note='has "quotes" and \\ and \n newline')

        parsed = _ReferenceParser(registry.render()).parse()

        assert parsed.help["escaping_probe"] == "Line 1\nLine 2 with \\ backslash."
        target = [sample for sample in parsed.samples if sample.name == "escaping_probe"]
        assert len(target) == 1
        assert target[0].labels["note"] == 'has "quotes" and \\ and \n newline'

    def test_counter_requires_total_suffix_in_family_name(self) -> None:
        registry = MetricsRegistry()
        registry.counter("jobs_done_total", help="Finished jobs.")

        parsed = _ReferenceParser(registry.render()).parse()

        assert parsed.types["jobs_done_total"] == "counter"

    def test_empty_registry_renders_valid_empty_payload(self) -> None:
        registry = MetricsRegistry()

        output = registry.render()

        assert output == ""
        parsed = _ReferenceParser(output).parse()
        assert parsed.samples == []
