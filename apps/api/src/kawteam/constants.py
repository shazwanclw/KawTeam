"""
Shared constants for the KawTeam backend.

Centralises magic numbers and repeated string literals so they can be
updated in one place and referenced by name in business logic and tests.
"""

# ---------------------------------------------------------------------------
# Session & authentication
# ---------------------------------------------------------------------------

SESSION_LIFETIME_SECONDS: int = 86_400  # 24 hours
MIN_SECRET_LENGTH: int = 32

# ---------------------------------------------------------------------------
# Budget & currency helpers
# ---------------------------------------------------------------------------

SEN_PER_RINGGIT: int = 100  # RM 1 = 100 sen; all monetary fields stored in sen


def sen_to_ringgit(sen: int) -> float:
    """Convert a sen amount to ringgit (RM)."""
    return sen / SEN_PER_RINGGIT


def ringgit_to_sen(rm: float) -> int:
    """Convert a ringgit amount to sen, rounding to the nearest sen."""
    return round(rm * SEN_PER_RINGGIT)


def format_rm(sen: int) -> str:
    """Return a human-readable ringgit string, e.g. 'RM 25.00'."""
    return f"RM {sen_to_ringgit(sen):,.2f}"


# ---------------------------------------------------------------------------
# Thread & conversation limits
# ---------------------------------------------------------------------------

MAX_THREAD_MESSAGES: int = 150  # Upper bound before a thread is considered full

# ---------------------------------------------------------------------------
# Supplier liaison
# ---------------------------------------------------------------------------

LIAISON_STATUSES = frozenset({
    "pending",
    "contacted",
    "replied",
    "ready",
    "declined",
    "unresponsive",
})

# ---------------------------------------------------------------------------
# Automation
# ---------------------------------------------------------------------------

AUTOMATION_STATES = frozenset({
    "idle",
    "running",
    "paused",
    "needs_attention",
    "complete",
})

# ---------------------------------------------------------------------------
# Demo & fixtures
# ---------------------------------------------------------------------------

DEMO_PROJECT_NAMES = (
    "Sunway Got Talent T-Shirts",
    "Career Fair Exhibitor Placements",
    "Weekly Team Catering",
)
