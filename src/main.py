from fastapi import FastAPI

from database.database import engine
from database.database import Base

from api.complaint_controller import router

from entities.complaint_entity import Complaint


app = FastAPI()


Base.metadata.create_all(bind=engine)


app.include_router(router)