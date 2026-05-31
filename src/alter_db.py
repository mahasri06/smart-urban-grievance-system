from database.database import engine
from sqlalchemy import text

# "My tables already exist. Add any missing columns without deleting existing data."

with engine.connect() as conn:
    conn.execute(text('ALTER TABLE complaints ADD COLUMN IF NOT EXISTS source VARCHAR;'))
    conn.execute(text('ALTER TABLE complaints ADD COLUMN IF NOT EXISTS cleaned_text VARCHAR;'))
    conn.execute(text('ALTER TABLE complaints ADD COLUMN IF NOT EXISTS category VARCHAR;'))
    conn.execute(text('ALTER TABLE complaints ADD COLUMN IF NOT EXISTS urgency VARCHAR;'))
    conn.execute(text('ALTER TABLE complaints ADD COLUMN IF NOT EXISTS sentiment VARCHAR;'))
    conn.execute(text('ALTER TABLE complaints ADD COLUMN IF NOT EXISTS lat DOUBLE PRECISION;'))
    conn.execute(text('ALTER TABLE complaints ADD COLUMN IF NOT EXISTS lng DOUBLE PRECISION;'))
    conn.execute(text('ALTER TABLE complaints ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();'))

    conn.execute(text('ALTER TABLE scraped_posts ADD COLUMN IF NOT EXISTS description VARCHAR;'))
    conn.execute(text('ALTER TABLE scraped_posts ADD COLUMN IF NOT EXISTS cleaned_text VARCHAR;'))
    conn.execute(text('ALTER TABLE scraped_posts ADD COLUMN IF NOT EXISTS location VARCHAR;'))
    conn.execute(text('ALTER TABLE scraped_posts ADD COLUMN IF NOT EXISTS lat DOUBLE PRECISION;'))
    conn.execute(text('ALTER TABLE scraped_posts ADD COLUMN IF NOT EXISTS lng DOUBLE PRECISION;'))
    conn.execute(text('ALTER TABLE scraped_posts ADD COLUMN IF NOT EXISTS category VARCHAR;'))
    conn.execute(text('ALTER TABLE scraped_posts ADD COLUMN IF NOT EXISTS urgency VARCHAR;'))
    conn.execute(text('ALTER TABLE scraped_posts ADD COLUMN IF NOT EXISTS sentiment VARCHAR;'))
    conn.execute(text('ALTER TABLE scraped_posts ADD COLUMN IF NOT EXISTS status VARCHAR;'))
    conn.execute(text('ALTER TABLE scraped_posts ADD COLUMN IF NOT EXISTS url VARCHAR;'))
    conn.execute(text('ALTER TABLE scraped_posts ADD COLUMN IF NOT EXISTS source_id VARCHAR;'))
    conn.execute(text('ALTER TABLE scraped_posts ADD COLUMN IF NOT EXISTS credibility_score DOUBLE PRECISION;'))
    conn.execute(text('ALTER TABLE scraped_posts ADD COLUMN IF NOT EXISTS scraped_at TIMESTAMPTZ DEFAULT NOW();'))
    conn.commit()
print("Columns added successfully")
