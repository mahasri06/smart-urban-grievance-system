from database.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    conn.execute(text('DROP TABLE IF EXISTS complaints;'))
    conn.commit()
print("Table dropped")
