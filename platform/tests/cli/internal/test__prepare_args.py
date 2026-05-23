from shell.utils.path.path import PathType
from shell.app.app import App
from shell.component.cli.cli.internal._init_cli import _init_cli


def test_node_flag_is_written_to_config(tmp_path):
    node_dir = tmp_path / "my_node"
    node_dir.mkdir()
    app = App()
    _init_cli(app.app_config_.cli_, argv=["--node-dir", str(node_dir)])
    assert app.app_config_.cli_.cli_properties_._node_dir == str(node_dir)


def test_source_dir_is_set_from_flag(tmp_path):
    app = App()
    _init_cli(app.app_config_.cli_, argv=["--source-dir", str(tmp_path)])
    assert app.app_config_.cli_.cli_properties_._source_dir == str(tmp_path)

