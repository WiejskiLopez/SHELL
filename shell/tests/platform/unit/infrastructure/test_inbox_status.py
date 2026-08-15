"""Unit tests for the platform inbox status enum."""

from __future__ import annotations

from shell.platform.domain.value_objects.inbox_status import InboxStatus


class TestInboxStatus:
    def test_enum_values_match_lifecycle_contract(self) -> None:
        assert InboxStatus.PENDING.value == "PENDING"
        assert InboxStatus.PROCESSING.value == "PROCESSING"
        assert InboxStatus.PROCESSED.value == "PROCESSED"
        assert InboxStatus.RETRY.value == "RETRY"
        assert InboxStatus.DEAD_LETTER.value == "DEAD_LETTER"
        assert InboxStatus.LEGACY_REVIEW.value == "LEGACY_REVIEW"

    def test_all_members_covered(self) -> None:
        assert set(InboxStatus) == {
            InboxStatus.PENDING,
            InboxStatus.PROCESSING,
            InboxStatus.PROCESSED,
            InboxStatus.RETRY,
            InboxStatus.DEAD_LETTER,
            InboxStatus.LEGACY_REVIEW,
        }

    def test_is_value_object_and_strenum(self) -> None:
        assert isinstance(InboxStatus.PENDING.value, str)
        assert InboxStatus.PENDING == "PENDING"
        assert InboxStatus.RETRY.value == str(InboxStatus.RETRY)
