from sqlalchemy.orm import Session
from entities.complaint_entity import Complaint
from dto.complaint_dto import ComplaintCreate
from repositories.complaint_repository import ComplaintRepository
from nlp.nlp_service import process_text

class ComplaintService:
    @staticmethod
    def create_complaint(db: Session, complaint_in: ComplaintCreate):
        # 1. Process NLP synchronously
        cleaned_text = process_text(complaint_in.description)
        
        # 2. Create the complaint entity
        new_complaint = Complaint(
            title=complaint_in.title,
            description=complaint_in.description,
            cleaned_description=cleaned_text,
            location=complaint_in.location,
            status="PROCESSED"
        )
        # 3. Save it to database synchronously
        saved_complaint = ComplaintRepository.create_complaint(db, new_complaint)
        return saved_complaint

    @staticmethod
    def create_complaints_bulk(db: Session, complaints_in: list[ComplaintCreate]):
        new_complaints = []
        for complaint_in in complaints_in:
            # 1. Process NLP synchronously for each
            cleaned_text = process_text(complaint_in.description)
            
            # 2. Create the complaint entity
            new_complaint = Complaint(
                title=complaint_in.title,
                description=complaint_in.description,
                cleaned_description=cleaned_text,
                location=complaint_in.location,
                status="PROCESSED"
            )
            new_complaints.append(new_complaint)
            
        # 3. Save all to database synchronously in bulk
        saved_complaints = ComplaintRepository.create_complaints_bulk(db, new_complaints)
        return saved_complaints

    @staticmethod
    def get_complaint_by_id(db: Session, complaint_id: int):
        return ComplaintRepository.get_complaint_by_id(db, complaint_id)

    @staticmethod
    def get_complaints(db: Session, page: int, size: int, location: str = None, title: str = None):
        # Passing default sort 'latest' as controller defaults to it
        return ComplaintRepository.get_complaints(db, page, size, "latest", location, title)

    @staticmethod
    def get_complaints_by_location(db: Session):
        return ComplaintRepository.complaints_by_location(db)

    @staticmethod
    def get_top_locations(db: Session, limit: int):
        return ComplaintRepository.top_locations(db, limit)