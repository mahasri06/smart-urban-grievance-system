# Smart Urban Grievance Redressal System - Documentation

## 1. Project Overview
The **Smart Urban Grievance Redressal and Infrastructure Monitoring System** is an advanced platform that collects citizen complaints and actively mines social media and news sources to detect and analyse urban issues proactively.

## 2. System Architecture
The system consists of a multi-tier architecture:
- **Data Ingestion**: A REST API for explicit citizen complaints, plus web scrapers (Reddit, News) for implicit issue detection.
- **NLP & Classification**: Complaints are cleaned and passed through a Logistic Regression classifier (trained on TF-IDF features) to determine the *Category* (e.g., Roads & Traffic, Flooding) and *Urgency* (HIGH, MEDIUM, LOW).
- **Location Processing**: Uses an LLM Parser to extract specific locations and coordinates from unstructured text (Recent Feature).
- **Data Mining**: Includes Association Rule Mining (Apriori) to detect co-occurring issues and Sequential Pattern Mining (PrefixSpan) for escalation chains.
- **Frontend Dashboard**: A comprehensive Streamlit dashboard providing visual insights, heatmaps, and pattern alerts.

## 3. Newly Added Features
Recent updates have introduced several major capabilities:

### A. LLM-Based Location Parser (`src/location/llm_parser.py`)
- Previously, location extraction was simple keyword matching.
- The new module leverages an LLM to accurately parse unstructured complaint descriptions and social media posts, extracting exact street names, localities, and geographic coordinates.

### B. News Collector integration (`src/scraper/collectors/news.py`)
- The scraper module was heavily refactored.
- A new News Collector was added to scrape local news sites for mentions of civic issues, complementing the existing Reddit scraper.
- The scraper configuration is now dynamically stemmed (`src/scraper/config_stemmed.json`) to improve keyword matching during filtering.

### C. Entity Alignment & Database Migrations
- Aligned the database entities (`complaint_entity.py` and `scraped_post_entity.py`) to properly store the newly extracted locality coordinates.
- Updated the FastAPI backend (`main.py`) to process these new fields synchronously and asynchronously.

## 4. How to Run the Project

**1. Start the API Server:**
```bash
cd src
uvicorn main:app --reload
```
API runs at `http://localhost:8000`

**2. Start the Streamlit Dashboard:**
```bash
cd src
streamlit run dashboard/app.py
```
Dashboard runs at `http://localhost:8501`

**3. Run the Data Scraper:**
```bash
cd src
python scraper/main.py
```

## 5. Technology Stack
- **Backend:** FastAPI, Uvicorn, Python 3.10+
- **Frontend:** Streamlit, Plotly
- **Database:** PostgreSQL, SQLAlchemy ORM
- **Machine Learning & NLP:** scikit-learn (Logistic Regression, TF-IDF), NLTK, mlxtend (Apriori)
- **Scraping:** PRAW (Reddit API), BeautifulSoup4 (News)
