from sqlalchemy.orm import Session
from sqlalchemy import func

from entities.scraped_post_entity import ScrapedPost


class ScrapedPostRepository:

    @staticmethod
    def upsert_bulk(db: Session, posts: list[ScrapedPost]) -> list[ScrapedPost]:
        """
        Insert posts that don't already exist (keyed on source_id).
        Skips duplicates so the scraper can be re-run safely.
        Returns only the newly inserted posts.
        """
        existing_ids = {
            row[0]
            for row in db.query(ScrapedPost.source_id).all()
        }

        new_posts = [p for p in posts if p.source_id not in existing_ids]

        if new_posts:
            db.add_all(new_posts)
            db.commit()
            for post in new_posts:
                db.refresh(post)

        return new_posts

    @staticmethod
    def get_all(db: Session) -> list[ScrapedPost]:
        return db.query(ScrapedPost).order_by(ScrapedPost.scraped_at.desc()).all()

    @staticmethod
    def get_by_id(db: Session, post_id: int) -> ScrapedPost | None:
        return db.query(ScrapedPost).filter(ScrapedPost.id == post_id).first()

    @staticmethod
    def get_unscored(db: Session) -> list[ScrapedPost]:
        """Returns posts that haven't been assigned a credibility score yet."""
        return (
            db.query(ScrapedPost)
            .filter(ScrapedPost.credibility_score == None)
            .all()
        )

    @staticmethod
    def get_high_credibility(db: Session, threshold: float = 0.6) -> list[ScrapedPost]:
        return (
            db.query(ScrapedPost)
            .filter(ScrapedPost.credibility_score >= threshold)
            .order_by(ScrapedPost.credibility_score.desc())
            .all()
        )

    @staticmethod
    def update_scores(db: Session, scores: dict[int, float]) -> None:
        """
        Bulk-update credibility scores.
        scores: { post_id: score_float }
        """
        for post_id, score in scores.items():
            db.query(ScrapedPost).filter(ScrapedPost.id == post_id).update(
                {"credibility_score": score}
            )
        db.commit()

    @staticmethod
    def count_by_category(db: Session) -> list[dict]:
        results = (
            db.query(ScrapedPost.category, func.count(ScrapedPost.id))
            .group_by(ScrapedPost.category)
            .all()
        )
        return [{"category": row[0], "count": row[1]} for row in results]

    @staticmethod
    def count_by_location(db: Session) -> list[dict]:
        results = (
            db.query(ScrapedPost.location, func.count(ScrapedPost.id))
            .filter(ScrapedPost.location != None)
            .group_by(ScrapedPost.location)
            .all()
        )
        return [{"location": row[0], "count": row[1]} for row in results]
