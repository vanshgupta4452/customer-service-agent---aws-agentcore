"""Session persistence backed by a local snapshot store."""

from __future__ import annotations

from customer_service_agent.config import Settings


def build_session_manager(settings: Settings):
    """Create a ``SnapshotSessionManager`` that persists conversations to disk.

    ``SnapshotSessionManager`` is compatible with ``context_manager="auto"``.
    Swap ``LocalFileStorage`` for ``S3Storage`` in production without changing
    the rest of the agent.
    """
    from strands.session import SnapshotSessionManager
    from strands.storage import LocalFileStorage

    settings.session_dir.mkdir(parents=True, exist_ok=True)
    return SnapshotSessionManager(
        session_id=settings.session_id,
        storage=LocalFileStorage(str(settings.session_dir)),
    )
