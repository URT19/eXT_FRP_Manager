"""Route validation helpers for HAProxy aggregation."""
from __future__ import annotations

from ..models import Route, Channel


def validate_route(route: Route, channels: dict[str, Channel]) -> list[str]:
    """Return list of errors (empty = valid).

    A balanced route must have at least 2 channels to be meaningful.
    A simple route must have exactly 1 channel.
    """
    errs: list[str] = []
    if not (1 <= route.entry_port <= 65535):
        errs.append(f"Invalid entry port: {route.entry_port}")
    if not route.channels:
        errs.append(f"Route {route.id} has no channels")
        return errs

    missing = [c for c in route.channels if c not in channels]
    if missing:
        errs.append(f"Route {route.id} references missing channels: {missing}")

    if route.mode == "simple" and len(route.channels) != 1:
        errs.append(
            f"Simple route {route.id} must have exactly 1 channel "
            f"(has {len(route.channels)})"
        )
    if route.mode == "balanced" and len(route.channels) < 2:
        errs.append(
            f"Balanced route {route.id} needs at least 2 channels "
            f"(has {len(route.channels)})"
        )
    return errs


def channels_for_route(route: Route,
                       channels: dict[str, Channel]) -> list[Channel]:
    return [channels[c] for c in route.channels if c in channels]
