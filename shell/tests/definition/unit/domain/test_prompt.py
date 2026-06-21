from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.definition.entities.prompt import Prompt
from shell.domain.definition.value_objects.ids import PromptId
from shell.domain.platform.value_objects.hash import Hash

_NOW = datetime(2026, 6, 1, tzinfo=UTC)


class TestPrompt:
    def test_new_creates_with_defaults(self) -> None:
        p = Prompt.new(
            id_=PromptId.generate(),
            name="system-instructions",
            body="You are a helpful assistant.",
            now=_NOW,
        )
        assert p.name == "system-instructions"
        assert p.version == 1
        assert p.body == "You are a helpful assistant."
        assert p.is_current is True
        assert p.created_at == _NOW

    def test_new_computes_hash_from_body(self) -> None:
        body = "You are a helpful assistant."
        p = Prompt.new(
            id_=PromptId.generate(),
            name="x",
            body=body,
            now=_NOW,
        )
        assert p.hash == Hash.of(body)

    def test_different_bodies_have_different_hashes(self) -> None:
        p1 = Prompt.new(id_=PromptId.generate(), name="a", body="hello", now=_NOW)
        p2 = Prompt.new(id_=PromptId.generate(), name="b", body="world", now=_NOW)
        assert p1.hash != p2.hash

    def test_identity_based_on_id(self) -> None:
        id1 = PromptId.generate()
        id2 = PromptId.generate()
        p1 = Prompt(id1, "a", 1, Hash.of("x"), "body", "uri", True, _NOW)
        p2 = Prompt(id1, "b", 2, Hash.of("y"), "diff", "uri2", False, _NOW)
        p3 = Prompt(id2, "a", 1, Hash.of("x"), "body", "uri", True, _NOW)
        assert p1 == p2
        assert p1 != p3
