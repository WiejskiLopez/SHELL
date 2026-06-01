"""_save_archive_zip.py
Private. Responsible for one thing: writing a timestamped ZIP archive
containing app metadata and snapshots of input/, output/, logs/, tmp/.
"""

from __future__ import annotations

import json
import zipfile
from collections.abc import Callable
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from shell.utils.path.path import Path, PathType

if TYPE_CHECKING:
    from shell.app.app_trace.app_trace import AppTrace

_SNAPSHOT_DIRS = ("input", "output", "logs", "temp")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _save_archive_zip(
    archive_dir: PathType,
    snapshot: dict,
    clock: Callable[[], datetime] | None = None,
    trace: 'AppTrace | None' = None,
) -> None:
    """Write a .zip archive under archive_dir/ capturing this execution snapshot.

    archive_dir: path to the node's archive/ directory.
    snapshot:    dict from result.runner_result (timestamp, status, role, mode, version, start, stop).
    clock:       optional callable () -> datetime for testability.
    """
    if clock is None:
        clock = _utc_now

    ts_dt = clock()
    meta = dict(snapshot)
    meta['timestamp'] = ts_dt.isoformat()

    role = meta['role']
    status = meta.get('status', 'unknown')
    ts = ts_dt.strftime("%Y%m%d_%H%M%S")
    fname = f"{role}_{ts}_{status}.zip"

    node = archive_dir.parent
    zip_path = archive_dir / fname
    if trace is not None:
        trace.record_info('node_archive._save_archive_zip._save_archive_zip', f'archive_dir exists={Path.exists(archive_dir)} path={archive_dir}')
        trace.record_info('node_archive._save_archive_zip._save_archive_zip', f'zip_path={zip_path}')
        trace.record_info('node_archive._save_archive_zip._save_archive_zip', f'meta={meta}')
    Path.mkdir(archive_dir)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("meta.json", json.dumps(meta, ensure_ascii=False, indent=2))
        if trace is not None:
            trace.record_info('node_archive._save_archive_zip._save_archive_zip', 'meta.json written to zip')
        for sub in _SNAPSHOT_DIRS:
            src = node / sub
            if trace is not None:
                trace.record_info('node_archive._save_archive_zip._save_archive_zip', f'scanning dir={src} exists={Path.exists(src)}')
            if not Path.exists(src):
                continue
            for p in Path.rglob(src, "*"):
                if Path.is_file(p):
                    arcname = f"{sub}/{p.relative_to(src)}"
                    zf.write(p, arcname=arcname)
                    if trace is not None:
                        trace.record_info('node_archive._save_archive_zip._save_archive_zip', f'archive add {arcname}')
    if trace is not None:
        trace.record_info('node_archive._save_archive_zip._save_archive_zip', f'zip written size={zip_path.stat().st_size}B')

