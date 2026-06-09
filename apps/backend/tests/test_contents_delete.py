"""R-E-1 / feedback #2: ContentRepository.delete must report True when the
Supabase row was removed, even if the fallback dict never held the id."""

from app.repositories.contents_repo import FALLBACK_CONTENTS, ContentRepository


class _FakeSupabase:
    is_configured = True

    def __init__(self, deleted_count: int) -> None:
        self.deleted_count = deleted_count
        self.calls: list[tuple[str, dict]] = []

    def delete(self, table: str, filters: dict) -> int:
        self.calls.append((table, filters))
        return self.deleted_count


class _UnconfiguredSupabase:
    is_configured = False

    def delete(self, *args, **kwargs):  # pragma: no cover - never reached
        raise AssertionError("should not be called when not configured")


def test_supabase_delete_success_returns_true_even_without_fallback_entry():
    FALLBACK_CONTENTS.clear()
    repo = ContentRepository(_FakeSupabase(deleted_count=1))  # type: ignore[arg-type]
    assert repo.delete("c-1") is True


def test_supabase_delete_zero_rows_and_no_fallback_returns_false():
    FALLBACK_CONTENTS.clear()
    repo = ContentRepository(_FakeSupabase(deleted_count=0))  # type: ignore[arg-type]
    assert repo.delete("c-1") is False


def test_fallback_mode_still_works():
    FALLBACK_CONTENTS.clear()
    FALLBACK_CONTENTS["c-1"] = {"id": "c-1"}
    repo = ContentRepository(_UnconfiguredSupabase())  # type: ignore[arg-type]
    assert repo.delete("c-1") is True
    assert repo.delete("c-1") is False
