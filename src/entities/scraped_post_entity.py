from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from database.database import Base


class ScrapedPost(Base):
    __tablename__ = "scraped_posts"

    id = Column(Integer, primary_key=True, index=True)

    source = Column(String)

    title = Column(String)
    description = Column(String, nullable=True)
    cleaned_text = Column(String, nullable=True)

    location = Column(String, nullable=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)

    category = Column(String, nullable=True)
    urgency = Column(String, nullable=True)
    sentiment = Column(String, nullable=True)

    status = Column(String, default="UNVERIFIED")

    # subreddit = Column(String, nullable=True)

    url = Column(String, nullable=True)
    source_id = Column(String, nullable=True)

    # upvotes = Column(Integer, default=0)
    # num_comments = Column(Integer, default=0)

    credibility_score = Column(Float, nullable=True)

    scraped_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )