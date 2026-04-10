"""
server/app.py — Multi-mode deployment entry point.

Re-exports the FastAPI application from api/ and provides a
`main()` entry point for use as a console script via pyproject.toml.
"""

from __future__ import annotations
import os

# Re-export the FastAPI app so tools that import server.app:app work
from api.app import app  # noqa: F401


def main() -> None:
    """Start the uvicorn server. Used by the 'serve' console script."""
    import uvicorn

    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(
        "server.app:app",
        host="0.0.0.0",
        port=port,
        workers=1,
        timeout_keep_alive=30,
    )


if __name__ == "__main__":
    main()
