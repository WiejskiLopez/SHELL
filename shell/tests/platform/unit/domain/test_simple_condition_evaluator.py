from __future__ import annotations

from shell.domain.definition.value_objects.ids import GraphDefinitionId
from shell.domain.execution.aggregates.graph_execution import GraphExecution
from shell.domain.execution.value_objects.ids import (
    GraphExecutionId,
    GraphNodeExecutionId,
    TaskExecutionId,
)
from shell.domain.platform.services.simple_condition_evaluator import SimpleConditionEvaluator


def _make_graph_execution() -> GraphExecution:
    return GraphExecution(
        id=GraphExecutionId.generate(),
        task_execution_id=TaskExecutionId("t1"),
        graph_definition_id=GraphDefinitionId("g1"),
    )


class TestSimpleConditionEvaluator:
    def setup_method(self) -> None:
        self._evaluator = SimpleConditionEvaluator()
        self._ge = _make_graph_execution()
        self._src = GraphNodeExecutionId("src")

    def test_true_returns_true(self) -> None:
        assert self._evaluator.evaluate("true", "plain", self._ge, self._src)

    def test_yes_returns_true(self) -> None:
        assert self._evaluator.evaluate("yes", "plain", self._ge, self._src)

    def test_one_returns_true(self) -> None:
        assert self._evaluator.evaluate("1", "plain", self._ge, self._src)

    def test_false_returns_false(self) -> None:
        assert not self._evaluator.evaluate("false", "plain", self._ge, self._src)

    def test_no_returns_false(self) -> None:
        assert not self._evaluator.evaluate("no", "plain", self._ge, self._src)

    def test_zero_returns_false(self) -> None:
        assert not self._evaluator.evaluate("0", "plain", self._ge, self._src)

    def test_case_insensitive_true(self) -> None:
        assert self._evaluator.evaluate("TRUE", "plain", self._ge, self._src)

    def test_case_insensitive_false(self) -> None:
        assert not self._evaluator.evaluate("FALSE", "plain", self._ge, self._src)

    def test_non_plain_language_returns_false(self) -> None:
        assert not self._evaluator.evaluate("true", "python", self._ge, self._src)

    def test_language_none_uses_plain(self) -> None:
        assert self._evaluator.evaluate("true", None, self._ge, self._src)

    def test_non_blank_unknown_expression_returns_true(self) -> None:
        assert self._evaluator.evaluate("something", "plain", self._ge, self._src)

    def test_whitespace_only_expression_returns_true(self) -> None:
        assert self._evaluator.evaluate("  TRuE  ", "plain", self._ge, self._src)
