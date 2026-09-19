import re
def normalize_string(s: str) -> str:
    """Normalize string for fast comparison (lowercase, alphanumeric only)."""
    return re.sub(r"[^a-zA-Z0-9]", "", s.lower())


