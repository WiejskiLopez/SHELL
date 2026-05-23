from shell.utils.path.path import Path, PathType
import sys
import logging

import pytest

from shell.app.app import App

# Make the shared `lib` package (outside this package) importable in tests.
_LIB_ROOT = Path.new(__file__).resolve().parents[2]  # 07-automation/
if str(_LIB_ROOT) not in sys.path:
    sys.path.insert(0, str(_LIB_ROOT))


@pytest.fixture
def fake_logger():
    """Logger writing nowhere — prevents any log file creation during tests."""
    logger = logging.getLogger("worker2-test")
    logger.handlers.clear()
    logger.addHandler(logging.NullHandler())
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    return logger


@pytest.fixture
def cfg(fake_logger):
    """Minimal app with pre-injected logger to avoid filesystem side effects."""
    cfg = App(logger=fake_logger)
    return cfg


@pytest.fixture
def node_dir(tmp_path):
    """Minimal valid node directory structure."""
    (tmp_path / '.node' / 'app').mkdir(parents=True)
    (tmp_path / '.node' / 'app' / 'app.yaml').write_text('# app\n', encoding='utf-8')
    (tmp_path / 'input').mkdir()
    (tmp_path / 'output').mkdir()
    (tmp_path / 'archive').mkdir()
    return tmp_path


@pytest.fixture
def cfg_with_node(cfg, node_dir):
    """App with pre-injected logger and a real valid node directory."""
    cfg.app_node_.node_._node_dir = str(node_dir)
    return cfg
