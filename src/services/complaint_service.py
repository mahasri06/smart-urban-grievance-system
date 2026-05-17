from sqlalchemy.orm import Session

from repositories.complaint_repository import ComplaintRepository

from entities.complaint_entity import Complaint

from dto.complaint_dto import ComplaintCreate


class ComplaintService:

    @staticmethod
    def create_complaint(
        db: Session,
        complaint_data: ComplaintCreate
    ):

        complaint = Complaint(

            title=complaint_data.title,

            description=complaint_data.description,

            location=complaint_data.location
        )

        return ComplaintRepository.create_complaint(
            db,
            complaint
        )
    
    @staticmethod
    def get_complaints(db, page, size, location=None, title=None):

        return ComplaintRepository.get_complaints(
            db,
            page,
            size,
            location,
            title
        )

    @staticmethod
    def get_complaint_by_id(
        db: Session,
        complaint_id: int
    ):

        return ComplaintRepository.get_complaint_by_id(
            db,
            complaint_id
        )