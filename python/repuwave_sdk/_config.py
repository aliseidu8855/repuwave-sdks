"""Where the Repuwave API is, when the caller does not say."""

from __future__ import annotations

import os

# The planned public host. It is not live yet, so it is only the last resort.
FALLBACK_BASE_URL = "https://repuwave.fasolink.app/v1"


def default_base_url() -> str:
    """
    REPUWAVE_API_URL if set, else the planned public host.

    Every constructor used to default to the public host outright. It does not
    answer yet, so an integration that followed the README failed on its first
    call. The dashboard's agent .env download already carries REPUWAVE_API_URL,
    so reading it means a new agent works with no code change.
    """
    return os.environ.get("REPUWAVE_API_URL") or FALLBACK_BASE_URL
