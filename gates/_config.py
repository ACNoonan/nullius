"""Opt-in discovery: which trees do these gates apply to?

A research-discipline gate is not a global lint. Installed at the user level it
would otherwise fire on every repo on the machine, and a gate that fires where
it was not invited is a gate that gets uninstalled — the one outcome these are
least able to survive.

So the rule is OPT-IN, per repository:

    a tree is governed iff it contains `.nullius.toml` at its root

No config file, no gating. That makes installation safe by default, keeps the
consent visible in the repo rather than in someone's dotfiles, and means the
same checkout behaves identically for a collaborator who cloned it.

Nothing here parses TOML — presence is the whole signal today. The file is a
declaration of intent with room to grow options later.
"""
from __future__ import annotations

import os

MARKER = ".nullius.toml"


def governing_root(path: str) -> str | None:
    """Nearest ancestor of `path` holding the marker, or None."""
    try:
        d = os.path.dirname(os.path.abspath(path))
    except Exception:
        return None
    while d and d != os.path.dirname(d):
        if os.path.isfile(os.path.join(d, MARKER)):
            return d
        d = os.path.dirname(d)
    return None


def in_scope(path: str) -> bool:
    return governing_root(path) is not None


def roots_for(path: str) -> tuple[str, ...]:
    """Drop-in replacement for the old hardcoded ROOTS tuple."""
    r = governing_root(path)
    return (r,) if r else ()
