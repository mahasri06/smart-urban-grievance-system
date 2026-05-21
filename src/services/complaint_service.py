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
    def create_complaints_bulk(db: Session, complaints_in: list[ComplaintCreate], background_tasks):
        new_complaints = []
        for complaint_in in complaints_in:
            # 2. Create the complaint entity without cleaning the text yet
            new_complaint = Complaint(
                title=complaint_in.title,
                description=complaint_in.description,
                location=complaint_in.location,
                status="PENDING_ANALYSIS"
            )
            new_complaints.append(new_complaint)
            
        # 3. Save all to database synchronously in bulk (Very fast)
        saved_complaints = ComplaintRepository.create_complaints_bulk(db, new_complaints)
        
        # 4. Schedule the heavy NLP processing in the background
        complaint_ids = [c.id for c in saved_complaints]
        background_tasks.add_task(ComplaintService.process_nlp_background, complaint_ids)
        
        return saved_complaints

    @staticmethod
    def process_nlp_background(complaint_ids: list[int]):
        """
        This runs completely in the background after the API responds.
        """
        from database.database import SessionLocal
        from nlp.classifier import classify_text
        db = SessionLocal()
        
        try:
            # Fetch the un-processed complaints
            complaints = ComplaintRepository.get_complaints_by_ids(db, complaint_ids)
            
            # Process each one
            for complaint in complaints:
                # 1. Clean the text
                complaint.cleaned_description = process_text(complaint.description)
                
                # 2. Run Classification Intelligence
                category, urgency, sentiment = classify_text(complaint.cleaned_description)
                
                # 3. Update the Database Entity
                complaint.category = category
                complaint.urgency = urgency
                complaint.sentiment = sentiment
                complaint.status = "PROCESSED"
                
            # Commit the changes to the database
            db.commit()
            print(f"Background NLP & Classification Task Finished for {len(complaint_ids)} complaints.")
            
        finally:
            db.close()

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