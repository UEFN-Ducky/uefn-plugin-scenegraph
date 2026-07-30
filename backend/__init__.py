"""Scene Graph — Store desktop plugin (gates core tool modules)."""

from __future__ import annotations


def register(api) -> None:
    """Import gated MCP tools onto the shared FastMCP instance."""
    import backend.tools.scene_graph  # noqa: F401
    api.log("scenegraph tools registered")
