"""_init_agent.py
Initialise Agent sub-objects from _app.
"""

from __future__ import annotations


def _init_agent(agent) -> None:
    """Initialise Agent — each sub-object reads from _app directly."""
    agent._agent_properties.init_agent_properties()
    agent._agent_command.init_agent_command()
    agent._agent_prompt.init_agent_prompt()
