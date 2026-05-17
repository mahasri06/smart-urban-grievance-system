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
    def get_complaints(db, page, size, location=None, title=None):

        query = db.query(Complaint)

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