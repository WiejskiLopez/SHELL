"""Mapper functions - each in its own module."""

from __future__ import annotations

from .node_link_definition_entity_to_model import node_link_definition_entity_to_model
from .node_link_definition_model_to_entity import node_link_definition_model_to_entity

__all__ = ["node_link_definition_entity_to_model", "node_link_definition_model_to_entity"]
