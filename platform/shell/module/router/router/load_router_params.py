"""load_router_params.py — DEPRECATED.
Use app.runner_.router_.init_router() instead.
"""


def load_router_params(app) -> None:
    """Deprecated. Delegates to app.runner_.router_.init_router()."""
    app.runner_.router_.init_router()

