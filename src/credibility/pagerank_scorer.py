"""
PageRank-Based Credibility Scorer
==================================
Scores scraped Reddit posts by credibility using a graph-based approach
inspired by Google's PageRank algorithm.

How it works:
  1. Build a graph where each node is a scraped post.
  2. Draw an edge between two posts if they share the same category
     AND location (they're talking about the same issue in the same area).
  3. Weight each edge by the engagement similarity between the two posts
     (posts with similar upvote/comment counts reinforce each other).
  4. Run networkx.pagerank() on this graph.
  5. Normalise scores to [0, 1] and store them in the DB.

Posts with high credibility scores are ones that:
    - Are corroborated by many other posts about the same issue
    - Are connected to other high-credibility posts
    - Can optionally use engagement if available (defaults to 0 when absent)

Usage:
    from credibility.pagerank_scorer import run_pagerank_scoring
    run_pagerank_scoring(db)
"""

import math
import networkx as nx
from sqlalchemy.orm import Session

from entities.scraped_post_entity import ScrapedPost
from repositories.scraped_post_repository import ScrapedPostRepository


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def _build_graph(posts: list[ScrapedPost]) -> nx.Graph:
    """
    Builds an undirected weighted graph from scraped posts.

    Node attributes:
        - engagement: log(upvotes + comments + 1)  — base node weight

    Edge condition:
        Two posts are connected if they share the same category AND location.

    Edge weight:
        Similarity of engagement scores (closer = stronger edge).
        weight = 1 / (1 + |engagement_i - engagement_j|)
    """
    G = nx.Graph()

    # Add nodes (use baseline engagement score of 1.0 since specific metrics were removed)
    for post in posts:
        engagement = 1.0
        G.add_node(post.id, engagement=engagement, post=post)

    # Add edges between posts sharing category + location
    for i in range(len(posts)):
        for j in range(i + 1, len(posts)):
            p1, p2 = posts[i], posts[j]

            # Both must have category and location to be comparable
            if not (p1.category and p2.category and p1.location and p2.location):
                continue

            same_category = p1.category == p2.category
            same_location = p1.location.strip().lower() == p2.location.strip().lower()

            if same_category and same_location:
                e1 = G.nodes[p1.id]["engagement"]
                e2 = G.nodes[p2.id]["engagement"]
                weight = 1.0 / (1.0 + abs(e1 - e2))
                G.add_edge(p1.id, p2.id, weight=weight)

    return G


def _personalisation_vector(posts: list[ScrapedPost], G: nx.Graph) -> dict[int, float]:
    """
    Personalisation vector biases PageRank toward high-engagement posts.
    Each node's personalisation weight = its normalised engagement score.
    This means popular posts start with more "rank juice".
    """
    engagements = {
        post.id: G.nodes[post.id]["engagement"]
        for post in posts
        if post.id in G.nodes
    }
    total = sum(engagements.values()) or 1.0
    return {node_id: eng / total for node_id, eng in engagements.items()}


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------

def _normalise(scores: dict[int, float]) -> dict[int, float]:
    """Min-max normalise PageRank scores to [0, 1]."""
    if not scores:
        return scores
    min_score = min(scores.values())
    max_score = max(scores.values())
    spread = max_score - min_score

    if spread == 0:
        # All scores identical — assign 0.5 to everyone
        return {k: 0.5 for k in scores}

    return {k: (v - min_score) / spread for k, v in scores.items()}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_pagerank_scoring(db: Session, alpha: float = 0.85) -> dict[int, float]:
    """
    Full pipeline:
      1. Load all scraped posts from DB
      2. Build similarity graph
      3. Run PageRank
      4. Normalise scores
      5. Persist scores back to DB

    Args:
        db:    SQLAlchemy session
        alpha: PageRank damping factor (0.85 is the standard)

    Returns:
        Dict mapping post_id → normalised credibility score (0.0 – 1.0)
    """
    posts = ScrapedPostRepository.get_all(db)

    if not posts:
        print("[PageRank] No scraped posts found.")
        return {}

    print(f"[PageRank] Scoring {len(posts)} posts...")

    G = _build_graph(posts)

    if G.number_of_nodes() == 0:
        print("[PageRank] Graph is empty.")
        return {}

    # Personalisation biases toward high-engagement posts
    personalisation = _personalisation_vector(posts, G)

    # Run PageRank
    # For isolated nodes (no edges), PageRank falls back to personalisation weight
    raw_scores = nx.pagerank(
        G,
        alpha=alpha,
        personalization=personalisation,
        weight="weight",
        max_iter=200,
        tol=1e-6,
    )

    # Normalise to [0, 1]
    normalised_scores = _normalise(raw_scores)

    # Persist to DB
    ScrapedPostRepository.update_scores(db, normalised_scores)

    print(
        f"[PageRank] Scoring complete. "
        f"Score range: {min(normalised_scores.values()):.3f} – "
        f"{max(normalised_scores.values()):.3f}"
    )

    return normalised_scores


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from database.database import SessionLocal

    db = SessionLocal()
    try:
        scores = run_pagerank_scoring(db)
        if scores:
            sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            print("\nTop 10 most credible posts:")
            for post_id, score in sorted_scores[:10]:
                print(f"  Post ID {post_id}: {score:.4f}")
    finally:
        db.close()
