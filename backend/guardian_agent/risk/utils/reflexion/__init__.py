"""
Reflexion (Verbal RL) system for Guardian Agent.

Provides text-based memory and lesson generation for learning from past trade decisions.
Architecture is designed to extend to Scout and Onboarder agents later.
"""

from .memory import ReflexionMemory
from .reflector import Reflector

__all__ = ['ReflexionMemory', 'Reflector']
