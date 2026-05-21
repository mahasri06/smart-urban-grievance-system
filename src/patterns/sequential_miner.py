"""
Sequential Pattern Mining
=========================
Discovers temporal sequences of complaint categories per location.

Example insight:
  "In Koramangala, Flooding complaints are consistently followed by
   Water & Sanitation complaints, then Electricity complaints."

This reveals predictable cascading failure chains so authorities
can act pre-emptively after the first complaint type appears.

Algorithm: PrefixSpan (implemented from scratch — no extra dependency).
PrefixSpan is efficient for sparse sequences and works well on the
small-to-medium datasets typical of a city-level grievance system.

Usage:
    from patterns.sequential_miner import run_sequential_mining
    patterns = run_sequential_mining(db)
"""

from collections import defaultdict
from sqlalchemy.orm import Session

from entities.complaint_entity import Complaint
from entities.scraped_post_entity import ScrapedPost


# ---------------------------------------------------------------------------
# Data preparation
# ---------------------------------------------------------------------------

def _build_sequences(db: Session) -> list[list[str]]:
    """
    Builds ordered sequences of complaint categories per location,
    sorted by complaint ID (proxy for time since we don't have timestamps
    on all records).

    Returns a list of sequences, one per location:
        [
            ["Flooding", "Water & Sanitation", "Electricity"],  # Koramangala
            ["Roads & Traffic", "Garbage & Waste"],              # Whitefield
            ...
        ]
    """
    rows = (
        db.query(Complaint.location, Complaint.category, Complaint.id)
        .filter(
            Complaint.category != None,
            Complaint.location != None,
            Complaint.status == "PROCESSED",
        )
        .order_by(Complaint.id.asc())
        .all()
    )

    scraped_rows = (
        db.query(ScrapedPost.location, ScrapedPost.category, ScrapedPost.id)
        .filter(
            ScrapedPost.category != None,
            ScrapedPost.location != None,
        )
        .order_by(ScrapedPost.id.asc())
        .all()
    )

    # Group by location, preserving order
    location_map: dict[str, list[str]] = defaultdict(list)

    for location, category, _ in rows:
        location_map[location.strip().title()].append(category)

    for location, category, _ in scraped_rows:
        location_map[location.strip().title()].append(category)

    # Only keep sequences with at least 2 events (otherwise no pattern possible)
    sequences = [seq for seq in location_map.values() if len(seq) >= 2]
    return sequences


# ---------------------------------------------------------------------------
# PrefixSpan implementation
# ---------------------------------------------------------------------------

def _prefix_span(sequences: list[list[str]], min_support: int) -> list[tuple[list[str], int]]:
    """
    PrefixSpan algorithm for sequential pattern mining.

    Args:
        sequences:   List of event sequences (each sequence is a list of strings)
        min_support: Minimum number of sequences a pattern must appear in

    Returns:
        List of (pattern, support_count) tuples, sorted by support descending
    """
    results: list[tuple[list[str], int]] = []

    def _project(seqs: list[list[str]], prefix_item: str) -> list[list[str]]:
        """
        Projects the sequence database with respect to a prefix item.
        Returns the suffix of each sequence after the first occurrence of prefix_item.
        """
        projected = []
        for seq in seqs:
            for i, item in enumerate(seq):
                if item == prefix_item:
                    suffix = seq[i + 1:]
                    if suffix:
                        projected.append(suffix)
                    break
        return projected

    def _mine(prefix: list[str], seqs: list[list[str]]):
        # Count support for each unique next item
        item_counts: dict[str, int] = defaultdict(int)
        for seq in seqs:
            seen_in_seq = set()
            for item in seq:
                if item not in seen_in_seq:
                    item_counts[item] += 1
                    seen_in_seq.add(item)

        for item, count in item_counts.items():
            if count >= min_support:
                new_prefix = prefix + [item]
                results.append((new_prefix, count))
                # Recurse with projected database
                projected = _project(seqs, item)
                if projected:
                    _mine(new_prefix, projected)

    _mine([], sequences)

    # Sort by support descending, then by pattern length descending
    results.sort(key=lambda x: (x[1], len(x[0])), reverse=True)
    return results


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_sequential_mining(
    db: Session,
    min_support: int = 2,
    min_length: int = 2,
    max_results: int = 20,
) -> list[dict]:
    """
    Runs sequential pattern mining on complaint data.

    Args:
        db:          SQLAlchemy session
        min_support: Minimum number of locations where the sequence must appear
        min_length:  Minimum pattern length (default 2 = at least A → B)
        max_results: Cap on number of patterns returned

    Returns:
        List of dicts:
            [
                {
                    "pattern": ["Flooding", "Water & Sanitation"],
                    "support": 4,
                    "description": "Flooding → Water & Sanitation (seen in 4 locations)"
                },
                ...
            ]
    """
    sequences = _build_sequences(db)

    if len(sequences) < 2:
        print(f"[SequentialMiner] Not enough data ({len(sequences)} sequences). "
              "Need complaints from at least 2 locations.")
        return []

    raw_patterns = _prefix_span(sequences, min_support=min_support)

    # Filter by minimum length
    filtered = [
        (pattern, support)
        for pattern, support in raw_patterns
        if len(pattern) >= min_length
    ]

    # Format output
    output = []
    for pattern, support in filtered[:max_results]:
        arrow_str = " → ".join(pattern)
        output.append({
            "pattern": pattern,
            "support": support,
            "description": f"{arrow_str} (seen in {support} location(s))",
        })

    print(f"[SequentialMiner] Found {len(output)} patterns from {len(sequences)} sequences.")
    return output


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from database.database import SessionLocal

    db = SessionLocal()
    try:
        patterns = run_sequential_mining(db, min_support=1)
        if not patterns:
            print("No patterns found.")
        else:
            for p in patterns:
                print(p["description"])
    finally:
        db.close()
