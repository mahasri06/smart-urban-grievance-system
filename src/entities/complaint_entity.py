from sqlalchemy import Column, DateTime, Integer, String, Float, func
from database.database import Base


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)

    source = Column(String, default="citizen")

    title = Column(String)
    description = Column(String)
    cleaned_text = Column(String, nullable=True)

    location = Column(String, nullable=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)

    category = Column(String, nullable=True)
    urgency = Column(String, nullable=True)
    sentiment = Column(String, nullable=True)

    status = Column(String, default="PENDING")

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )