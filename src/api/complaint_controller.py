from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from database.dependencies import get_db

from services.complaint_service import ComplaintService

from dto.complaint_dto import ComplaintCreate

router = APIRouter()


@router.post("/complaints")
def create_complaint(
    complaint: ComplaintCreate,
    db: Session = Depends(get_db)
):

    saved_complaint = ComplaintService.create_complaint(
        db,
        complaint
    )
    
    return saved_complaint


@router.get("/complaints/{complaint_id}")
def get_complaint_by_id(
    complaint_id: int,
    db: Session = Depends(get_db)
):

    complaint = ComplaintService.get_complaint_by_id(db, complaint_id)

    if complaint is None:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found"
        )

    return complaint

@router.get("/complaints")
def get_complaints(
    page: int = 1,
    size: int = 10,
    sort: str = "latest",
    location: str = None,
    title: str = None,
    db: Session = Depends(get_db)
):

    return ComplaintService.get_complaints(
        db,
        page,
        size,
        location,
        title
    )

@router.get("/analytics/complaints/by-location")
def complaints_by_location(db: Session = Depends(get_db)):

    return ComplaintService.get_complaints_by_location(db)

@router.get("/analytics/complaints/top-locations")
def top_locations(
    limit: int = 3,
    db: Session = Depends(get_db)
):

    return ComplaintService.get_top_locations(db, limit)
