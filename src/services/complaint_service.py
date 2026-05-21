from sqlalchemy.orm import Session
from entities.complaint_entity import Complaint
from dto.complaint_dto import ComplaintCreate
from repositories.complaint_repository import ComplaintRepository
from nlp.nlp_service import process_text
from nlp.classifier import classify_text


class ComplaintService:

    @staticmethod
    def create_complaint(db: Session, complaint_in: ComplaintCreate):
        """Single complaint — processed synchronously and returned immediately."""

        # 1. NLP preprocessing
        cleaned_text = process_text(complaint_in.description)

        # 2. Classification (category, urgency, sentiment)
        category, urgency, sentiment = classify_text(cleaned_text)

        # 3. Build entity
        new_complaint = Complaint(
            title=complaint_in.title,
            description=complaint_in.description,
            cleaned_description=cleaned_text,
            location=complaint_in.location,
            category=category,
            urgency=urgency,
            sentiment=sentiment,
            status="PROCESSED",
        )

        # 4. Persist
        return ComplaintRepository.create_complaint(db, new_complaint)

    @staticmethod
    def create_complaints_bulk(
        db: Session,
        complaints_in: list[ComplaintCreate],
        background_tasks,
    ):
        """
        Bulk ingest — saves all complaints immediately with PENDING_ANALYSIS
        status, then schedules NLP + classification as a background task.
        This keeps the API response fast even for large batches.
        """
        new_complaints = [
            Complaint(
                title=c.title,
                description=c.description,
                location=c.location,
                status="PENDING_ANALYSIS",
            )
            for c in complaints_in
        ]

        saved = ComplaintRepository.create_complaints_bulk(db, new_complaints)

        # IDs are populated after bulk insert + refresh (fixed in repository)
        complaint_ids = [c.id for c in saved]
        background_tasks.add_task(ComplaintService._process_nlp_background, complaint_ids)

        return saved

    @staticmethod
    def _process_nlp_background(complaint_ids: list[int]):
        """
        Background task: runs NLP + classification on a batch of complaints
        that were saved with PENDING_ANALYSIS status.
        Opens its own DB session since FastAPI's request session is closed.
        """
        from database.database import SessionLocal

        db = SessionLocal()
        try:
            complaints = ComplaintRepository.get_complaints_by_ids(db, complaint_ids)

            for complaint in complaints:
                cleaned = process_text(complaint.description)
                category, urgency, sentiment = classify_text(cleaned)

                complaint.cleaned_description = cleaned
                complaint.category = category
                complaint.urgency = urgency
                complaint.sentiment = sentiment
                complaint.status = "PROCESSED"

            db.commit()
            print(
                f"[Background NLP] Processed {len(complaints)} complaints "
                f"(IDs: {complaint_ids})"
            )
        except Exception as e:
            print(f"[Background NLP] Error: {e}")
            db.rollback()
        finally:
            db.close()

    @staticmethod
    def get_complaint_by_id(db: Session, complaint_id: int):
        return ComplaintRepository.get_complaint_by_id(db, complaint_id)

    @staticmethod
    def get_complaints(
        db: Session,
        page: int,
        size: int,
        location: str = None,
        title: str = None,
    ):
        return ComplaintRepository.get_complaints(db, page, size, "latest", location, title)

    @staticmethod
    def get_complaints_by_location(db: Session):
        return ComplaintRepository.complaints_by_location(db)

    @staticmethod
    def get_top_locations(db: Session, limit: int):
        return ComplaintRepository.top_locations(db, limit)
