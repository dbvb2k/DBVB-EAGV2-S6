"""
Cognitive Layers for Law Case Finder AI System

This package contains the four cognitive layers that power the AI system:
1. Perception Layer - LLM interactions and model management
2. Memory Layer - User preferences and context storage
3. Decision Layer - Orchestration and agent sequencing
4. Action Layer - Task execution (extraction, generation, normalization)
"""

from .perception_layer import PerceptionLayer
from .memory_layer import MemoryLayer
from .decision_layer import DecisionLayer
from .action_layer import ActionLayer

__all__ = ['PerceptionLayer', 'MemoryLayer', 'DecisionLayer', 'ActionLayer']

