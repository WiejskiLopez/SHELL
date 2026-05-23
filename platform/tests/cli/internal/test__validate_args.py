import pytest
from shell.component.cli.cli.internal._assert_node_dir_set import _assert_node_dir_set
from shell.component.cli.cli.internal._assert_task_name_set import _assert_task_name_set
from shell.component.cli.cli.internal._assert_mode_allowed import _assert_mode_allowed


def test_assert_node_dir_set_raises_in_agent_mode_when_missing():
    with pytest.raises(ValueError, match="--node-dir"):
        _assert_node_dir_set(None, 'agent')


def test_assert_node_dir_set_does_not_raise_when_present():
    _assert_node_dir_set("/some/path", 'agent')


def test_assert_node_dir_set_does_not_raise_when_mode_none():
    _assert_node_dir_set(None, None)


def test_assert_task_name_set_raises_in_tasker_mode_when_missing():
    with pytest.raises(ValueError, match="--task-name"):
        _assert_task_name_set(None, 'tasker')


def test_assert_task_name_set_does_not_raise_when_present():
    _assert_task_name_set("my-task", 'tasker')


def test_assert_mode_allowed_raises_for_unknown_mode():
    with pytest.raises(ValueError, match="mode is required"):
        _assert_mode_allowed('unknown')


def test_assert_mode_allowed_does_not_raise_for_agent():
    _assert_mode_allowed('agent')


def test_assert_mode_allowed_does_not_raise_for_tasker():
    _assert_mode_allowed('tasker')
