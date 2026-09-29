"""Small reusable helper functions."""
import re
from datetime import datetime


def safe_filename(text: str) -> str:
    """Turn a pytest node name such as 'test_x[Network Explorer]' into a safe file name."""
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("_")


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")
