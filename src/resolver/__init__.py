"""Entity resolution package for canonicalizing entity names."""

from .entity_resolver import EntityResolver, normalize_entity_name, ResolutionResult

__all__ = ["EntityResolver", "normalize_entity_name", "ResolutionResult"]
