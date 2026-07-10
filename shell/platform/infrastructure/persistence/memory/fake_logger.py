from __future__ import annotations


class FakeLogger:
    def debug(self, msg: str, **kw: object) -> None:
        pass

    def info(self, msg: str, **kw: object) -> None:
        pass

    def warning(self, msg: str, **kw: object) -> None:
        pass

    def error(self, msg: str, **kw: object) -> None:
        pass
