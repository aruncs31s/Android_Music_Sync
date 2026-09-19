import sys
import importlib.util
from .args import parse_args

__all__ = ["parse_args"]

# Forward standard library cmd attributes (e.g. Cmd) so stdlib modules like pdb work
for _p in sys.path:
    if _p and "Android_Music_Sync" not in _p:
        _stdlib_cmd = f"{_p}/cmd.py"
        try:
            _spec = importlib.util.spec_from_file_location("_stdlib_cmd", _stdlib_cmd)
            if _spec and _spec.loader:
                _mod = importlib.util.module_from_spec(_spec)
                _spec.loader.exec_module(_mod)
                for _k, _v in _mod.__dict__.items():
                    if not _k.startswith("__") and _k not in globals():
                        globals()[_k] = _v
                break
        except Exception:
            pass