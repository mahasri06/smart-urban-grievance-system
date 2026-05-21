"""
Association Rule Mining
=======================
Discovers co-occurring complaint categories using the Apriori algorithm.

Example insight:
  "When Flooding complaints appear in a location, Water & Sanitation
   complaints follow 78% of the time." (confidence = 0.78)

This helps municipal authorities anticipate cascading infrastructure
failures — fixing one issue proactively prevents the next.

Usage:
    from patterns.association_miner import run_association_mining
    rules_df = run_association_mining(db)
"""

import pandas as pd
from sqlalchemy.orm import Session

try:
    from mlxtend.frequent_patterns import apriori, association_rules
    from mlxtend.preprocessing import TransactionEncoder
    MLXTEND_AVAILABLE = True
except ImportError:
    MLXTEND_AVAILABLE = False
    print("[AssociationMiner] mlxtend not installed. Run: pip install mlxtend")

from entities.complaint_entity import Complaint
from entities.scraped_post_entity import ScrapedPost


# ---------------------------------------------------------------------------
# Data preparation
# ---------------------------------------------------------------------------

def _build_transactions(db: Session) -> list[list[str]]:
    """
    Groups complaints by location and builds a transaction list where
    each transaction = set of unique categories reported at that location.

    e.g. [
        ["Flooding", "Roads & Traffic", "Water & Sanitation"],  # Koramangala
        ["Electricity", "Garbage & Waste"],                      # Whitefield
        ...
    ]
    """
    # Pull all processed complaints that have a category and location
    rows = (
        db.query(Complaint.location, Complaint.category)
        .filter(
            Complaint.category != None,
            Complaint.location != None,
            Complaint.status == "PROCESSED",
        )
        .all()
    )

    # Also include scraped posts
    scraped_rows = (
        db.query(ScrapedPost.location, ScrapedPost.category)
        .filter(
            ScrapedPost.category != None,
            ScrapedPost.location != None,
        )
        .all()
    )

    all_rows = list(rows) + list(scraped_rows)

    if not all_rows:
        return []

    # Group by location
    location_map: dict[str, set[str]] = {}
    for location, category in all_rows:
        location = location.strip().title()
        if location not in location_map:
            location_map[location] = set()
        location_map[location].add(category)

    # Each location becomes one transaction
    transactions = [list(cats) for cats in location_map.values() if len(cats) >= 1]
    return transactions


# ---------------------------------------------------------------------------
# Mining
# ---------------------------------------------------------------------------

def run_association_mining(
    db: Session,
    min_support: float = 0.05,
    min_confidence: float = 0.4,
    min_lift: float = 1.0,
) -> pd.DataFrame:
    """
    Runs Apriori + association rule extraction on complaint data.

    Args:
        db:             SQLAlchemy session
        min_support:    Minimum fraction of locations where itemset appears
        min_confidence: Minimum P(consequent | antecedent)
        min_lift:       Minimum lift (> 1 means positive correlation)

    Returns:
        DataFrame with columns:
            antecedents, consequents, support, confidence, lift
        Empty DataFrame if not enough data or mlxtend not installed.
    """
    if not MLXTEND_AVAILABLE:
        return pd.DataFrame()

    transactions = _build_transactions(db)

    if len(transactions) < 3:
        print(f"[AssociationMiner] Not enough data ({len(transactions)} locations). "
              "Need at least 3 locations with complaints.")
        return pd.DataFrame()

    # Encode transactions into a binary matrix
    te = TransactionEncoder()
    te_array = te.fit_transform(transactions)
    df_encoded = pd.DataFrame(te_array, columns=te.columns_)

    # Apriori — find frequent itemsets
    frequent_itemsets = apriori(
        df_encoded,
        min_support=min_support,
        use_colnames=True,
    )

    if frequent_itemsets.empty:
        print("[AssociationMiner] No frequent itemsets found. Try lowering min_support.")
        return pd.DataFrame()

    # Generate association rules
    rules = association_rules(
        frequent_itemsets,
        metric="confidence",
        min_threshold=min_confidence,
    )

    # Filter by lift
    rules = rules[rules["lift"] >= min_lift]

    # Clean up for display
    rules["antecedents"] = rules["antecedents"].apply(lambda x: ", ".join(sorted(x)))
    rules["consequents"] = rules["consequents"].apply(lambda x: ", ".join(sorted(x)))

    result = (
        rules[["antecedents", "consequents", "support", "confidence", "lift"]]
        .sort_values("lift", ascending=False)
        .reset_index(drop=True)
    )

    print(f"[AssociationMiner] Found {len(result)} rules from {len(transactions)} location transactions.")
    return result


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from database.database import SessionLocal

    db = SessionLocal()
    try:
        rules_df = run_association_mining(db, min_support=0.05, min_confidence=0.3)
        if rules_df.empty:
            print("No rules generated.")
        else:
            print(rules_df.to_string(index=False))
    finally:
        db.close()
