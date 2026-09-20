import re
from typing import Optional


def normalize_string(s: str) -> str:
    """Normalize string for fast comparison (lowercase, alphanumeric only)."""
    if not s:
        return ""
    return re.sub(r"[^a-zA-Z0-9]", "", s.lower())


def clean_string_for_matching(text: Optional[str]) -> str:
    """
    Single source of truth to normalize song titles or filenames for fuzzy matching:
    - Lowercases text
    - Strips common audio quality/release tags in brackets/parentheses (e.g. (128), [FLAC], (Official Video))
    - Strips audio file extensions (.mp3, .flac, .m4a, etc.)
    - Normalizes punctuation and consecutive whitespace
    """
    if not text:
        return ""
    s = text.lower()
    # Remove common audio tags in parentheses or brackets e.g. (128), (320), (Official Video), [FLAC]
    s = re.sub(
        r"\s*[\(\[][^\)\]]*(?:128|192|256|320|flac|kbps|audio|video|lyrics|official|remaster|hd|hq)[^\)\]]*[\)\]]",
        "",
        s,
        flags=re.IGNORECASE
    )
    # Strip audio extension if present
    s = re.sub(r"\.(?:mp3|flac|m4a|wav|ogg|opus|aac)$", "", s, flags=re.IGNORECASE)
    # Normalize punctuation and separators to single spaces
    s = re.sub(r"[\-_\.\(\)\[\]\'\"~]+", " ", s)
    return " ".join(s.split()).strip()


def sanitize_filename(filename: str, replacement: str = "_") -> str:
    """Sanitize string to be safe for filenames across Linux, Android, and macOS."""
    if not filename:
        return "unnamed"
    # Replace illegal filesystem characters: / \ : * ? " < > |
    cleaned = re.sub(r'[\\/*?:"<>|]', replacement, filename)
    # Strip leading/trailing dots and spaces
    cleaned = cleaned.strip(". ")
    return cleaned or "unnamed"


