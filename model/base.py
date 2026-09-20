from dataclasses import dataclass, asdict
from typing import Any, Dict


@dataclass
class DictLikeRecord:
    """
    Base dataclass mixin offering dictionary-like key access and serialization.
    Ensures models and dictionaries can be used interchangeably across all layers.
    """

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(key)

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
