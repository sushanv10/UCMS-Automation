"""Small reusable helper functions."""
import re
from datetime import datetime
import time
import uuid


def safe_filename(text: str) -> str:
    """Turn a pytest node name such as 'test_x[Network Explorer]' into a safe file name."""
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("_")


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def unique(prefix: str) -> str:
    """Avoid name collisions across re-runs."""
    return f"{prefix}_{uuid.uuid4().hex[:6]}"

def _unique_with_length(length: int, filler: str = "Q") -> str:
    """Unique name of EXACTLY `length` characters (suffix replaces filler)."""
    suffix = unique("")
    body_len = length - len(suffix)
    if body_len < 1:
        return suffix[:length]
    return (filler * body_len) + suffix


def _unique_numeric(base: str = "20260") -> str:
    """Unique numeric-only name: base digits + 6 time-derived digits."""
    return f"{base}{int(time.time_ns()) % 1_000_000:06d}"