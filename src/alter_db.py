from database.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    conn.execute(text('ALTER TABLE complaints ADD COLUMN IF NOT EXISTS cleaned_description VARCHAR;'))
    conn.execute(text('ALTER TABLE complaints ADD COLUMN IF NOT EXISTS category VARCHAR;'))
    conn.execute(text('ALTER TABLE complaints ADD COLUMN IF NOT EXISTS urgency VARCHAR;'))
    conn.execute(text('ALTER TABLE complaints ADD COLUMN IF NOT EXISTS sentiment VARCHAR;'))
    conn.commit()
print("Columns added successfully")
