"""
Audio Fingerprinting Module for Antigravity Music Manager.
Uses the Chromaprint 'fpcalc' CLI utility to generate acoustic fingerprints
from audio waveforms, enabling accurate duplicate detection regardless of
file format, bitrates, filenames, or tag metadata.
"""

import json
import os
import shutil
import subprocess
from typing import Optional, Dict, Any

from utils import get_logger

logger = get_logger()


def is_fpcalc_available() -> bool:
    """
    Check if the 'fpcalc' (Chromaprint) executable is available on the system PATH.
    """
    return shutil.which("fpcalc") is not None


def generate_audio_fingerprint(
    filepath: str, length: int = 120, timeout: int = 20
) -> Optional[Dict[str, Any]]:
    """
    Generate an acoustic fingerprint for an audio file using fpcalc.

    Args:
        filepath: Absolute or relative path to the audio file.
        length: Maximum length (in seconds) of the audio to analyze (default 120s).
        timeout: Maximum execution timeout in seconds.

    Returns:
        Dict with 'duration' (float) and 'fingerprint' (str), or None on failure.
    """
    if not is_fpcalc_available():
        logger.warning("[AudioFingerprint] 'fpcalc' executable not found on system PATH.")
        return None

    if not os.path.isfile(filepath):
        logger.debug(f"[AudioFingerprint] File not found: {filepath}")
        return None

    try:
        logger.debug(f"[AudioFingerprint] Generating fingerprint for {filepath} with length={length}s and timeout={timeout}s")
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
                logger.debug(f"[AudioFingerprint] Incomplete output from fpcalc for {filepath}")
        else:
            logger.debug(
                f"[AudioFingerprint] fpcalc returned non-zero code {res.returncode} for {filepath}: {res.stderr.strip()}"
            )
    except subprocess.TimeoutExpired:
        logger.warning(f"[AudioFingerprint] fpcalc timed out after {timeout}s for {filepath}")
    except Exception as err:
        logger.error(f"[AudioFingerprint] Error generating fingerprint for {filepath}: {err}")

    return None


def are_fingerprints_equal(fp1: Optional[str], fp2: Optional[str]) -> bool:
    """
    Check if two Chromaprint fingerprints are identical.
    """
    if not fp1 or not fp2:
        return False
    return fp1.strip() == fp2.strip()

if __name__ == "__main__":
    logger.info(f"fpcalc available: {is_fpcalc_available()}")