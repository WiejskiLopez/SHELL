from __future__ import annotations

import asyncio

import pytest

from shell.platform.application.context.correlation_id import (
    get_correlation_id,
    reset_correlation_id,
    set_correlation_id,
)


class TestCorrelationId:
    def test_set_and_get(self) -> None:
        set_correlation_id("abc-123")
        assert get_correlation_id() == "abc-123"
        set_correlation_id("")

    @pytest.mark.asyncio
    async def test_parallel_tasks_keep_correlation_context_isolated(self) -> None:
        baseline = get_correlation_id()

        async def capture(value: str) -> str:
            token = set_correlation_id(value)
            try:
                await asyncio.sleep(0)
                return get_correlation_id()
            finally:
                reset_correlation_id(token)

        results = await asyncio.gather(capture("corr-a"), capture("corr-b"))

        assert tuple(results) == ("corr-a", "corr-b")
        assert get_correlation_id() == baseline
