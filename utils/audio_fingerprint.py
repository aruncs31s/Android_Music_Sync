"""
Audio Fingerlogger.infoing Module for Antigravity Music Manager.
Uses the Chromaprint 'fpcalc' CLI utility to generate acoustic fingerprints
from audio waveforms, enabling accurate duplicate detection regardless of
file format, bitrates, filenames, or tag metadata.
"""

import base64
import json
import os
import shutil
import subprocess
from collections import defaultdict
from typing import Any, Dict, List, Optional

from utils import get_logger

logger = get_logger()

# Analyze the whole track by default. Chromaprint's own default is 120s, but a
# 2-minute window is fragile: two copies of the same song that differ only in
# their intro/silence offset/mastering within that window produce different
# hashes. Set to an int number of seconds to limit analysis (0 = full track).
DEFAULT_FINGERPRINT_LENGTH = 0

# Similarity in [0, 1] above which two Chromaprint fingerprints are considered
# the same recording. Identical files score 1.0, a re-encode/remaster of the
# same track scores ~0.99, unrelated tracks score near 0.0.
SIMILARITY_THRESHOLD = 0.90

# Duration guard: two copies of the same recording should not differ by more
# than this many seconds (or this fraction, whichever is larger).
DURATION_TOLERANCE_SECONDS = 5.0
DURATION_TOLERANCE_RATIO = 0.05

# Candidate prefilter for grouping. Comparing every pair of full-track
# fingerprints is O(n^2) and far too slow for a real library, so we first count
# how many raw fingerprint integers two tracks share (an inverted index) and
# only run the expensive similarity comparison on plausible candidates.
MIN_SHARED_TOKENS = 20
MIN_SHARED_RATIO = 0.10

try:
    import acoustid as _acoustid

    _ACOUSTID_AVAILABLE = True
except Exception as _imp_err:  # pragma: no cover - optional native dependency
    _acoustid = None
    _ACOUSTID_AVAILABLE = False
    logger.warning(
        f"[AudioFingerprint] pyacoustid/libchromaprint unavailable ({_imp_err}); "
        "falling back to exact fingerprint string matching."
    )


def is_fpcalc_available() -> bool:
    """
    Check if the 'fpcalc' (Chromaprint) executable is available on the system PATH.
    """
    return shutil.which("fpcalc") is not None


def is_similarity_available() -> bool:
    """
    Check whether similarity-based fingerprint comparison is available
    (requires the pyacoustid package + libchromaprint).
    """
    return _ACOUSTID_AVAILABLE


def generate_audio_fingerprint(
    filepath: str, length: int = DEFAULT_FINGERPRINT_LENGTH, timeout: int = 20
) -> dict[str, Any] | None:
    """
    Generate an acoustic fingerprint for an audio file using fpcalc.

    Args:
        filepath: Absolute or relative path to the audio file.
        length: Maximum length (in seconds) of the audio to analyze.
            Defaults to DEFAULT_FINGERPRINT_LENGTH (0 = full track).
        timeout: Maximum execution timeout in seconds.

    Returns:
        Dict with 'duration' (float) and 'fingerprint' (str), or None on failure.
    """
    if not is_fpcalc_available():
        logger.warning(
            "[AudioFingerprint] 'fpcalc' executable not found on system PATH."
        )
        return None

    if not os.path.isfile(filepath):
        logger.debug(f"[AudioFingerprint] File not found: {filepath}")
        return None

    try:
        logger.debug(
            f"[AudioFingerprint] Generating fingerprint for {filepath} with length={length}s and timeout={timeout}s"
        )
        cmd = ["fpcalc", "-json", "-length", str(length), filepath]
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
        logger.debug(f"[AudioFingerprint] fpcalc stdout: {res.stdout.strip()}")
        if res.returncode == 0 and res.stdout.strip():
            data = json.loads(res.stdout)
            fingerprint = data.get("fingerprint")
            duration = data.get("duration")

            if fingerprint and duration is not None:
                return {
                    "duration": round(float(duration), 2),
                    "fingerprint": str(fingerprint).strip(),
                }
            else:
                logger.debug(
                    f"[AudioFingerprint] Incomplete output from fpcalc for {filepath}"
                )
        else:
            logger.debug(
                f"[AudioFingerprint] fpcalc returned non-zero code {res.returncode} for {filepath}: {res.stderr.strip()}"
            )
    except subprocess.TimeoutExpired:
        logger.warning(
            f"[AudioFingerprint] fpcalc timed out after {timeout}s for {filepath}"
        )
    except Exception as err:
        logger.error(
            f"[AudioFingerprint] Error generating fingerprint for {filepath}: {err}"
        )

    return None


def are_fingerprints_equal(fp1: str| None, fp2: str | None) -> bool:
    """
    Check if two Chromaprint fingerprints are byte-for-byte identical.

    Note: this is a fast-path only. The same recording re-encoded at a
    different bitrate/codec produces a slightly different Chromaprint string,
    so prefer get_fingerprint_similarity() for duplicate detection.
    """
    if not fp1 or not fp2:
        return False
    return fp1.strip() == fp2.strip()


def _looks_like_chromaprint(fp: str) -> bool:
    """Cheaply validate that a string could be a Chromaprint fingerprint.

    Chromaprint emits URL-safe base64 (using '-' and '_'), so normalise before
    decoding. Binary fingerprints need at least 4 bytes to be decodable.
    """
    try:
        s = fp.strip().replace("-", "+").replace("_", "/")
        s += "=" * (-len(s) % 4)
        return len(base64.b64decode(s, validate=True)) >= 4
    except Exception:
        return False


