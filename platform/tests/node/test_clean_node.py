"""Tests for Node.clean_node()

Verifies: unlink called for files, rmtree called for subdirectories,
missing directories are skipped, OSError on individual items is ignored.
"""

import pytest
from shell.app.app import App

_CLEAN_DIRS = ("tmp", "script")


def _make_node_with_content(tmp_path):
    """Create a node with files and subdirs in all cleanable dirs."""
    for dir_name in _CLEAN_DIRS:
        d = tmp_path / dir_name
        d.mkdir(exist_ok=True)
        (d / "file.txt").write_text("content")
        (d / "subdir").mkdir()
    return tmp_path


def test_unlink_called_for_files_in_cleanable_dirs(cfg_with_node, node_dir):
    _make_node_with_content(node_dir)
    unlinked = []
    rmtrees = []
    cfg_with_node.app_node_.node_.clean_node(rmtree=rmtrees.append, unlink=unlinked.append)
    # Each cleanable dir has one file
    assert len(unlinked) >= len(_CLEAN_DIRS)


def test_rmtree_called_for_subdirectories_in_cleanable_dirs(cfg_with_node, node_dir):
    _make_node_with_content(node_dir)
    rmtrees = []
    cfg_with_node.app_node_.node_.clean_node(rmtree=rmtrees.append, unlink=lambda p: None)
    # Each cleanable dir has one subdir
    assert len(rmtrees) >= len(_CLEAN_DIRS)


def test_missing_cleanable_directory_is_skipped(cfg_with_node, node_dir):
    # Remove 'temp' if it exists; it's optional
    import shutil
    for d in ["temp"]:
        target = node_dir / d
        if target.exists():
            shutil.rmtree(target)
    # Must not raise
    cfg_with_node.app_node_.node_.clean_node(rmtree=lambda p: None, unlink=lambda p: None)


def test_oserror_on_item_is_silently_ignored(cfg_with_node, node_dir):
    (node_dir / "tmp").mkdir(exist_ok=True)
    (node_dir / "tmp" / "bad.txt").write_text("x")

    def raising_unlink(p):
        raise OSError("permission denied")

    # Must not propagate the OSError
    cfg_with_node.app_node_.node_.clean_node(rmtree=lambda p: None, unlink=raising_unlink)


def test_clean_node_uses_real_filesystem_by_default(node_dir):
    """Integration: verify real files are removed without DI."""
    import logging
    logger = logging.getLogger("test")
    logger.addHandler(logging.NullHandler())
    app = App(logger=logger)
    app.app_node_.node_._node_dir = str(node_dir)
    target = node_dir / "output" / "result.txt"
    target.write_text("output data")
    app.app_node_.node_.clean_node()
    assert not target.exists()
