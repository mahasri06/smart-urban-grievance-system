from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func

from database.database import Base


class ScrapedPost(Base):
    """
    Stores posts collected from Reddit (and future sources).
    Each post goes through the same NLP + classification pipeline
    as citizen-submitted complaints, plus a credibility score
    computed by the PageRank scorer.
    """

    __tablename__ = "scraped_posts"

    id = Column(Integer, primary_key=True, index=True)

    # Source metadata
    source = Column(String, default="reddit")          # "reddit", "news", etc.
    source_id = Column(String, unique=True, index=True) # Reddit post ID — prevents duplicates
    subreddit = Column(String, nullable=True)

    # Content
    title = Column(String)
    body = Column(String, nullable=True)               # post selftext
    url = Column(String, nullable=True)

    # Extracted / inferred location
    location = Column(String, nullable=True)

    # Engagement signals (used by PageRank scorer)
    upvotes = Column(Integer, default=0)
    num_comments = Column(Integer, default=0)
    author = Column(String, nullable=True)

    # NLP outputs
    cleaned_text = Column(String, nullable=True)
    category = Column(String, nullable=True)
    urgency = Column(String, nullable=True)
    sentiment = Column(String, nullable=True)

    # Credibility score from PageRank (0.0 – 1.0)
    credibility_score = Column(Float, nullable=True)

    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