def get_fingerprint_similarity(fp1: str | None, fp2: str | None) -> float:
    """
    Return an acoustic similarity score in [0, 1] between two Chromaprint
    fingerprints, tolerant of re-encoding, differing bitrates, and minor
    mastering/intro differences.

    Falls back to 1.0 on an exact string match (when pyacoustid is missing)
    and 0.0 otherwise.
    """
    if not fp1 or not fp2:
        return 0.0

    a = fp1.strip()
    b = fp2.strip()
    if a == b:
        return 1.0

    if not _ACOUSTID_AVAILABLE:
        return 0.0

    if not (_looks_like_chromaprint(a) and _looks_like_chromaprint(b)):
        return 0.0

    try:
        # acoustid.compare_fingerprints expects a (duration, fingerprint) pair
        # where the fingerprint is base64 bytes; the duration is unused here.
        return float(
            _acoustid.compare_fingerprints((0.0, a.encode()), (0.0, b.encode()))
        )
    except Exception as err:
        logger.debug(
            f"[AudioFingerprint] similarity comparison failed, treating as no match: {err}"
        )
        return 0.0


def durations_are_compatible(
    dur1: float | None,
    dur2: float | None,
    tolerance_seconds: float = DURATION_TOLERANCE_SECONDS,
    tolerance_ratio: float = DURATION_TOLERANCE_RATIO,
) -> bool:
    """
    Sanity-check that two recordings have comparable lengths.

    Returns True when either duration is unknown or when both are within
    max(tolerance_seconds, tolerance_ratio * longer_duration) of each other.
    """
    if dur1 is None or dur2 is None:
        return True
    try:
        d1 = float(dur1)
        d2 = float(dur2)
    except (TypeError, ValueError):
        return True
    longest = max(d1, d2)
    allowed = max(tolerance_seconds, tolerance_ratio * longest)
    return abs(d1 - d2) <= allowed


def fingerprints_match(
    fp1: str | None,
    fp2: str | None,
    dur1: float | None = None,
    dur2: float | None = None,
    threshold: float = SIMILARITY_THRESHOLD,
) -> bool:
    """
    Decide whether two fingerprints represent the same recording, applying
    acoustic similarity plus an optional duration sanity check.
    """
    if not durations_are_compatible(dur1, dur2):
        return False
    return get_fingerprint_similarity(fp1, fp2) >= threshold


def decode_fingerprint(fp: str | None) -> List[int] | None:
    """
    Decode a compressed Chromaprint fingerprint into its raw 32-bit integers.

    Returns None when decoding is unavailable or the fingerprint is invalid.
    """
    if not fp or not _ACOUSTID_AVAILABLE:
        return None
    try:
        import chromaprint  # bundled with pyacoustid

        decoded, _ = chromaprint.decode_fingerprint(fp.strip().encode())
        return [int(x) for x in decoded]
    except Exception as err:
        logger.debug(f"[AudioFingerprint] Could not decode fingerprint: {err}")
        return None


def _min_shared_tokens(num_ints: int) -> int:
    """Minimum shared raw integers for two fingerprints to be worth comparing."""
    return max(MIN_SHARED_TOKENS, int(num_ints * MIN_SHARED_RATIO))


def group_fingerprints(
    fingerprints: List[str | None],
    durations: List[float | None] | None = None,
    threshold: float = SIMILARITY_THRESHOLD,
) -> List[List[int]]:
    """
    Group fingerprints that represent the same recording.

    Uses an inverted index over raw fingerprint integers to shortlist
    candidates, then confirms each candidate with the similarity comparison
    (and duration guard). This keeps the cost near-linear for large libraries.

    Args:
        fingerprints: List of fingerprint strings (None entries are ignored).
        durations: Optional parallel list of track durations (seconds).
        threshold: Similarity threshold in [0, 1].

    Returns:
        A list of groups, each a list of indices into ``fingerprints``.
    """
    if durations is None:
        durations = [None] * len(fingerprints)

    groups: List[Dict[str, Any]] = []
    value_index: Dict[int, set] = defaultdict(set)
    exact_index: Dict[str, int] = {}

    for idx, fp in enumerate(fingerprints):
        if not fp:
            continue
        dur = durations[idx] if idx < len(durations) else None
        key = fp.strip()

        # Fast path: byte-identical fingerprint already seen.
        gid = exact_index.get(key)
        if gid is not None:
            groups[gid]["members"].append(idx)
            continue

        ints = decode_fingerprint(key) or []

        # Score candidate groups by how many raw integers they share with us.
        # Undecodable fingerprints can't be indexed, so fall back to comparing
        # against every existing group (rare, and usually just a few).
        if ints:
            scores: Dict[int, int] = {}
            for value in ints:
                for candidate_gid in value_index.get(value, ()):
                    scores[candidate_gid] = scores.get(candidate_gid, 0) + 1
            candidates = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
            required = _min_shared_tokens(len(ints))
        else:
            candidates = [(gid, 0) for gid in range(len(groups))]
            required = 0

        matched_gid = None
        for candidate_gid, shared in candidates:
            if ints and shared < required:
                break
            group = groups[candidate_gid]
            if fingerprints_match(
                key, group["rep_fp"], dur, group["rep_dur"], threshold
            ):
                matched_gid = candidate_gid
                break

        if matched_gid is None:
            new_gid = len(groups)
            groups.append({"rep_fp": key, "rep_dur": dur, "members": [idx]})
            exact_index[key] = new_gid
            for value in set(ints):
                value_index[value].add(new_gid)
        else:
            groups[matched_gid]["members"].append(idx)

    return [group["members"] for group in groups]


if __name__ == "__main__":
    logger.info(f"fpcalc available: {is_fpcalc_available()}")
