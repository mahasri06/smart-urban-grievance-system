from sqlalchemy import Column, Integer, String

from database.database import Base


class Complaint(Base):

    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String)

    description = Column(String)

    cleaned_description = Column(String, nullable=True)

    location = Column(String)

    status = Column(String, default="PENDING")

    category = Column(String, nullable=True)

    urgency = Column(String, nullable=True)

    sentiment = Column(String, nullable=True)