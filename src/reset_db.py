from database.database import engine, Base
from entities.complaint_entity import Complaint
from entities.scraped_post_entity import ScrapedPost

print("Dropping all tables...")
Base.metadata.drop_all(bind=engine)

print("Recreating all tables for bulk social media data...")
Base.metadata.create_all(bind=engine)

print("Database cleared and initialized successfully!")
