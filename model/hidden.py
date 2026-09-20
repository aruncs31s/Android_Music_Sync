from dataclasses import dataclass
from typing import Optional
from model.base import DictLikeRecord


@dataclass
class HiddenFileRecord(DictLikeRecord):
    """Model representing a hidden file in the library."""
    filepath: str
    filename: str = ""
    id: Optional[int] = None
    hidden_at: Optional[str] = None
