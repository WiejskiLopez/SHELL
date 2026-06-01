from __future__ import annotations


def _init_agent(agent) -> None:
    agent.agent_properties_.init_agent_properties()
    agent.agent_prompt_.init_agent_prompt()
