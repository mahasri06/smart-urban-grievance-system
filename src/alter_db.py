from database.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    conn.execute(text('ALTER TABLE complaints ADD COLUMN IF NOT EXISTS cleaned_description VARCHAR;'))
    conn.commit()
print("Column added")
