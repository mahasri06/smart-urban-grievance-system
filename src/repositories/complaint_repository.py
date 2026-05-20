from sqlalchemy import func
from sqlalchemy.orm import Session

from entities.complaint_entity import Complaint


class ComplaintRepository:

    @staticmethod
    def create_complaint(
        db: Session,
        complaint: Complaint
    ):

        db.add(complaint)

        db.commit()

        db.refresh(complaint)

        return complaint

    @staticmethod
    def create_complaints_bulk(
        db: Session,
        complaints: list[Complaint]
    ):
        """
        Efficiently inserts a list of complaints into the database.
        """
        db.add_all(complaints)
        db.commit()
        # Note: We typically don't refresh all objects after a bulk insert 
        # unless absolutely necessary to save database roundtrips.
        return complaints

    @staticmethod
    def get_complaint_by_id(
        db: Session,
        complaint_id: int
    ):

        return (
            db.query(Complaint)
            .filter(Complaint.id == complaint_id)
            .first()
        )
    
    
    @staticmethod
    def get_complaints(db, page, size, sort , location=None, title=None):

        query = db.query(Complaint)

        if sort == "latest":
            query = query.order_by(Complaint.id.desc())

        elif sort == "oldest":
            query = query.order_by(Complaint.id.asc())

        if location:
            query = query.filter(
                Complaint.location.ilike(f"%{location}%")
            )

        if title:
            query = query.filter(
                Complaint.title.ilike(f"%{title}%")
            )

        offset = (page - 1) * size

        return query.limit(size).offset(offset).all()
    
    @staticmethod
    def complaints_by_location(db):

        results = (
            db.query(
                Complaint.location,
                func.count(Complaint.id)
            )
            .group_by(Complaint.location)
            .all()
        )

        return [
            {
                "location": row[0],
                "count": row[1]
            }
            for row in results
        ]
    
    @staticmethod
    def top_locations(db, limit=5):

        results = (
            db.query(
                Complaint.location,
                func.count(Complaint.id).label("total")
            )
            .group_by(Complaint.location)
            .order_by(func.count(Complaint.id).desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "location": row[0],
                "total": row[1]
            }
            for row in results
        ]