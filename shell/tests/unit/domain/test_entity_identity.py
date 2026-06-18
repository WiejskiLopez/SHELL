from __future__ import annotations

from .conftest import _SampleEntity, _SampleId


class TestEntityIdentity:
    def test_id_is_exposed_via_property(self) -> None:
        e = _SampleEntity(_SampleId("a"), "x")
        assert e.id == _SampleId("a")

    def test_equality_is_identity_based(self) -> None:
        a1 = _SampleEntity(_SampleId("same"), "label-1")
        a2 = _SampleEntity(_SampleId("same"), "label-2-different")
        assert a1 == a2

    def test_inequality_for_different_ids(self) -> None:
        a = _SampleEntity(_SampleId("a"), "x")
        b = _SampleEntity(_SampleId("b"), "x")
        assert a != b

    def test_hash_matches_identity(self) -> None:
        a1 = _SampleEntity(_SampleId("same"), "label-1")
        a2 = _SampleEntity(_SampleId("same"), "label-2")
        assert hash(a1) == hash(a2)
        assert {a1, a2} == {a1}

    def test_compare_with_non_entity_returns_not_implemented(self) -> None:
        e = _SampleEntity(_SampleId("a"), "x")
        assert (e == "not-an-entity") is False
