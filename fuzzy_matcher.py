"""
Lazy & Fuzzy matching engine for filtering and scoring song items.
Supports subsequence matching, boundary bonuses, multi-word queries, and metadata weighting.
"""
import re
from typing import List, Dict, Any, Tuple, Optional

WORD_BOUNDARY_CHARS = set(" _-/.()[]|\\:#$&")

def fuzzy_subsequence_match(query: str, target: str) -> Tuple[bool, int, List[int]]:
    """
    Check if query is a subsequence of target (case-insensitive) and compute match score and matched indices.
    Returns: (is_match, score, matched_indices_in_target)
    """
    if not query:
        return True, 0, []
    if not target:
        return False, 0, []

    q_lower = query.lower()
    t_lower = target.lower()

    q_idx = 0
    t_idx = 0
    q_len = len(q_lower)
    t_len = len(t_lower)

    matched_indices = []
    score = 0
    consecutive_count = 0

    while q_idx < q_len and t_idx < t_len:
        if q_lower[q_idx] == t_lower[t_idx]:
            matched_indices.append(t_idx)

            # Base match score
            char_score = 10

            # Boundary bonus: matched at start of target or right after word boundary
            if t_idx == 0 or t_lower[t_idx - 1] in WORD_BOUNDARY_CHARS:
                char_score += 15
            
            # Exact case match bonus
            if query[q_idx] == target[t_idx]:
                char_score += 2

            # Consecutive character match bonus
            if consecutive_count > 0:
                char_score += 10 * consecutive_count
            consecutive_count += 1

            score += char_score
            q_idx += 1
        else:
            consecutive_count = 0
        t_idx += 1

    # Check if all query characters were found in sequence
    if q_idx == q_len:
        # Exact substring bonus
        if q_lower in t_lower:
            score += 50
            if t_lower.startswith(q_lower):
                score += 50

        # Compactness bonus (penalize large span of matched characters)
        if matched_indices:
            span = matched_indices[-1] - matched_indices[0] + 1
            compactness_penalty = max(0, span - q_len) * 2
            score -= compactness_penalty

        return True, max(1, score), matched_indices

    return False, 0, []

def score_song(query: str, song: Dict[str, Any]) -> Tuple[bool, int]:
    """
    Score a song against a search query.
    Query can contain multiple space-separated terms (all terms must match).
    """
    if not query.strip():
        return True, 0

    tokens = query.strip().split()
    total_score = 0

    # Fields to search with priority weights
    search_fields = [
        ("title", 4.0),
        ("artist", 3.0),
        ("album", 2.0),
        ("_display_name", 1.5),
        ("_data", 1.0)
    ]

    for token in tokens:
        token_matched = False
        best_token_score = 0

        for field_name, weight in search_fields:
            val = song.get(field_name) or ""
            if not val:
                continue
            matched, score, _ = fuzzy_subsequence_match(token, val)
            if matched:
                token_matched = True
                weighted_score = int(score * weight)
                if weighted_score > best_token_score:
                    best_token_score = weighted_score

        if not token_matched:
            return False, 0

        total_score += best_token_score

    return True, total_score

def filter_and_rank_songs(query: str, songs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter list of songs by query using lazy matching and return them sorted by relevance score descending.
    """
    if not query or not query.strip():
        return songs

    results = []
    for song in songs:
        matched, score = score_song(query, song)
        if matched:
            results.append((score, song))

    # Sort descending by score
    results.sort(key=lambda x: x[0], reverse=True)
    return [song for score, song in results]
